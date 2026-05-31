"""
System prompt builder — thin wrapper around core.game_state functions.

Provides a single entry-point that extracts relevant fields from a
GameState instance and delegates to the core prompt builder.
"""
from resources.game_constants import normalize_language, detect_language
from core.game_state import build_role_simulation_prompt


def get_system_prompt(game_state):
    """Build the full localized role-simulation system prompt.

    Parameters
    ----------
    game_state : core.game_state.GameState
        The current game state holding language, stats, and day.

    Returns
    -------
    str — The complete system prompt for chat_history[0]["content"].
    """
    import os
    import json
    selected_lang = normalize_language(game_state.cached_lang)
    user_lang = detect_language(game_state.last_user_input, selected_lang)
    base_prompt = build_role_simulation_prompt(
        selected_lang=selected_lang,
        user_lang=user_lang,
        current_day=game_state.current_day,
        favorability=game_state.favorability,
        suspicion=game_state.suspicion,
        escape_rate=game_state.escape_rate,
    )

    # Force think block to use player's language (spoken stays in game language)
    if user_lang and user_lang != selected_lang:
        # Replace the think language rule directly in the prompt
        lang_names = {"中文": "Simplified Chinese", "English": "English", "日本語": "Japanese"}
        think_lang = lang_names.get(user_lang, user_lang)
        # Override any existing think rule
        base_prompt = base_prompt.replace(
            "内心独白也必须使用简体中文",
            f"内心独白必须使用{think_lang}"
        ).replace(
            "内心独白も日本語で書き",
            f"内心独白は{think_lang}で書くこと"
        ).replace(
            "The inner monologue must also be written in English",
            f"The inner monologue must be written in {think_lang}"
        )
        base_prompt += (
            f"\n\n【THINK LANGUAGE — FINAL RULE】"
            f"\n`<think>` MUST be in 【{think_lang}】 ONLY. Spoken text stays in 【{selected_lang}】."
        )

    char_id = getattr(game_state, "current_char_id", "saki")
    if char_id == "saki":
        return base_prompt

    # Check if it's a custom character from custom_characters.json
    custom_chars = {}
    chars_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "custom_characters.json")
    if os.path.exists(chars_path):
        try:
            with open(chars_path, "r", encoding="utf-8") as f:
                custom_chars = json.load(f)
        except Exception:
            pass

    if char_id in custom_chars:
        cdata = custom_chars[char_id]
        name = cdata.get("character_name", cdata.get("name", "自定义角色"))
        age = cdata.get("age", "18")
        personality = cdata.get("personality", "偏执、极度敏感的病娇，占有欲极强")
        main_story = cdata.get("backstory", cdata.get("main_story", "将你关在密室里"))
        character_plot = cdata.get("character_plot", "只要你顺从就温柔，一旦你想走就爆发疯狂")
        world_view = cdata.get("world_view", "阴暗冷酷的地牢")

        prompt = base_prompt
        prompt = prompt.replace("扮演纱希 Saki", f"扮演{name}")
        prompt = prompt.replace("扮演纱希Saki", f"扮演{name}")
        prompt = prompt.replace("扮演Saki", f"扮演{name}")
        prompt = prompt.replace("扮演 纱希 Saki", f"扮演{name}")
        prompt = prompt.replace("纱希 Saki", name)
        prompt = prompt.replace("Saki", name)
        prompt = prompt.replace("纱希", name)
        prompt = prompt.replace("病娇少女", "病娇角色")
        prompt = prompt.replace("她对玩家有强烈依恋", "该角色对玩家有强烈依恋")
        prompt = prompt.replace("她对玩家", "该角色对玩家")
        prompt = prompt.replace("她", "该角色")
        prompt = prompt.replace("乖猫咪", "心爱之人")

        injection = (
            f"\n\n【自定义角色脑回路设定】\n"
            f"- 角色姓名：{name}\n"
            f"- 角色年龄：{age}\n"
            f"- 角色性格：{personality}\n"
            f"- 故事主线：{main_story}\n"
            f"- 人物剧情：{character_plot}\n"
            f"- 世界观：{world_view}\n\n"
            f"注意：你现在扮演的是 {name}。你必须严格按照以上性格、背景、主线和剧情设定来进行模拟。"
        )
        return prompt + injection

    return base_prompt


def get_vlm_system_prompt(game_state) -> str:
    """Build the VLM agent system prompt with current game context."""
    from agent.vlm_agent import VLM_SYSTEM_PROMPT
    return VLM_SYSTEM_PROMPT
