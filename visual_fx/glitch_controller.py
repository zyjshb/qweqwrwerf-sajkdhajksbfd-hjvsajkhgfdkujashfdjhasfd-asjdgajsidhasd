# -*- coding: utf-8 -*-
"""
GlitchController -- central dispatcher for horror/glitch visual effects.

Selects and triggers glitch effects based on Saki's current suspicion
rating and other game-state signals. Delegates all actual effect work
to EffectsSystem.
"""

import random


class GlitchController:
    """Manages and dispatches all glitch/horror visual effects.

    Uses the app's EffectsSystem instance for actual rendering and
    bases its trigger decisions on game state (suspicion, etc.).
    """

    def __init__(self, app):
        self.app = app

    @property
    def _fx(self):
        """Lazy access to the EffectsSystem attached to the app."""
        return self.app._effects_system

    @property
    def _state(self):
        return self.app.state

    # ------------------------------------------------------------------
    # Central dispatcher
    # ------------------------------------------------------------------

    def trigger_glitch_effect(self, level=None):
        """Choose and dispatch glitch effects based on suspicion level.

        Parameters
        ----------
        level : int or None
            0 = none, 1 = mild, 2 = severe.
            If None, auto-detect from current suspicion.
        """
        if self._state.game_over:
            return

        susp = self._state.suspicion
        if level is None:
            if susp < 40:
                level = 0
            elif susp < 70:
                level = 1
            else:
                level = 2

        if level == 0:
            self.app.glitch_rune_active = False
            self.app.glitch_font_shake_active = False
            return

        # Map of (id, callable) pairs for all 30+ glitch effects
        all_glitches = [
            (1, lambda: setattr(self.app, "glitch_font_shake_active", True)),
            (2, self._fx.glitch_chat_shake),
            (3, self._fx.glitch_ghost_text),
            (4, self._fx.glitch_evaporate),
            (5, self._fx.glitch_speed_shift),
            (6, self._fx.glitch_blood_pulse),
            (7, self._fx.glitch_invert_colors),
            (8, self._fx.glitch_widget_melt_frame),
            (9, self._fx.glitch_heavy_earthquake),
            (10, self._fx.glitch_title_corruption),
            (11, self._fx.glitch_force_topmost),
            (12, self._fx.glitch_dripping_blood),
            (13, self._fx.glitch_flatline),
            (14, self._fx.glitch_scanlines),
            (15, self._fx.glitch_snow_noise),
            (16, self._fx.glitch_subliminal_popup),
            (17, self._fx.glitch_chat_shake),
            (18, self._fx.glitch_mouse_attract),
            (19, self._fx.glitch_suffocation),
            (20, self._fx.glitch_dialogue_overlap),
            (21, self._fx.glitch_day_loop),
            (22, self._fx.glitch_blood_overlay),
            (23, self._fx.glitch_vignette_squeeze),
            (24, self._fx.glitch_scanline_crt),
            (25, self._fx.glitch_static_burst),
            (26, self._fx.glitch_chromatic_tear),
            (27, self._fx.glitch_blood_drips),
            (28, self._fx.glitch_scream_radial),
            (29, self._fx.glitch_dungeon_grid),
            (30, self._fx.glitch_corruption_blocks),
        ]

        if level == 1:
            candidates = [g for g in all_glitches if g[0] in [
                1, 2, 3, 4, 5, 12, 13, 14, 15,
                23, 24, 25, 26, 29,
            ]]
            to_trigger = random.sample(candidates, k=random.randint(1, 3))
            for item in to_trigger:
                try:
                    item[1]()
                except Exception as e:
                    print(f"[Glitch Error] {e}")
        elif level == 2:
            to_trigger = random.sample(all_glitches, k=random.randint(5, 8))
            for item in to_trigger:
                try:
                    item[1]()
                except Exception as e:
                    print(f"[Glitch Error] {e}")

    # ------------------------------------------------------------------
    # High-level effect triggers (used by main_window event dispatch)
    # ------------------------------------------------------------------

    def psychic_strobe(self, duration_ms=300, silent_ms=1300):
        self._fx.psychic_strobe(duration_ms, silent_ms)

    def obsessive_barrage(self, duration_sec=1.0):
        self._fx.obsessive_barrage(duration_sec)

    def melt_overlay(self, duration_ms=1200):
        self._fx.melt_overlay(duration_ms)

    def mouse_tremor(self, duration_ms=1500):
        self._fx.mouse_tremor(duration_ms)

    def fake_error_popup(self):
        self._fx.fake_error_popup()

    def widget_meltdown(self, duration_sec=1.5):
        self._fx.widget_meltdown(duration_sec)

    def mouse_magnetic_pull(self, duration_sec=1.5):
        self._fx.mouse_magnetic_pull(duration_sec)

    def physical_shake(self, range_px=12):
        self._fx.physical_shake(range_px)

    def render_overlapping_text(self, text):
        self._fx.render_overlapping_text(text)

    def carnage_burst(self):
        self._fx.carnage_burst()
