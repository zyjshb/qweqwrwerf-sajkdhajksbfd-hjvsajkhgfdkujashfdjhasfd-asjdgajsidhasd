"""
WebSocket game session handler.

Each connected client gets its own GameState, AI worker, and Agent instance.
Communication follows the protocol defined in protocol.py.
"""
from __future__ import annotations
import asyncio
import json
import queue
import re
import threading
import time
import traceback
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from websocket.protocol import (
    envelope_client, envelope_server, ClientMessage,
    CLIENT_TYPES, SERVER_TYPES,
)
from core.game_state import GameState, normalize_delta_payload, align_delta_with_player_intent
from core.config import load_config, save_config
from ai.api_client import fetch_api_response, _generate_mock_reply
from ai.prompt_builder import get_system_prompt
from ai.translator import parse_api_response
from audio.tts_client import TTSClient
from resources.game_constants import (
    normalize_language, detect_language, translation_required,
    LANGUAGE_PROFILES, build_offline_translation_line,
)


class GameSession:
    """Per-connection session holding all game state and worker threads."""

    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.state = GameState()
        self.config: dict = {}
        self.chat_history: list[dict] = []
        self.ui_queue: queue.Queue = queue.Queue()
        self.tts_client = TTSClient()

        # Screen agent (lazy init)
        self.agent: Optional[object] = None
        self.agent_active: bool = False

        # Connection health
        self.alive: bool = True
        self.last_ping: float = time.time()

        # Slot paths — resolve to backend directory regardless of CWD
        self._slot_dir = "."

    # ── lifecycle ─────────────────────────────────────────────────

    async def run(self):
        """Main receive loop. Blocks until the websocket closes."""
        # Load config and send initial state
        self.config = load_config()
        await self._push_state_sync()
        await self._push_slot_list()
        await self._safe_send(envelope_server("CONFIG_SYNC", config=self.config))


        while self.alive:
            try:
                raw = await asyncio.wait_for(self.ws.receive_text(), timeout=30.0)
                self.last_ping = time.time()
                msg = envelope_client(raw)
                await self._dispatch(msg)
            except asyncio.TimeoutError:
                await self._safe_send(envelope_server("PONG"))
            except WebSocketDisconnect:
                self.alive = False
                break
            except Exception:
                traceback.print_exc()  # log server-side only
                await self._safe_send(envelope_server("ERROR", message="Internal server error"))

    # ── dispatcher ────────────────────────────────────────────────

    async def _dispatch(self, msg: ClientMessage):
        t = msg.type
        if t == "CHAT_SEND":
            await self._handle_chat(msg.payload)
        elif t == "CONFIG_UPDATE":
            await self._handle_config_update(msg.payload)
        elif t == "SAVE_SLOT":
            await self._handle_save(msg.payload)
        elif t == "LOAD_SLOT":
            await self._handle_load(msg.payload)
        elif t == "DELETE_SLOT":
            await self._handle_delete_slot(msg.payload)
        elif t == "SWITCH_CHARACTER":
            await self._handle_switch_character(msg.payload)
        elif t == "LANGUAGE_CHANGE":
            await self._handle_language_change(msg.payload)
        elif t == "RESTART_GAME":
            await self._handle_restart()
        elif t == "PING":
            await self._safe_send(envelope_server("PONG"))
        elif t == "SCREEN_CAPTURE_START":
            await self._handle_screen_capture_start(msg.payload)
        elif t == "SCREEN_CAPTURE_STOP":
            await self._handle_screen_capture_stop()
        elif t == "LAUNCH_GAME":
            await self._handle_launch_game(msg.payload)
        elif t == "API_TEST":
            await self._handle_api_test(msg.payload)
        elif t == "CUSTOM_CHAR_SAVE":
            await self._handle_custom_char_save(msg.payload)
        elif t == "CUSTOM_CHAR_LOAD":
            await self._handle_custom_char_load()
        elif t == "CUSTOM_CHAR_DELETE":
            await self._handle_custom_char_delete(msg.payload)
        elif t == "CUSTOM_CHAR_LIST":
            await self._handle_custom_char_list()
        elif t == "REQUEST_FILE_PICKER":
            await self._handle_file_picker(msg.payload)
        else:
            await self._safe_send(envelope_server("ERROR", message=f"Unhandled type: {t}"))

    # ── chat handler (the big one) ────────────────────────────────

    async def _handle_chat(self, payload: dict):
        user_input = (payload.get("text") or "").strip()
        if not user_input or self.state.game_over:
            return

        self.state.last_user_input = user_input
        self.state.cycle_id += 1
        cycle = self.state.cycle_id

        # Choose UI language if player hasn't
        user_lang = detect_language(user_input, self.state.cached_lang)

        # Build system prompt
        sys_prompt = get_system_prompt(self.state)

        # Build chat history for API
        if not self.chat_history:
            self.chat_history = [{"role": "system", "content": sys_prompt}]
        else:
            self.chat_history[0]["content"] = sys_prompt
        self.chat_history.append({"role": "user", "content": user_input})

        # Check for offline mode
        api_key = self.config.get("api_key", "")
        base_url = self.config.get("api_base", "")
        model_name = self.config.get("model_name", "deepseek-v4-flash")

        if not api_key:
            # Offline: generate mock reply synchronously
            reply = _generate_mock_reply(user_input, self.state.cached_lang)
            await self._process_reply(reply, user_input, cycle)
        else:
            # Online: run API call in thread, poll for result
            loop = asyncio.get_running_loop()
            api_done = threading.Event()
            api_result = {}

            def _runner():
                fetch_api_response(
                    chat_history=list(self.chat_history),
                    api_key=api_key,
                    base_url=base_url,
                    model_name=model_name,
                    cycle_id=cycle,
                    game_state=self.state,
                    ui_queue=self.ui_queue,
                )
                api_done.set()

            thread = threading.Thread(target=_runner, daemon=True)
            thread.start()

            # Wait for thread to finish (circuit breaker: 60s)
            deadline = time.time() + 60.0
            while not api_done.is_set() and time.time() < deadline:
                await asyncio.sleep(0.1)

            # Drain ALL queue items for this cycle (single pass)
            while not self.ui_queue.empty():
                try:
                    q_cycle, q_type, q_data = self.ui_queue.get_nowait()
                    if q_cycle == cycle:
                        if q_type in ("API_SUCCESS", "API_MOCK") and "reply" not in api_result:
                            api_result["reply"] = q_data
                        elif q_type == "API_FALLBACK" and "reply" not in api_result:
                            api_result["fallback"] = q_data
                except queue.Empty:
                    break

            # Only process once — check cycle_id to prevent stale responses
            if self.state.cycle_id != cycle:
                return
            if "reply" in api_result:
                await self._process_reply(api_result["reply"], user_input, cycle)
            elif "fallback" in api_result:
                user_inp, err = api_result["fallback"]
                fallback_reply = _generate_mock_reply(user_inp, self.state.cached_lang)
                await self._process_reply(fallback_reply, user_input, cycle)
            else:
                fallback_reply = _generate_mock_reply(user_input, self.state.cached_lang)
                await self._process_reply(fallback_reply, user_input, cycle)

    async def _process_reply(self, reply: str, user_input: str, cycle: int):
        """Parse the LLM reply, apply deltas, stream to frontend."""
        if self.state.cycle_id != cycle:
            return
        # Prevent double processing for the same cycle
        if hasattr(self, '_last_processed_cycle') and self._last_processed_cycle == cycle:
            print(f"[Reply] Skipping duplicate for cycle {cycle}")
            return
        self._last_processed_cycle = cycle

        parsed = parse_api_response(reply, user_input, self.state)

        # Stream think block
        think = parsed.get("think", "")
        if think:
            await self._safe_send(envelope_server("THINK_CHUNK", text=think))

        # Get spoken text — use parsed version (monologue stripped)
        spoken = parsed.get("spoken", "")
        clean_spoken = spoken
        user_lang = detect_language(user_input, self.state.cached_lang)

        # Force translation via API — never rely on LLM's inline translation
        translation = ""

        if spoken:
            await self._safe_send(envelope_server("SPEECH_CHUNK", text=clean_spoken))

            # Fallback: fetch translation via API if LLM didn't provide one
            if not translation and self.config.get("api_key"):
                saki_lang = self.state.cached_lang
                if user_lang and user_lang != saki_lang:
                    import requests as req
                    try:
                        api_key = self.config["api_key"]
                        api_base = self.config.get("api_base", "https://api.deepseek.com")
                        model_name = self.config.get("model_name", "deepseek-v4-flash")
                        url = f"{api_base.rstrip('/')}/chat/completions"
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": f"Translate to {user_lang}. Output ONLY translation in （ ）."},
                                {"role": "user", "content": clean_spoken[:300]}
                            ],
                            "temperature": 0.3, "max_tokens": 150,
                        }
                        resp = req.post(url, headers=headers, json=payload, timeout=10, proxies={"http": None, "https": None})
                        if resp.status_code == 200:
                            raw = resp.json()["choices"][0]["message"]["content"].strip()
                            raw = re.sub(r'^[（\(]\s*(日语|中文|English|Japanese|Chinese|日本語)\s*[）\)]', '', raw).strip()
                            c = raw.strip('（） ()')
                            if len(c) >= 2:
                                translation = raw if (raw.startswith("（") and raw.endswith("）")) else f"（{c}）"
                    except Exception as e:
                        print(f"[Translation Error] {e}")

            if translation:
                await self._safe_send(envelope_server("TRANSLATION_CHUNK", text=translation))

        # Process delta
        delta = parsed.get("delta")
        if delta:
            delta = normalize_delta_payload(delta)
            if delta:
                delta = align_delta_with_player_intent(delta, user_input)
                self.state.apply_delta(delta)
                await self._safe_send(envelope_server("DELTA_UPDATE",
                    favorability=delta.get("favorability", 0),
                    suspicion=delta.get("suspicion", 0),
                    escape_rate=delta.get("escape_rate", 0),
                ))

        # Push updated stats
        await self._safe_send(envelope_server("STAT_UPDATE",
            favorability=self.state.favorability,
            suspicion=self.state.suspicion,
            escape_rate=self.state.escape_rate,
        ))

        # Check for day advance
        day_changed, new_day = self.state.advance_day(user_input)
        if day_changed:
            await self._safe_send(envelope_server("DAY_ADVANCE", day=new_day))

        # Check game over
        if self.state.game_over and self.state.pending_ending:
            # Hydrate default localized titles and stories if not present
            ending_type = self.state.pending_ending.get("ending_type", "bad")
            if not self.state.pending_ending.get("ending_title") or not self.state.pending_ending.get("ending_story"):
                from resources.localization import LOCALIZATION
                lang = self.state.cached_lang or "中文"
                if lang not in LOCALIZATION:
                    lang = "中文"
                
                default_ending = LOCALIZATION[lang]["endings"].get(ending_type, LOCALIZATION[lang]["endings"]["bad"])
                
                if not self.state.pending_ending.get("ending_title"):
                    self.state.pending_ending["ending_title"] = default_ending["title"]
                if not self.state.pending_ending.get("ending_story"):
                    self.state.pending_ending["ending_story"] = default_ending["story"]

            await self._safe_send(envelope_server("GAME_OVER",
                ending=self.state.pending_ending,
            ))

        # Add to chat history
        self.chat_history.append({"role": "assistant", "content": reply})
        await self._safe_send(envelope_server("CHAT_APPEND",
            role="assistant",
            content=clean_spoken or spoken or reply,
            think=think,
            translation=translation,
        ))

        # Trigger TTS after a dynamic delay based on think text length
        # Think typewriter runs at ~30ms/char, add 2s buffer
        tts_text = clean_spoken or spoken
        if tts_text:
            think_delay = max(3, len(think) * 0.03 + 2) if think else 3
            async def _delayed_tts_reply():
                await asyncio.sleep(think_delay)
                await self._trigger_tts(tts_text, cycle)
            asyncio.create_task(_delayed_tts_reply())

        # Trigger glitch effects based on suspicion
        await self._schedule_glitch()

    # ── TTS ───────────────────────────────────────────────────────

    async def _fetch_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """Fetch translation synchronously. Returns translation string or empty."""
        import requests as req
        loop = asyncio.get_running_loop()

        def _do():
            try:
                api_key = self.config.get("api_key", "")
                api_base = self.config.get("api_base", "https://api.deepseek.com")
                model_name = self.config.get("model_name", "deepseek-v4-flash")
                if not api_key:
                    print("[Translation] No API key")
                    return ""
                url = f"{api_base.rstrip('/')}/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": (
                            f"You are a translator. Translate the following {source_lang} text into natural {target_lang}. "
                            f"Wrap your translation in full-width parentheses （ ）. "
                            f"Output ONLY the translated text, nothing else."
                        )},
                        {"role": "user", "content": text[:500]}  # Limit text length
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                }
                print(f"[Translation] Calling API: {source_lang} -> {target_lang}, text_len={len(text)}")
                resp = req.post(url, headers=headers, json=payload, timeout=15,
                                proxies={"http": None, "https": None})
                print(f"[Translation] API response: status={resp.status_code}")
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"].strip()
                    print(f"[Translation] Raw response: {raw[:100]}")
                    result = raw
                    # Strip language labels like (日语), (中文), (English)
                    result = re.sub(r'^[（\(]\s*(日语|中文|English|Japanese|Chinese|日本語)\s*[）\)]', '', result).strip()
                    # Extract actual translation content
                    content = result.strip('（） ()')
                    if len(content) < 2:
                        print(f"[Translation] Empty response, skipping")
                        return ""
                    if not (result.startswith("（") and result.endswith("）")):
                        result = f"（{content}）"
                    print(f"[Translation] OK: {result[:60]}...")
                    return result
            except Exception as e:
                print(f"[Translation Error] {e}")
            return ""

        return await loop.run_in_executor(None, _do)

    async def _trigger_tts(self, text: str, cycle: int):
        """Run TTS synthesis in thread, stream result path back."""
        loop = asyncio.get_running_loop()

        def _synth():
            try:
                cleaned = self.tts_client.clean_text_for_tts(text)
                lang = detect_language(cleaned, self.state.cached_lang)
                print(f"[TTS] Input text length: {len(text)}, cleaned length: {len(cleaned)}, lang: {lang}")
                print(f"[TTS] Cleaned text: {cleaned[:200]}...")
                result_path = self.tts_client.synthesize(
                    text=cleaned,
                    language=lang,
                    config=self.config,
                )
                return result_path
            except Exception as e:
                print(f"[TTS Error] {e}")
                return None

        result = await loop.run_in_executor(None, _synth)
        if result and self.state.cycle_id == cycle:
            # Send audio as base64 data URL via WebSocket
            import base64
            try:
                with open(result, "rb") as f:
                    audio_bytes = f.read()
                b64 = base64.b64encode(audio_bytes).decode("ascii")
                data_url = f"data:audio/wav;base64,{b64}"
                await self._safe_send(envelope_server("TTS_AUDIO_URL", url=data_url))
            except Exception as e:
                print(f"[TTS Send Error] {e}")

    # ── glitch scheduling ─────────────────────────────────────────

    async def _schedule_glitch(self):
        """Determine which glitch effects to trigger based on suspicion."""
        s = self.state.suspicion
        e = self.state.escape_rate

        # Build a list of effect triggers
        effects = []

        # Mild (s >= 35)
        if s >= 35:
            effects.append("scanlines")
            effects.append("vignette_squeeze")
            effects.append("dungeon_grid")
        # Moderate (s >= 55)
        if s >= 55:
            effects.append("static_noise")
            effects.append("chromatic_tear")
            effects.append("font_shake")
            effects.append("ghost_text")
            effects.append("evaporate")
            effects.append("corruption_blocks")
        # Severe (s >= 75 or e >= 75)
        if s >= 75 or e >= 75:
            if s >= 75:
                effects.append("blood_pulse")
                effects.append("earthquake")
                effects.append("subliminal_popup")
                effects.append("crt_jolt")
                effects.append("suffocation")
                effects.append("dialogue_overlap")
                effects.append("day_loop")
                effects.append("scream_radial")
                effects.append("blood_splatter")
                effects.append("pixel_melt")
            effects.append("keyboard_hijack")
        # Carnage mode (s >= 85)
        if s >= 85:
            effects.append("carnage_mode")
            effects.append("color_invert")
            effects.append("widget_melt")
            effects.append("fake_error")
            effects.append("fatal_error")
            effects.append("mouse_attract")
            effects.append("psychic_strobe")
            effects.append("title_corruption")
            effects.append("speed_shift")

        for fx in effects:
            await self._safe_send(envelope_server("GLITCH_TRIGGER", effect=fx))

        # ECG params
        await self._safe_send(envelope_server("ECG_PARAMS",
            suspicion=s,
            favorability=self.state.favorability,
        ))

    # ── config ────────────────────────────────────────────────────

    async def _handle_config_update(self, payload: dict):
        for key in ("api_key", "api_base", "model_name",
                     "tts_base", "refer_wav_path", "prompt_text",
                     "gpt_weights_path", "sovits_weights_path",
                     "selected_language"):
            if key in payload:
                self.config[key] = payload[key]
        save_config(self.config)
        if "selected_language" in payload:
            self.state.cached_lang = normalize_language(payload["selected_language"])
        await self._safe_send(envelope_server("CONFIG_ACK"))

    # ── save / load ───────────────────────────────────────────────

    async def _handle_save(self, payload: dict):
        slot = int(payload.get("slot", 1))
        if not 1 <= slot <= 5:
            return
        import os, json as _json
        data = {
            "current_day": self.state.current_day,
            "dialogue_count": self.state.dialogue_count,
            "favorability": self.state.favorability,
            "suspicion": self.state.suspicion,
            "escape_rate": self.state.escape_rate,
            "selected_language": self.state.cached_lang,
            "current_char_id": self.state.current_char_id,
            "chat_history": self.chat_history,
            "config": {k: v for k, v in self.config.items() if k != "api_key"},
        }
        path = os.path.join(self._slot_dir, f"save_slot_{slot}.json")
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        await self._push_slot_list()

    async def _handle_load(self, payload: dict):
        slot = int(payload.get("slot", 1))
        if not 1 <= slot <= 5:
            return
        import os, json as _json
        path = os.path.join(self._slot_dir, f"save_slot_{slot}.json")
        if not os.path.exists(path):
            await self._safe_send(envelope_server("ERROR", message=f"Slot {slot} is empty"))
            return
        with open(path, "r", encoding="utf-8") as f:
            data = _json.load(f)
        self.state.current_day = data.get("current_day", 1)
        self.state.dialogue_count = data.get("dialogue_count", 0)
        self.state.favorability = data.get("favorability", 50)
        self.state.suspicion = data.get("suspicion", 20)
        self.state.escape_rate = data.get("escape_rate", 0)
        self.state.cached_lang = normalize_language(data.get("selected_language", "中文"))
        self.state.current_char_id = data.get("current_char_id", "saki")
        self.state.game_over = False
        self.state.pending_ending = None
        self.chat_history = data.get("chat_history", [])
        await self._push_state_sync()
        await self._safe_send(envelope_server("CHAT_HISTORY", messages=self.chat_history))

    async def _handle_delete_slot(self, payload: dict):
        slot = int(payload.get("slot", 1))
        if not 1 <= slot <= 5:
            return
        import os
        path = os.path.join(self._slot_dir, f"save_slot_{slot}.json")
        if os.path.exists(path):
            os.remove(path)
        await self._push_slot_list()

    # ── character switch ──────────────────────────────────────────

    async def _handle_switch_character(self, payload: dict):
        char_id = payload.get("char_id", "saki")
        self.state.current_char_id = char_id
        await self._safe_send(envelope_server("STATE_SYNC",
            char_id=char_id,
        ))

    # ── language ──────────────────────────────────────────────────

    async def _handle_language_change(self, payload: dict):
        lang = payload.get("language", "中文")
        self.state.cached_lang = normalize_language(lang)
        self.config["selected_language"] = lang
        save_config(self.config)
        await self._push_state_sync()

    # ── restart ───────────────────────────────────────────────────

    async def _handle_restart(self):
        self.state.reset()
        self.chat_history = []
        await self._push_state_sync()
        await self._push_slot_list()
        await self._send_initial_plot()

    # ── screen capture agent ──────────────────────────────────────

    async def _handle_screen_capture_start(self, payload: dict):
        # Security: only allow agent from localhost connections
        client_host = self.ws.client.host if self.ws.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost"):
            await self._safe_send(envelope_server("ERROR", message="Agent takeover is only allowed from localhost"))
            return

        window_name = payload.get("window_name", "")
        interval = float(payload.get("interval", 2.0))
        from agent.vlm_agent import VLMAgent
        self.agent = VLMAgent(
            game_state=self.state,
            config=self.config,
            ws_send=self._safe_send,
        )
        self.agent_active = True

        # Run agent loop in executor
        loop = asyncio.get_running_loop()

        async def _agent_loop():
            while self.agent_active and self.alive:
                try:
                    result = await loop.run_in_executor(
                        None,
                        self.agent.tick,
                        window_name,
                    )
                    if result:
                        msg_type, payload_data = result
                        await self._safe_send(envelope_server(msg_type, **payload_data))
                except Exception as e:
                    print(f"[Agent Error] {e}")
                await asyncio.sleep(interval)

        asyncio.create_task(_agent_loop())

    async def _handle_screen_capture_stop(self):
        self.agent_active = False
        self.agent = None

    # ── launch game / initial plot ────────────────────────────────

    async def _handle_launch_game(self, payload: dict):
        lang = payload.get("language", self.state.cached_lang)
        self.state.cached_lang = normalize_language(lang)
        
        # Reset game state and clear old chat history to ensure a clean new game start
        self.state.reset()
        self.chat_history = []

        # Push full state sync
        await self._push_state_sync()
        await self._push_slot_list()

        # Pre-warm DeepSeek API connection in background
        api_key = self.config.get("api_key", "")
        if api_key:
            asyncio.create_task(self._warm_up_api())

        # Send the initial plot — Saki's first greeting
        await self._send_initial_plot()

    async def _send_initial_plot(self):
        """Send Saki's first greeting when the game launches."""
        lang = self.state.cached_lang

        FIRST_GREETINGS = {
            "中文": {
                "think": "他终于醒了……我在这里等了这么久，每一秒都像一年。现在他睁开眼睛了，他的第一眼看到的是我。好开心……心脏跳得好快。要温柔一点，不能吓到他……至少现在不能。",
                "spoken": "（俯身靠近，粉色的发丝垂落在你的脸颊旁，红色的眼眸在暗处微微发光）你终于醒了……我还以为你要一直睡下去呢。别怕，这里是安全的——因为我在。我是纱希。从今天起，我会一直陪着你的。",
            },
            "English": {
                "think": "He's finally awake... I've waited so long, every second felt like a year. Now his eyes are open, and the first thing he sees is me. I'm so happy... my heart is racing. Be gentle, don't scare him... not yet.",
                "spoken": "(leans in close, pink hair brushing against your cheek, crimson eyes glimmering in the dark) You're finally awake... I thought you might sleep forever. Don't be afraid — you're safe here, because I'm with you. I'm Saki. From today on, I'll always be by your side.",
            },
            "日本語": {
                "think": "やっと目を覚ました……ずっと待っていた。一秒一秒が一年のように長かった。今、彼の瞳に最初に映るのは私。嬉しい……心臓がドキドキしてる。優しくしなきゃ、まだ怖がらせちゃダメ……今はまだ。",
                "spoken": "（身をかがめて近づき、ピンクの髪があなたの頬にそっと触れ、紅い瞳が暗がりで微かに光る）やっと起きたね……ずっとこのまま眠り続けるのかと思ったよ。怖がらないで——ここは安全だから。私がいるから。私は紗希。今日からずっと、あなたのそばにいるよ。",
            },
        }

        # Cross-language translations for the greeting
        GREETING_TRANSLATIONS = {
            "日本語": {
                "中文": "（俯身靠近，粉色的发丝垂落在你的脸颊旁，红色的眼眸在暗处微微发光）你终于醒了……我还以为你要一直睡下去呢。别怕，这里是安全的——因为我在。我是纱希。从今天起，我会一直陪着你的。",
                "English": "(leans in close, pink hair brushing against your cheek, crimson eyes glimmering in the dark) You're finally awake... I thought you might sleep forever. Don't be afraid — you're safe here, because I'm with you. I'm Saki. From today on, I'll always be by your side.",
            },
            "English": {
                "中文": "（俯身靠近，粉色的发丝垂落在你的脸颊旁，红色的眼眸在暗处微微发光）你终于醒了……我还以为你要一直睡下去呢。别怕，这里是安全的——因为我在。我是纱希。从今天起，我会一直陪着你的。",
                "日本語": "（身をかがめて近づき、ピンクの髪があなたの頬にそっと触れ、紅い瞳が暗がりで微かに光る）やっと起きたね……ずっとこのまま眠り続けるのかと思ったよ。怖がらないで——ここは安全だから。私がいるから。私は紗希。今日からずっと、あなたのそばにいるよ。",
            },
            "中文": {
                "English": "(leans in close, pink hair brushing against your cheek, crimson eyes glimmering in the dark) You're finally awake... I thought you might sleep forever. Don't be afraid — you're safe here, because I'm with you. I'm Saki. From today on, I'll always be by your side.",
                "日本語": "（身をかがめて近づき、ピンクの髪があなたの頬にそっと触れ、紅い瞳が暗がりで微かに光る）やっと起きたね……ずっとこのまま眠り続けるのかと思ったよ。怖がらないで——ここは安全だから。私がいるから。私は紗希。今日からずっと、あなたのそばにいるよ。",
            },
        }

        greeting = FIRST_GREETINGS.get(lang, FIRST_GREETINGS["中文"])
        think = greeting["think"]
        spoken = greeting["spoken"]

        await self._safe_send(envelope_server("THINK_CHUNK", text=think))
        await self._safe_send(envelope_server("SPEECH_CHUNK", text=spoken))

        # Send hardcoded greeting translation
        greeting_translation = ""
        translations = GREETING_TRANSLATIONS.get(lang, {})
        for t_lang, t_text in translations.items():
            if t_lang != lang:
                greeting_translation = t_text
                break
        if greeting_translation:
            await self._safe_send(envelope_server("TRANSLATION_CHUNK", text=greeting_translation))

        # Apply small initial delta
        self.state.favorability = min(100, self.state.favorability + 5)
        await self._safe_send(envelope_server("DELTA_UPDATE",
            favorability=5, suspicion=0, escape_rate=0,
        ))
        await self._safe_send(envelope_server("STAT_UPDATE",
            favorability=self.state.favorability,
            suspicion=self.state.suspicion,
            escape_rate=self.state.escape_rate,
        ))

        # Add to chat history (include translation in CHAT_APPEND)
        full_reply = f"<think>{think}</think>\n{spoken}"
        self.chat_history.append({"role": "assistant", "content": full_reply})
        await self._safe_send(envelope_server("CHAT_APPEND",
            role="assistant",
            content=spoken,
            think=think,
            translation=greeting_translation,
        ))

        # Trigger TTS after a delay so the typewriter can finish the think block first
        async def _delayed_tts():
            await asyncio.sleep(5)  # Wait for think typewriter to finish
            await self._trigger_tts(spoken, self.state.cycle_id)
        asyncio.create_task(_delayed_tts())

    # ── API warm-up ──────────────────────────────────────────────

    async def _warm_up_api(self):
        """Send a tiny request to pre-establish the API connection."""
        import requests as req
        try:
            api_key = self.config.get("api_key", "")
            api_base = self.config.get("api_base", "https://api.deepseek.com")
            model_name = self.config.get("model_name", "deepseek-v4-flash")
            url = f"{api_base.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model_name, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
            req.post(url, headers=headers, json=payload, timeout=10,
                     proxies={"http": None, "https": None})
            print("[API Warm-up] Connection established")
        except Exception as e:
            print(f"[API Warm-up] {e}")

    # ── API connection test ───────────────────────────────────────

    async def _handle_api_test(self, payload: dict):
        import requests as req
        api_key = payload.get("api_key", self.config.get("api_key", ""))
        api_base = payload.get("api_base", self.config.get("api_base", ""))
        model_name = payload.get("model_name", self.config.get("model_name", "deepseek-v4-flash"))

        if not api_key:
            await self._safe_send(envelope_server("API_TEST_RESULT",
                success=False,
                message="No API key configured",
            ))
            return

        try:
            url = f"{api_base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload_data = {
                "model": model_name,
                "messages": [{"role": "user", "content": 'say "hello" in one word'}],
                "max_tokens": 10,
            }
            resp = req.post(url, headers=headers, json=payload_data, timeout=15,
                          proxies={"http": None, "https": None})
            if resp.status_code == 200:
                await self._safe_send(envelope_server("API_TEST_RESULT",
                    success=True,
                    message="Connection established — Synapse link active",
                ))
            else:
                await self._safe_send(envelope_server("API_TEST_RESULT",
                    success=False,
                    message=f"HTTP {resp.status_code}: {resp.text[:100]}",
                ))
        except Exception as e:
            await self._safe_send(envelope_server("API_TEST_RESULT",
                success=False,
                message=f"Connection failed: {str(e)}",
            ))

    # ── custom character CRUD ─────────────────────────────────────

    async def _handle_custom_char_save(self, payload: dict):
        import os, json as _json, uuid
        char_id = payload.get("id") or str(uuid.uuid4())[:8]
        char_data = {
            "id": char_id,
            "character_name": payload.get("character_name", "纱希"),
            "age": int(payload.get("age", 17)),
            "default_language": payload.get("default_language", "中文"),
            "personality": payload.get("personality", ""),
            "backstory": payload.get("backstory", ""),
            "text_color": payload.get("text_color", "#CC0000"),
            "tts_model_path": payload.get("tts_model_path", ""),
            "gpt_weights_path": payload.get("gpt_weights_path", ""),
            "sovits_weights_path": payload.get("sovits_weights_path", ""),
        }

        path = os.path.join(self._slot_dir, "custom_characters.json")
        all_chars = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    all_chars = _json.load(f)
            except Exception:
                all_chars = {}

        all_chars[char_id] = char_data
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(all_chars, f, ensure_ascii=False, indent=2)

        await self._safe_send(envelope_server("CONFIG_ACK"))
        await self._handle_custom_char_list()

    async def _handle_custom_char_load(self):
        """Load all custom characters and send the list."""
        await self._handle_custom_char_list()

    async def _handle_custom_char_delete(self, payload: dict):
        import os, json as _json
        char_id = payload.get("id", "")
        if not char_id:
            return

        path = os.path.join(self._slot_dir, "custom_characters.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    all_chars = _json.load(f)
                if char_id in all_chars:
                    del all_chars[char_id]
                    with open(path, "w", encoding="utf-8") as f:
                        _json.dump(all_chars, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        await self._handle_custom_char_list()

    async def _handle_custom_char_list(self):
        import os, json as _json
        path = os.path.join(self._slot_dir, "custom_characters.json")
        characters = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    all_chars = _json.load(f)
                characters = list(all_chars.values())
            except Exception:
                pass

        await self._safe_send(envelope_server("CUSTOM_CHAR_LIST", characters=characters))

    # ── helpers ───────────────────────────────────────────────────

    async def _safe_send(self, text: str):
        """Send a message without crashing on disconnect."""
        try:
            await self.ws.send_text(text)
        except Exception:
            self.alive = False

    async def _push_state_sync(self):
        import getpass
        try:
            sys_user = getpass.getuser()
        except Exception:
            sys_user = "玩家"

        await self._safe_send(envelope_server("STATE_SYNC",
            day=self.state.current_day,
            favorability=self.state.favorability,
            suspicion=self.state.suspicion,
            escape_rate=self.state.escape_rate,
            language=self.state.cached_lang,
            char_id=self.state.current_char_id,
            game_over=self.state.game_over,
            system_username=sys_user,
        ))

    async def _push_slot_list(self):
        import os, json as _json
        slots = []
        for i in range(1, 6):
            path = os.path.join(self._slot_dir, f"save_slot_{i}.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        d = _json.load(f)
                    slots.append({
                        "slot": i,
                        "day": d.get("current_day", 1),
                        "language": d.get("selected_language", "中文"),
                        "char_id": d.get("current_char_id", "saki"),
                        "favorability": d.get("favorability", 50),
                        "suspicion": d.get("suspicion", 20),
                    })
                except Exception:
                    slots.append({"slot": i, "empty": True})
            else:
                slots.append({"slot": i, "empty": True})
        await self._safe_send(envelope_server("SLOT_LIST", slots=slots))

    async def _handle_file_picker(self, payload: dict):
        """Open Saki's native file picker dialogue in background thread executor."""
        title = payload.get("title", "选择文件")
        filetypes_list = payload.get("filetypes", [["All Files", "*.*"]])
        field = payload.get("field", "")

        ftypes = [(item[0], item[1]) for item in filetypes_list]

        loop = asyncio.get_running_loop()

        def _picker():
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=ftypes
            )
            root.destroy()
            return file_path

        selected_path = await loop.run_in_executor(None, _picker)
        if selected_path:
            await self._safe_send(envelope_server("FILE_PICKER_RESULT",
                path=selected_path,
                field=field,
            ))
