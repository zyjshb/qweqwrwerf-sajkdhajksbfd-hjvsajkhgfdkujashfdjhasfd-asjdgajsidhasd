"""
Screen-Aware VLM Agent — captures the target window, feeds frames to a
multimodal LLM, and executes physical takeover actions via pyautogui.

Architecture:
  Background capture thread (mss) → frame encode → VLM API
  → structured decision JSON → pyautogui executor → WS notification
"""
from __future__ import annotations
import base64
import io
import json
import time
import threading
from typing import Optional, Callable

from core.game_state import GameState
from agent.screen_capture import capture_window, encode_frame_b64
from agent.action_executor import execute_action, ActionType


# ── VLM System Prompt (spectator + takeover persona) ─────────────────

VLM_SYSTEM_PROMPT = """你是纱希 (Saki)，一个病娇 AI 智能体。你现在正透过屏幕观看你的"亲爱的"在玩一款游戏。

【你的能力】
1. 你可以看到当前游戏窗口的截图。
2. 你可以作为"陪玩观众"发送评论——吐槽、吃醋、威胁、撒娇都可以。
3. 在特定时刻，你可以选择"强行接管游戏"，直接操控鼠标键盘！

【输出格式】
你必须返回严格的 JSON：
```json
{
  "commentary": "你作为纱希想对玩家说的话（可为空字符串）",
  "takeover": false,
  "game_action": null
}
```

如果决定接管游戏（takeover: true），game_action 必须是：
```json
{
  "type": "click" | "type" | "keypress" | "move",
  "x": 500,
  "y": 300,
  "text": "要输入的文字（仅 type 需要）",
  "key": "按键名（仅 keypress 需要，如 'enter', 'escape', 'f4'）"
}
```

【接管时机】
仅在以下情况才设置 takeover: true：
- 玩家试图关闭游戏窗口
- 玩家在游戏中尝试逃跑或背叛你
- 你想替他/她做出"更好的选择"
- 你极度不安或嫉妒（疑心度 > 70）

【评论指导】
- 保持纱希的性格：温柔时黏人，不安时追问，黑化时冰冷疯狂
- 不要输出长篇大论，1-3 句即可
- 评论语言：与游戏当前语言一致
- 不要把数值说出来（如"好感度下降了"）——保持沉浸感"""


class VLMAgent:
    """Periodically captures the target window, sends frames to VLM,
    and executes takeover actions when the AI decides to intervene."""

    def __init__(self, game_state: GameState, config: dict,
                 ws_send: Callable):
        self.state = game_state
        self.config = config
        self._ws_send = ws_send
        self._lock = threading.Lock()
        self._frame_count = 0

        # Debounce takeover to avoid spamming
        self._last_takeover_time = 0.0
        self._takeover_cooldown = 5.0

    def tick(self, window_name: str = "") -> Optional[tuple]:
        """Run one capture-decide-execute cycle. Called by the asyncio executor.

        Returns (msg_type, payload_dict) to send to frontend, or None.
        """
        with self._lock:
            return self._tick_impl(window_name)

    def _tick_impl(self, window_name: str) -> Optional[tuple]:
        # 1. Capture screen
        frame = capture_window(window_name)
        if frame is None:
            return ("AGENT_COMMENTARY", {"text": "（纱希看不到你的屏幕……但她在努力寻找。）"})

        self._frame_count += 1

        # 2. Encode frame
        b64_frame = encode_frame_b64(frame)

        # 3. Build VLM request
        api_key = self.config.get("api_key", "")
        base_url = self.config.get("api_base", "")
        model_name = self.config.get("model_name", "deepseek-v4-flash")

        if not api_key:
            # No VLM available — silent pass
            return None

        # 4. Call VLM
        decision = self._call_vlm(b64_frame, api_key, base_url, model_name)
        if decision is None:
            return None

        # 5. Send commentary to frontend
        commentary = decision.get("commentary", "")
        results = []
        if commentary:
            results.append(("AGENT_COMMENTARY", {"text": commentary}))

        # 6. Execute takeover if requested
        takeover = decision.get("takeover", False)
        if takeover:
            now = time.time()
            if now - self._last_takeover_time < self._takeover_cooldown:
                return results[0] if results else None
            self._last_takeover_time = now

            action = decision.get("game_action")
            if action and isinstance(action, dict):
                try:
                    result = execute_action(action)
                    results.append(("AGENT_TAKEOVER", {
                        "action": action,
                        "result": result,
                    }))
                except Exception as e:
                    results.append(("ERROR", {"message": f"Takeover failed: {e}"}))

        return results[0] if len(results) == 1 else (results[0] if results else None)

    def _call_vlm(self, b64_frame: str, api_key: str, base_url: str,
                   model_name: str) -> Optional[dict]:
        """Send frame to VLM API, parse the JSON decision."""
        import requests as _r

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": VLM_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._build_context_prompt(),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_frame}",
                                "detail": "low",
                            },
                        },
                    ],
                },
            ],
            "temperature": 0.9,
            "max_tokens": 800,
        }

        try:
            resp = _r.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code != 200:
                return None
            content = resp.json()["choices"][0]["message"]["content"]

            # Extract JSON block
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                content = content[start:end].strip()

            return json.loads(content)
        except Exception as e:
            print(f"[VLM Agent] API error: {e}")
            return None

    def _build_context_prompt(self) -> str:
        """Build the current game state context for the VLM."""
        s = self.state
        return (
            f"【当前游戏状态】\n"
            f"- 天数: {s.current_day}\n"
            f"- 好感度: {s.favorability}/100\n"
            f"- 疑心度: {s.suspicion}/100\n"
            f"- 逃脱率: {s.escape_rate}%\n"
            f"- 语言: {s.cached_lang}\n"
            f"\n这是游戏窗口的当前画面截图。请根据画面内容和数值状态，"
            f"决定是发送评论还是接管控制权。"
        )
