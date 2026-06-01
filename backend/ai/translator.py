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

    # ---- 1. Extract delta from the LAST ||...|| block (most reliable) ----
    delta_matches = list(re.finditer(r'\|\|(\{.*?"favorability".*?\})\|\|', raw_text))
    if delta_matches:
        try:
            last = delta_matches[-1]
            raw_delta = json.loads(last.group(1))
            # Remove ALL || blocks from spoken text
            spoken_text = re.sub(r'\|\|.*?\|\|', '', raw_text).strip()
        except Exception:
            pass

    # ---- 2. Regex fallback: find a valid-looking delta block ----
    if raw_delta is None:
        match = re.search(r'\{[^{}]*"favorability"[^{}]*\}', raw_text)
        if match:
            try:
                raw_delta = json.loads(match.group(0))
                spoken_text = raw_text.replace(match.group(0), "").replace("||", "").strip()
            except Exception:
                pass

    # ---- 3. Strip any residual || tokens from spoken text ----
    spoken_text = re.sub(r'\|\|.*?\|\|', '', spoken_text).strip()

    # ---- 4. Extract <think> or <thinking> block ----
    think_content = ""
    lower_text = spoken_text.lower()
    for tag in ("<think>", "<thinking>"):
        start_idx = lower_text.find(tag)
        if start_idx != -1:
            tag_len = len(tag)
            end_tag = "</think>" if tag == "<think>" else "</thinking>"
            end_idx = lower_text.find(end_tag, start_idx + tag_len)
            if end_idx != -1:
                think_content = spoken_text[start_idx + tag_len:end_idx].strip()
                spoken_text = spoken_text[:start_idx] + " " + spoken_text[end_idx + len(end_tag):]
            else:
                think_content = spoken_text[start_idx + tag_len:].strip()
                spoken_text = spoken_text[:start_idx]
            break

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

    # Remove long parenthetical monologue blocks (>40 chars).
    # Short blocks (≤40 chars) are treated as action descriptions and kept.
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

    text = ''.join(result).strip()

    # Strip a leading sequence of 2+ parenthetical blocks (inner-monologue
    # fragments that leaked before the actual dialogue).  A single block is
    # treated as a legitimate action description and kept.
    leading = re.match(r'^([（\(][^）\)]*[）\)]\s*){2,}', text)
    if leading:
        after = text[leading.end():].strip()
        if after:
            text = after

    return text


# ── Japanese kanji hallucination auto-correction ─────────────────────
# Reasoning models (deepseek-v4-pro etc.) occasionally confuse similar-
# looking kanji in Japanese output: 違う→進う, 嘘→嵯, 遣い→造い, etc.
# This map targets high-confidence errors; each key is a compiled regex.

_JAPANESE_CORRECTIONS = [
    # 違う (chigau — different / wrong)
    (re.compile(r'進う'), '違う'),
    # 嘘 (uso — lie)
    (re.compile(r'嵯(?=だ|じゃ|つ|を|は|の|か|な|よ|ね|。|、|で|っ)'), '嘘'),
    # 遣い (zukai — e.g. 上目遣い, 言葉遣い)
    (re.compile(r'造い(?=に|は|が|を|の|で|。|、|見|睨|使)'), '遣い'),
    # 約束 (yakusoku — promise)
    (re.compile(r'約東'), '約束'),
    # 誓う (chikau — swear)
    (re.compile(r'誓ぅ'), '誓う'),
    # 震え (furue — tremble)
    (re.compile(r'震ぇ'), '震え'),
    # 本当 (hontou — really)
    (re.compile(r'本峠'), '本当'),
    # 離れ (hanare — separate) ← 誰れ
    (re.compile(r'誰れ(?=ない|た|て|る|そう|ば|。|、)'), '離れ'),
    # 目 (me — eye) ← 日 (in compound contexts)
    (re.compile(r'上日遣い'), '上目遣い'),
    (re.compile(r'日が(?=.*?(震|潤|光|輝|合|覚|醒|冴|見開|閉|据))'), '目が'),
    (re.compile(r'日を(?=.*?(見|開|閉|瞑|逸|細|輝|覚|醒|据|逸|背|伏))'), '目を'),
    # 見つめ (mitsume — stare)
    (re.compile(r'見つぬ'), '見つめ'),
    # 一緒 (issho — together)
    (re.compile(r'一緖'), '一緒'),
    # 永遠 (eien — forever)
    (re.compile(r'永道(?!に|を|が|の|は|で|、|。|り)'), '永遠'),
    # 瞳 (hitomi — pupil) ← 睡孔 (hallucinated compound)
    (re.compile(r'睡孔'), '瞳'),
    # 頼が → 顔が (when blushing context)
    (re.compile(r'頼が(?=.*?(赤|红|熱|火照|上気|染))'), '顔が'),
    # Various ぃ→い endings (small-i kana hallucination)
    (re.compile(r'嬉しぃ'), '嬉しい'),
    (re.compile(r'怖ぃ'), '怖い'),
    (re.compile(r'欲しぃ'), '欲しい'),
    (re.compile(r'新しぃ'), '新しい'),
    (re.compile(r'優しぃ'), '優しい'),
    (re.compile(r'寂しぃ'), '寂しい'),
    (re.compile(r'苦しぃ'), '苦しい'),
    (re.compile(r'楽しぃ'), '楽しい'),
    (re.compile(r'詳しぃ'), '詳しい'),
    # ちゃんと (chanto — properly)
    (re.compile(r'ちやんと'), 'ちゃんと'),
    # ぎゅっと (gyutto — tightly)
    (re.compile(r'ぎゆつと'), 'ぎゅっと'),
    # ドキドキ (dokidoki — heartbeat)
    (re.compile(r'ド丰'), 'ドキ'),
    # バクバク (bakubaku — pounding)
    (re.compile(r'バクパク'), 'バクバク'),
    # そば (soba — beside) ← そば (itself correct, but そぱ → そば)
    (re.compile(r'そぱ'), 'そば'),
    # もう (mou — already) ← もぅ
    (re.compile(r'もぅ'), 'もう'),
]


def auto_correct_japanese(text: str) -> str:
    """Apply targeted kanji corrections for reasoning-model hallucinations.

    Only fires on high-confidence patterns with context anchors.
    Returns the corrected text.
    """
    if not text:
        return text
    for pattern, replacement in _JAPANESE_CORRECTIONS:
        text = pattern.sub(replacement, text)
    return text
