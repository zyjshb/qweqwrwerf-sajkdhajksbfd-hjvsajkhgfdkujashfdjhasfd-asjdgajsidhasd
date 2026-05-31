"""
WebSocket JSON protocol v2.0 — strict message type definitions.

All communication between the Vue 3 frontend and FastAPI backend flows
through a single /ws/game WebSocket using these typed envelopes.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
import json
import time


# ── client → server ──────────────────────────────────────────────────

@dataclass
class ClientMessage:
    type: str  # see CLIENT_TYPES below
    payload: dict = field(default_factory=dict)
    ts: float = 0.0

    def __post_init__(self):
        if not self.ts:
            self.ts = time.time()


CLIENT_TYPES = {
    "CHAT_SEND",           # player sends a message
    "CONFIG_UPDATE",       # update API key / base / model / TTS settings
    "SAVE_SLOT",           # save to slot N
    "LOAD_SLOT",           # load from slot N
    "DELETE_SLOT",         # delete slot N
    "SWITCH_CHARACTER",    # F12 character toggle
    "LANGUAGE_CHANGE",     # change UI/game language
    "RESTART_GAME",        # start fresh
    "PING",                # latency probe
    "SCREEN_CAPTURE_START",# begin periodic screen capture
    "SCREEN_CAPTURE_STOP", # stop screen capture
    "LAUNCH_GAME",         # enter game from launcher, trigger initial plot
    "API_TEST",            # test API connection from launcher
    "REQUEST_FILE_PICKER", # open native file picker dialog
    "CUSTOM_CHAR_SAVE",    # save custom character to custom_characters.json
    "CUSTOM_CHAR_LOAD",    # load all custom characters
    "CUSTOM_CHAR_DELETE",  # delete a custom character by id
    "CUSTOM_CHAR_LIST",    # list custom character summaries
}


# ── server → client ──────────────────────────────────────────────────

@dataclass
class ServerMessage:
    type: str  # see SERVER_TYPES below
    payload: dict = field(default_factory=dict)
    ts: float = 0.0

    def __post_init__(self):
        if not self.ts:
            self.ts = time.time()

    def json(self) -> str:
        return json.dumps({"type": self.type, "payload": self.payload, "ts": self.ts}, ensure_ascii=False)


SERVER_TYPES = {
    # Dialogue flow
    "THINK_CHUNK",          # streaming think block chunk
    "SPEECH_CHUNK",         # streaming speech chunk (typewriter)
    "TRANSLATION_CHUNK",    # streaming translation chunk
    "DELTA_UPDATE",         # finalised stat deltas
    "GAME_OVER",            # ending triggered
    "TTS_AUDIO_URL",        # URL/path to synthesised voice wav

    # State sync
    "STATE_SYNC",           # full state snapshot (on connect / load)
    "STAT_UPDATE",          # live stat bar updates
    "CHAT_APPEND",          # add a complete message to history
    "CHAT_HISTORY",         # full history on load
    "DAY_ADVANCE",          # day counter changed

    # Glitch & FX triggers
    "GLITCH_TRIGGER",       # trigger named glitch effect
    "OVERLAY_SHOW",         # show a procedural overlay
    "OVERLAY_HIDE",         # hide overlay
    "ECG_PARAMS",           # heartbeat waveform params update

    # Agent / takeover
    "AGENT_COMMENTARY",     # VLM agent sends spectator commentary
    "AGENT_TAKEOVER",       # agent takes control (frontend locks input)
    "AGENT_ACTION_EXECUTED",# action result

    # Character customization
    "CUSTOM_CHAR_LIST",     # list of custom character summaries
    "CUSTOM_CHAR_DATA",     # full data for a custom character

    # Launcher
    "API_TEST_RESULT",      # result of API connection test
    "INITIAL_PLOT",         # first plot greeting on game launch

    # System
    "ERROR",                # error message
    "PONG",                 # latency response
    "SLOT_LIST",            # save slot metadata list
    "CONFIG_ACK",           # config update acknowledged
    "CONFIG_SYNC",          # server pushes saved configuration on connect
    "FILE_PICKER_RESULT",   # native file picker result
}


# ── helpers ───────────────────────────────────────────────────────────

def envelope_client(raw: str | bytes) -> ClientMessage:
    """Parse a raw WebSocket text frame into a ClientMessage."""
    data = json.loads(raw)
    t = data.get("type", "")
    if t not in CLIENT_TYPES:
        raise ValueError(f"Unknown client message type: {t}")
    return ClientMessage(type=t, payload=data.get("payload", {}), ts=data.get("ts", 0))


def envelope_server(msg_type: str, **payload) -> str:
    """Build a JSON ServerMessage string."""
    if msg_type not in SERVER_TYPES:
        raise ValueError(f"Unknown server message type: {msg_type}")
    return ServerMessage(type=msg_type, payload=payload).json()
