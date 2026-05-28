# -*- coding: utf-8 -*-
"""
Standalone offline player-intent keyword classifier.

Wraps the intent classification logic from resources.game_constants
so the ai/ package has its own clear entry point for NLP tasks.
"""

from resources.game_constants import (
    classify_player_intent,
    roll_delta_for_intent,
    INTENT_RULES,
)


def classify(user_input):
    """Classify player input into an intent rule dict.

    Parameters
    ----------
    user_input : str
        Raw text from the player.

    Returns
    -------
    dict
        Intent rule with keys: name, keywords, delta, prompt.
    """
    return classify_player_intent(user_input)


def roll_delta(intent_rule):
    """Roll random delta values within the intent rule's range.

    Returns (delta_favorability, delta_suspicion, delta_escape_rate).
    """
    return roll_delta_for_intent(intent_rule)


def get_all_intents():
    """Return the full INTENT_RULES list for inspection."""
    return INTENT_RULES
