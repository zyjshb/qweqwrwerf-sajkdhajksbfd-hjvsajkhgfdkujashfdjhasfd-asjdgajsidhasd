# -*- coding: utf-8 -*-
"""
===============================================================================
  visual_fx package -- Procedural visual effects for Saki yandere game.
  Provides runtime-generated textures, particle engines, overlay management,
  and glitch controllers. Zero external image assets required.
===============================================================================
"""

from .procedural_pillow import ProceduralFX
from .particle_engine import ParticleEngine
from .overlay_manager import OverlayManager, get_widget_size
from .effects_system import EffectsSystem
from .glitch_controller import GlitchController

__all__ = [
    "ProceduralFX", "ParticleEngine", "OverlayManager",
    "EffectsSystem", "GlitchController", "get_widget_size",
]
