# -*- coding: utf-8 -*-
"""
Parse raw API responses into structured game data.

Extracts the inner monologue (<think> block), spoken dialogue, and the
JSON delta payload that the LLM appended.
"""
import json
import re

from resources.game_constants import (
    normalize_language,
    detect_language,
    ensure_readability_translation,
    extract_terminal_parenthetical_translation,
    strip_terminal_parenthetical_translation,
)


def parse_api_response(raw_text, user_input, game_state, skip_offline_translation=False):
    """Parse a raw LLM reply into structured components."""
    raw_delta = None
    spoken_text = raw_text

    # ---- 1. Split on the canonical || delimiter ----
    if "||" in raw_text:
        try:
            parts = raw_text.split("||")
            spoken_text = parts[0].strip()
            json_str = parts[1].strip()
            raw_delta = json.loads(json_str)
        except Exception:
            pass

    # ---- 2. Regex fallback: find a valid-looking delta block ----
    if raw_delta is None:
        match = re.search(r'\{[^{}]*"favorability"[^{}]*\}', raw_text)
        if match:
            try:
                raw_delta = json.loads(match.group(0))
                spoken_text = raw_text.replace(
                    match.group(0), ""
                ).replace("||", "").strip()
            except Exception:
                pass

    # ---- 3. Strip any residual || tokens from spoken text ----
    if "||" in spoken_text:
        spoken_text = spoken_text.split("||")[0].strip()

    # ---- 4. Extract <think>...</think> block ----
    think_content = ""
    lower_text = spoken_text.lower()
    start_idx = lower_text.find("<think>")
    if start_idx != -1:
        end_idx = lower_text.find("</think>", start_idx + 7)
        if end_idx != -1:
            think_content = spoken_text[start_idx + 7:end_idx].strip()
            spoken_text = (
                spoken_text[:start_idx] + " " + spoken_text[end_idx + 8:]
            )
        else:
            think_content = spoken_text[start_idx + 7:].strip()
            spoken_text = spoken_text[:start_idx]

    # ---- 5. Strip inner monologue leaked into spoken text ----
    spoken_text = _strip_monologue_from_spoken(spoken_text)

    # ---- 6. Extract translation if present at the end ----
    selected_lang = normalize_language(game_state.cached_lang)
    user_lang = detect_language(user_input, selected_lang)
    translation = extract_terminal_parenthetical_translation(spoken_text, user_lang)
    if translation:
        spoken_text = strip_terminal_parenthetical_translation(spoken_text, user_lang)

    return {
        "think": think_content,
        "spoken": spoken_text,
        "delta": raw_delta,
        "translation": translation,
    }


def _strip_monologue_from_spoken(text):
    """Remove inner monologue that leaked into the spoken text."""
    if not text:
        return text

    # Strip bare monologue before first action description
    first_action = re.search(r'[（\(][^\)）\（\(]{1,40}[）\)]', text)
    if first_action and first_action.start() > 5:
        text = text[first_action.start():]

    # Remove long parenthetical monologue blocks (>40 chars)
    result = []
    i = 0
    while i < len(text):
        if text[i] in ('(', '（'):
            open_char = text[i]
            close_char = ')' if open_char == '(' else '）'
            depth = 1
            j = i + 1
            while j < len(text) and depth > 0:
                if text[j] == open_char:
                    depth += 1
                elif text[j] == close_char:
                    depth -= 1
                j += 1
            block_content = text[i + 1:j - 1].strip()
            if len(block_content) <= 40:
                result.append(text[i:j])
            i = j
        else:
            result.append(text[i])
            i += 1

    return ''.join(result).strip()
