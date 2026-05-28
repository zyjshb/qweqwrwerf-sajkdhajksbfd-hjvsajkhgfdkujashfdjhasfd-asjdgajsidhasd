# -*- coding: utf-8 -*-
"""
GPT-SoVITS TTS client wrapper — endpoint probing, speech synthesis,
and language-aware model hot-switching.

Provides the TTSClient class used by the WebSocket game session.
"""
from __future__ import annotations
import os
import tempfile
import time
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from resources.game_constants import (
    clean_text_for_tts,
    language_to_tts_code,
    detect_language,
    build_tts_request_params,
    normalize_language,
)


class TTSClient:
    """Manages GPT-SoVITS TTS synthesis with language auto-detection
    and model hot-switching."""

    def __init__(self):
        self._working_endpoint: str = "/tts"
        self._current_model_lang: Optional[str] = None
        self._probed: bool = False

    # ── public API ───────────────────────────────────────────────

    def clean_text_for_tts(self, text: str) -> str:
        """Strip think blocks, JSON, and non-speech tokens from dialogue."""
        return clean_text_for_tts(text)

    def synthesize(self, text: str, language: str,
                   config: dict) -> Optional[str]:
        """Synthesize speech and save to a temp WAV file.

        Returns the absolute path to the WAV file, or None on failure.
        """
        if not HAS_REQUESTS:
            return None

        tts_base = config.get("tts_base", "http://127.0.0.1:9880")
        if not tts_base:
            return None

        # Probe endpoint if needed
        if not self._probed:
            self._probe(tts_base, config)

        # Determine reference audio and weights based on language
        ref_wav, prompt_text, gpt_w, sovits_w = self._resolve_voice_assets(
            language, config
        )

        # Hot-switch model weights if language changed
        if language != self._current_model_lang:
            self._hot_load_weights(tts_base, gpt_w, sovits_w)
            self._current_model_lang = language

        # Call synthesis
        target_lang_code = language_to_tts_code(language)
        wav_bytes = self._call_synthesis(
            text, ref_wav, prompt_text, tts_base, target_lang_code
        )
        if wav_bytes is None:
            return None

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", prefix="saki_tts_", delete=False
        )
        tmp.write(wav_bytes)
        tmp.close()
        return tmp.name

    # ── internals ────────────────────────────────────────────────

    def _probe(self, tts_base: str, config: dict):
        """Discover working TTS endpoint."""
        url = tts_base.rstrip("/")
        ref_wav = config.get("refer_wav_path", "")
        prompt_text = config.get("prompt_text", "")

        for ep in ["/tts", "/tts_to_audio", ""]:
            target = f"{url}{ep}"
            try:
                params = {
                    "refer_wav_path": ref_wav,
                    "prompt_text": prompt_text,
                    "prompt_language": "zh",
                    "text": "hello",
                    "text_language": "zh",
                }
                r = requests.get(target, params=params, timeout=2.5,
                               proxies={"http": None, "https": None})
                if r.status_code == 200:
                    self._working_endpoint = ep
                    print(f"[TTS] Endpoint found: {target}")
                    break
            except Exception:
                pass
        self._probed = True

    def _resolve_voice_assets(self, language: str, config: dict):
        """Return (ref_wav, prompt_text, gpt_weights, sovits_weights)
        for the detected language, falling back to config defaults."""
        lang = normalize_language(language)

        # Default voice assets per language
        if lang == "日本語":
            defaults = {
                "ref_wav": "models/mi/mita.wav",
                "prompt": "どうして、また、た、わかった、またか、中身が気になるんでしょ?",
                "gpt": "models/mita-e15.ckpt",
                "sovits": "models/mita_e10_s860.pth",
            }
        else:
            defaults = {
                "ref_wav": "models/hua/huahuo.wav",
                "prompt": "你要是有什么危险的差事要办，尽管来找我。",
                "gpt": "models/hua/huahuo.ckpt",
                "sovits": "models/hua/huahuo.pth",
            }

        ref_wav = config.get("refer_wav_path") or defaults["ref_wav"]
        prompt_text = config.get("prompt_text") or defaults["prompt"]
        gpt_w = config.get("gpt_weights_path") or defaults["gpt"]
        sovits_w = config.get("sovits_weights_path") or defaults["sovits"]

        # Resolve relative paths
        for p in [ref_wav, gpt_w, sovits_w]:
            if p and not os.path.isabs(p):
                p = os.path.abspath(p)

        return ref_wav, prompt_text, gpt_w, sovits_w

    def _hot_load_weights(self, tts_base: str, gpt_weights: str,
                           sovits_weights: str):
        """Send a weight-switch request to GPT-SoVITS."""
        try:
            url = f"{tts_base.rstrip('/')}/set_model_weights"
            payload = {
                "gpt_weights_path": gpt_weights,
                "sovits_weights_path": sovits_weights,
            }
            r = requests.post(url, json=payload, timeout=10)
            print(f"[TTS] Weight hot-load: {'OK' if r.status_code == 200 else 'FAIL'}")
        except Exception as e:
            print(f"[TTS] Weight hot-load error: {e}")

    def _call_synthesis(self, text: str, ref_wav: str, prompt_text: str,
                         tts_base: str, target_lang_code: str) -> Optional[bytes]:
        """Make the actual TTS HTTP request."""
        cleaned = clean_text_for_tts(text)
        if not cleaned:
            return None

        ref_lang = detect_language(prompt_text)
        prompt_lang_code = language_to_tts_code(ref_lang)
        target = f"{tts_base.rstrip('/')}{self._working_endpoint}"

        # Quality params first
        params = build_tts_request_params(
            ref_wav, prompt_text, prompt_lang_code,
            cleaned, target_lang_code, quality=True,
        )

        try:
            r = requests.get(target, params=params, timeout=35,
                           proxies={"http": None, "https": None})
        except Exception as e:
            print(f"[TTS] Request failed: {e}")
            return None

        # Fallback to basic params
        if r.status_code != 200:
            params = build_tts_request_params(
                ref_wav, prompt_text, prompt_lang_code,
                cleaned, target_lang_code, quality=False,
            )
            try:
                r = requests.get(target, params=params, timeout=35,
                               proxies={"http": None, "https": None})
            except Exception:
                return None

        if r.status_code == 200 and len(r.content) > 1000:
            return r.content

        return None
