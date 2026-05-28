"""
Physical action executor — translates structured game_action JSON
into real pyautogui mouse/keyboard operations on the player's system.
"""
from __future__ import annotations
from typing import Literal, Optional
import time

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

ActionType = Literal["click", "type", "keypress", "move"]


def execute_action(action: dict) -> dict:
    """Execute a single physical action on the host system.

    Parameters
    ----------
    action : dict with keys:
        type    — "click" | "type" | "keypress" | "move"
        x, y    — coordinates (for click, move)
        text    — string to type (for type)
        key     — key name (for keypress)

    Returns
    -------
    dict — {"success": bool, "detail": str}
    """
    if not HAS_PYAUTOGUI:
        return {"success": False, "detail": "pyautogui not installed"}

    try:
        action_type = action.get("type", "")

        if action_type == "click":
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            pyautogui.click(x, y)
            return {"success": True, "detail": f"clicked ({x}, {y})"}

        elif action_type == "type":
            text = str(action.get("text", ""))
            interval = 0.05  # human-like typing speed
            pyautogui.typewrite(text, interval=interval)
            return {"success": True, "detail": f"typed '{text[:30]}...'" if len(text) > 30 else f"typed '{text}'"}

        elif action_type == "keypress":
            key = str(action.get("key", "")).lower()
            # Map common key names
            key_map = {
                "enter": "enter",
                "escape": "esc",
                "esc": "esc",
                "f4": "f4",
                "alt": "alt",
                "tab": "tab",
                "space": "space",
                "backspace": "backspace",
            }
            resolved = key_map.get(key, key)
            pyautogui.press(resolved)
            return {"success": True, "detail": f"pressed '{resolved}'"}

        elif action_type == "move":
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            duration = float(action.get("duration", 0.3))
            pyautogui.moveTo(x, y, duration=duration)
            return {"success": True, "detail": f"moved to ({x}, {y})"}

        else:
            return {"success": False, "detail": f"unknown action type: {action_type}"}

    except Exception as e:
        return {"success": False, "detail": str(e)}
