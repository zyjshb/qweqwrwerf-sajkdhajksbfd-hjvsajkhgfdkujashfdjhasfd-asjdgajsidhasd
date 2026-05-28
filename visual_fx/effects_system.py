# -*- coding: utf-8 -*-
"""
EffectsSystem -- Tkinter-based horror/glitch visual disturbances.

Manages mouse warping, window shakes, color strobes, widget melting,
carnage text overlays, and all psychological horror effects. Fully
event-paced to prevent CPU bottlenecks.

All methods operate safely on the main thread via the app reference.
"""

import random
import time
import threading
import tkinter as tk

from visual_fx.procedural_pillow import ProceduralFX
from visual_fx.overlay_manager import get_widget_size


# ---------------------------------------------------------------------------
# Font helpers (mirror main_window cross-platform fallback logic)
# ---------------------------------------------------------------------------

_FONT_CJK = (
    "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei",
    "SimHei", "sans-serif",
)
_FONT_UI = (
    "Microsoft YaHei", "Noto Sans CJK SC", "sans-serif",
)


def _fcjk(size, bold=False):
    from tkinter import font as _tkfont
    families = set(_tkfont.families())
    for name in _FONT_CJK:
        if name in families:
            return (name, size, "bold" if bold else "normal")
    return ("sans-serif", size, "bold" if bold else "normal")


def _fui(size, bold=False):
    from tkinter import font as _tkfont
    families = set(_tkfont.families())
    for name in _FONT_UI:
        if name in families:
            return (name, size, "bold" if bold else "normal")
    return ("sans-serif", size, "bold" if bold else "normal")


def _glitch_text(lang, key):
    """Safe wrapper around resources.game_constants.glitch_text."""
    try:
        from resources.game_constants import glitch_text
        return glitch_text(lang, key)
    except Exception:
        _fallbacks = {
            "barrage": ["看着我", "你是我的", "ERROR"],
            "ghost": "看着我看着我看着我",
            "titles": ["看着我！", "别丢下我！"],
            "popup": ["看着我", "你是我的"],
            "suffocation": "👁️ 👁️\n\n看着我！",
            "overlap": "看着我看着我看着我",
            "prefix": "纱希: ",
        }
        return _fallbacks.get(key, ["ERROR"])


# ============================================================================
# EffectsSystem
# ============================================================================


class EffectsSystem:
    """Central manager for all Tkinter-based horror/glitch visual effects.

    Parameters
    ----------
    app : MainWindow
        Reference to the main application instance for accessing root,
        game_state, ui_queue, overlay_mgr, sound_mgr, etc.
    """

    def __init__(self, app):
        self.app = app

    # -- helpers --------------------------------------------------------------

    @property
    def _root(self):
        return self.app.root

    @property
    def _state(self):
        return self.app.state

    @property
    def _ui_queue(self):
        return self.app.ui_queue

    @property
    def _overlay(self):
        return self.app.overlay_mgr

    @property
    def _sound(self):
        return self.app.sound_mgr

    @property
    def _lang(self):
        from resources.game_constants import normalize_language
        return normalize_language(self.app.selected_language.get())

    def _queue(self, action, data=None, cycle_id=None):
        self.app._queue_ui(action, data, cycle_id)

    def _safe_destroy(self, widget):
        try:
            widget.destroy()
        except Exception:
            pass

    # ========================================================================
    # Psychic Strobe
    # ========================================================================

    def psychic_strobe(self, duration_ms=300, silent_ms=1300):
        self.app.psychic_strobe_active = True
        self._state.ecg_frenzy = True
        self._state.scanlines_active = True

        steps = 4
        cycle_id = self._state.cycle_id

        def revert():
            try:
                self._root.config(bg="#000000")
                self.app.chat_text.config(bg="#000000")
                self.app.chat_frame.config(bg="#000000")
                self.app.bottom_frame.config(bg="#000000")
                self.app.status_bar.config(bg="#0D0000")
                self.app.stats_frame.config(bg="#0D0000")
                self.app.canvas_ecg.config(bg="#000000")
            except Exception:
                pass

        def do_jolt():
            if cycle_id != self._state.cycle_id:
                return
            self.physical_shake(range_px=25)
            try:
                w, h = get_widget_size(self._root)
                tear = ProceduralFX.screen_tear(w, h, num_tears=8)
                self._overlay.show(tear, duration_ms=250)
            except Exception as e:
                print(f"[CRT Jolt Error] {e}")

        def do_strobe(step=0):
            if cycle_id != self._state.cycle_id or not self.app.psychic_strobe_active:
                self.app.psychic_strobe_active = False
                self._state.ecg_frenzy = False
                self._state.scanlines_active = False
                revert()
                return
            if step >= steps:
                self.app.psychic_strobe_active = False
                self._state.ecg_frenzy = False
                self._state.scanlines_active = False
                revert()
                self._root.after(silent_ms, do_jolt)
                return

            color = "#FF0000" if step % 2 == 0 else "#000000"
            try:
                self._root.config(bg=color)
                self.app.chat_text.config(bg=color)
                self.app.chat_frame.config(bg=color)
                self.app.bottom_frame.config(bg=color)
                self.app.status_bar.config(bg=color)
                self.app.stats_frame.config(bg=color)
                self.app.canvas_ecg.config(bg=color)
            except Exception:
                pass
            self._root.after(60, lambda: do_strobe(step + 1))

        do_strobe()

    # ========================================================================
    # Obsessive Barrage
    # ========================================================================

    def obsessive_barrage(self, duration_sec=1.0):
        if hasattr(self.app, "_flood_canvas_ref") and self.app._flood_canvas_ref is not None:
            self._safe_destroy(self.app._flood_canvas_ref)
            self.app._flood_canvas_ref = None

        self.app.barrage_active = True
        w_width, w_height = get_widget_size(self._root)

        flood = tk.Canvas(self._root, bg="#000000", highlightthickness=0, bd=0)
        self.app._flood_canvas_ref = flood
        flood.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            flood.tkraise()
        except Exception:
            pass

        def cleanup():
            self._safe_destroy(flood)
            self.app.barrage_active = False
            if hasattr(self.app, "_flood_canvas_ref") and self.app._flood_canvas_ref is flood:
                self.app._flood_canvas_ref = None

        try:
            flood.create_rectangle(0, 0, w_width, w_height, fill="#050000", outline="")
            words = _glitch_text(self._lang, "barrage")
            if not words:
                words = ["看着我", "你是我的", "ERROR", "YOU CANNOT ESCAPE"]

            for _ in range(80):
                rx = random.randint(-40, max(40, w_width - 80))
                ry = random.randint(-20, max(40, w_height))
                size = random.choice([16, 20, 24, 30, 36])
                color = random.choice(["#FF0000", "#D30000", "#B20000", "#9E0000", "#7A0000"])
                word = random.choice(words)
                flood.create_text(
                    rx, ry, text=word, fill=color,
                    font=_fcjk(size, bold=True), anchor=tk.NW,
                )
        except Exception as err:
            print(f"[Barrage Error] {err}")
            cleanup()
            return

        self._root.after(int(duration_sec * 1000), cleanup)

    # ========================================================================
    # Melt Overlay
    # ========================================================================

    def melt_overlay(self, duration_ms=1200):
        try:
            w, h = get_widget_size(self._root)
            photo = ProceduralFX.pixel_melt_layer(w, h, intensity=0.6)
            self._overlay.show(photo, duration_ms=duration_ms)
        except Exception as e:
            print(f"[Melt Overlay Error] {e}")

    # ========================================================================
    # Mouse Tremor (35ms pacing per plan spec)
    # ========================================================================

    def mouse_tremor(self, duration_ms=1500):
        if getattr(self.app, "mouse_tremor_active", False):
            return
        self.app.mouse_tremor_active = True
        cycle_id = self._state.cycle_id

        try:
            orig_x = self._root.winfo_pointerx()
            orig_y = self._root.winfo_pointery()
        except Exception:
            self.app.mouse_tremor_active = False
            return

        start_time = time.time()
        duration_sec = duration_ms / 1000.0

        def run():
            if (
                cycle_id != self._state.cycle_id
                or not self.app.mouse_tremor_active
                or (time.time() - start_time) >= duration_sec
            ):
                self.app.mouse_tremor_active = False
                return
            try:
                dx = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])
                dy = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])
                curr_x = self._root.winfo_pointerx()
                curr_y = self._root.winfo_pointery()
                self._root.event_generate(
                    "<Motion>", warp=True,
                    x=curr_x + dx - self._root.winfo_rootx(),
                    y=curr_y + dy - self._root.winfo_rooty(),
                )
                self._root.after(35, run)
            except Exception as e:
                print(f"[Mouse Tremor Error] {e}")
                self.app.mouse_tremor_active = False

        self._root.after(35, run)

    # ========================================================================
    # Fake Error Popup
    # ========================================================================

    def fake_error_popup(self):
        try:
            popup = tk.Toplevel(self._root)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)

            w_w, w_h = get_widget_size(self._root)
            p_w, p_h = 360, 140
            rx = self._root.winfo_rootx() + (w_w - p_w) // 2
            ry = self._root.winfo_rooty() + (w_h - p_h) // 2
            popup.geometry(f"{p_w}x{p_h}+{rx}+{ry}")
            popup.configure(bg="#D4D0C8", bd=2, relief=tk.RAISED)

            title_bar = tk.Frame(popup, bg="#000080", height=22, bd=0)
            title_bar.pack(fill=tk.X, padx=2, pady=2)

            tk.Label(
                title_bar, text="Fatal Error", fg="#FFFFFF", bg="#000080",
                font=_fui(9, bold=True), anchor=tk.W,
            ).pack(side=tk.LEFT, padx=3, pady=1)

            def on_close():
                try:
                    popup.destroy()
                    self.physical_shake(range_px=15)
                    self.psychic_strobe(duration_ms=150, silent_ms=100)
                except Exception:
                    pass

            tk.Button(
                title_bar, text="X", bg="#D4D0C8", fg="#000000",
                activebackground="#D4D0C8", activeforeground="#000000",
                font=_fui(7, bold=True), bd=1, relief=tk.RAISED,
                command=on_close, width=2, height=1,
            ).pack(side=tk.RIGHT, padx=2, pady=1)

            content_frame = tk.Frame(popup, bg="#D4D0C8")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

            icon = tk.Canvas(content_frame, width=36, height=36, bg="#D4D0C8", highlightthickness=0)
            icon.pack(side=tk.LEFT, padx=(0, 10))
            icon.create_oval(3, 3, 33, 33, fill="#FF0000", outline="#800000", width=1)
            icon.create_line(11, 11, 25, 25, fill="#FFFFFF", width=3)
            icon.create_line(25, 11, 11, 25, fill="#FFFFFF", width=3)

            lang = self._lang
            if lang == "日本語":
                msg_text = "Fatal Error: ユーザーが脱走を試みました。\n精神支配を起動中。"
            elif lang == "English":
                msg_text = "Fatal Error: User tried to escape.\nMind control active."
            else:
                msg_text = "Fatal Error: 玩家尝试逃跑。\n精神控制已激活。"

            tk.Label(
                content_frame, text=msg_text, bg="#D4D0C8", fg="#000000",
                font=_fui(9), justify=tk.LEFT, anchor=tk.W,
            ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            btn_frame = tk.Frame(popup, bg="#D4D0C8")
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 12))
            tk.Button(
                btn_frame, text="OK", bg="#D4D0C8", fg="#000000",
                activebackground="#E0E0E0", activeforeground="#000000",
                font=_fui(9), bd=2, relief=tk.RAISED, width=8, command=on_close,
            ).pack(anchor=tk.CENTER)

            self.physical_shake(range_px=10)
        except Exception as e:
            print(f"[Fake Error Popup Error] {e}")

    # ========================================================================
    # Widget Meltdown
    # ========================================================================

    def widget_meltdown(self, duration_sec=1.5):
        self.app.meltdown_active = True
        try:
            orig_padx = self.app.entry_input.pack_info().get("padx", (0, 10))
            orig_pady = self.app.btn_send.pack_info().get("pady", 0)
        except Exception:
            orig_padx = (0, 10)
            orig_pady = 0

        def do_melt(step=0):
            if step >= int(duration_sec / 0.035) or not self.app.meltdown_active:
                self.app.meltdown_active = False
                try:
                    self.app.entry_input.pack_configure(padx=orig_padx, pady=0)
                    self.app.btn_send.pack_configure(padx=0, pady=orig_pady)
                except Exception:
                    pass
                return
            dx = random.randint(-15, 15)
            dy = random.randint(-10, 10)
            try:
                self.app.entry_input.pack_configure(
                    padx=(max(0, dx), max(0, 10 - dx)), pady=max(0, dy),
                )
                self.app.btn_send.pack_configure(padx=max(0, -dx), pady=max(0, -dy))
            except Exception:
                pass
            self._root.after(35, lambda: do_melt(step + 1))

        do_melt()

    # ========================================================================
    # Mouse Magnetic Pull (60ms pacing per plan spec)
    # ========================================================================

    def mouse_magnetic_pull(self, duration_sec=1.5):
        self.app.mouse_pull_active = True
        steps = int(duration_sec / 0.06)

        def do_pull(step=0):
            if step >= steps or not self.app.mouse_pull_active:
                self.app.mouse_pull_active = False
                return
            try:
                cx = self._root.winfo_x() + self._root.winfo_width() // 2
                cy = self._root.winfo_y() + self._root.winfo_height() // 2
                cur_x = self._root.winfo_pointerx()
                cur_y = self._root.winfo_pointery()
                nx = int(cur_x + (cx - cur_x) * 0.15 + random.randint(-8, 8))
                ny = int(cur_y + (cy - cur_y) * 0.15 + random.randint(-8, 8))
                self._root.event_generate(
                    "<Motion>", warp=True,
                    x=nx - self._root.winfo_x(),
                    y=ny - self._root.winfo_y(),
                )
                self._root.after(60, lambda: do_pull(step + 1))
            except Exception as e:
                print(f"[Mouse Pull Error] {e}")
                self.app.mouse_pull_active = False

        do_pull()

    # ========================================================================
    # Carnage / Overlapping Text
    # ========================================================================

    def render_overlapping_text(self, text):
        if not text:
            return
        if not hasattr(self.app, "carnage_labels"):
            self.app.carnage_labels = []

        # Write legible spoken text in chat log
        self.app.chat_text.config(state=tk.NORMAL)
        prefix = _glitch_text(self._lang, "prefix")
        self.app.chat_text.insert(tk.END, f"{prefix}█▄ {text} ▆▇█\n", "saki")
        self.app.chat_text.config(state=tk.DISABLED)
        self.app.chat_text.see(tk.END)

        words = list(text)
        chunks = []
        i = 0
        while i < len(words):
            chunk_len = random.randint(2, 5)
            chunks.append("".join(words[i:i + chunk_len]))
            i += chunk_len

        runes = ["☠", "♥", "🔪", "⛓", "🖤", "❤", "♦", "✝", "☆", "◆"]
        for idx in range(len(chunks)):
            if random.random() < 0.25:
                chunks[idx] = random.choice(runes) + chunks[idx] + random.choice(runes)

        target_count = 55
        if len(chunks) > target_count:
            chunks = random.sample(chunks, target_count)
        elif len(chunks) > 0:
            while len(chunks) < target_count:
                chunks.extend(random.sample(chunks, min(len(chunks), target_count - len(chunks))))

        w_width = self.app.chat_text.winfo_width()
        w_height = self.app.chat_text.winfo_height()
        if w_width <= 100:
            w_width = 900
        if w_height <= 100:
            w_height = 500

        current_labels = []
        for chunk in chunks:
            rx = random.randint(10, max(20, w_width - 300))
            ry = random.randint(10, max(20, w_height - 80))
            font_size = random.choice([14, 18, 22, 26])
            if random.random() < 0.15:
                font_size = 34

            lbl = tk.Label(
                self.app.chat_text, text=chunk,
                fg="#FF0000", bg="#000000",
                font=_fcjk(font_size, bold=True), bd=0, highlightthickness=0,
            )
            lbl.place(x=rx, y=ry)
            self.app.carnage_labels.append(lbl)
            current_labels.append(lbl)

        def auto_decay():
            for lbl in current_labels:
                try:
                    if lbl.winfo_exists():
                        lbl.destroy()
                        if lbl in self.app.carnage_labels:
                            self.app.carnage_labels.remove(lbl)
                except Exception:
                    pass

        self._root.after(2500, auto_decay)

    # ========================================================================
    # Physical Window Shake
    # ========================================================================

    def physical_shake(self, range_px=12):
        if getattr(self._state, "shaking", False):
            return

        self._state.shaking = True
        self.afterimage_shake_overlay(duration_ms=300)

        orig_x = self._root.winfo_x()
        orig_y = self._root.winfo_y()

        def worker(ox, oy):
            try:
                steps = 22
                for _ in range(steps):
                    dx = random.randint(-range_px, range_px)
                    dy = random.randint(-range_px, range_px)
                    self._queue("TRIGGER_MOVE", (ox + dx, oy + dy))
                    time.sleep(0.025)
                self._queue("TRIGGER_MOVE", (ox, oy))
            except Exception as e:
                print(f"[shake error] {e}")
            finally:
                self._state.shaking = False

        threading.Thread(target=worker, args=(orig_x, orig_y), daemon=True).start()

    def afterimage_shake_overlay(self, duration_ms=200):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.chromatic_aberration(w, h, shift=random.randint(3, 8))
        self._overlay.show(img, duration_ms=duration_ms)

    # ========================================================================
    # Individual Glitch Effects (21+ methods)
    # ========================================================================

    def glitch_ghost_text(self):
        self.app.chat_text.config(state=tk.NORMAL)
        self.app.chat_text.insert(
            tk.END, f"\n{_glitch_text(self._lang, 'ghost')}\n", "glitch_large",
        )
        self.app.chat_text.config(state=tk.DISABLED)
        self.app.chat_text.see(tk.END)

        def remove():
            self.app.chat_text.config(state=tk.NORMAL)
            try:
                self.app.chat_text.delete("end-2l", "end-1c")
            except Exception:
                pass
            self.app.chat_text.config(state=tk.DISABLED)

        self._root.after(120, remove)

    def glitch_evaporate(self):
        self.app.chat_text.config(state=tk.NORMAL)
        length = len(self.app.chat_text.get("1.0", tk.END))
        if length > 50:
            for _ in range(8):
                idx = random.randint(20, length - 5)
                char_pos = f"1.0 + {idx} chars"
                orig = self.app.chat_text.get(char_pos)
                if orig.strip():
                    self.app.chat_text.delete(char_pos)
                    self.app.chat_text.insert(char_pos, " ")

                    def restore(p=char_pos, c=orig):
                        self.app.chat_text.config(state=tk.NORMAL)
                        try:
                            self.app.chat_text.delete(p)
                            self.app.chat_text.insert(p, c)
                        except Exception:
                            pass
                        self.app.chat_text.config(state=tk.DISABLED)

                    self._root.after(150, restore)
        self.app.chat_text.config(state=tk.DISABLED)

    def glitch_speed_shift(self):
        self.app.typewriter_speed_mult = random.choice([0.02, 0.05, 5.0, 10.0])
        self._root.after(1200, lambda: setattr(self.app, "typewriter_speed_mult", 1.0))

    def glitch_blood_pulse(self):
        steps = 15
        delay = 35

        def fade_in(step=0):
            if step > steps:
                fade_out(steps)
                return
            r = int((step / steps) * 74)
            color = f"#{r:02x}0000"
            try:
                self.app.chat_text.config(bg=color)
                self._root.config(bg=color)
                self.app.chat_frame.config(bg=color)
                self.app.bottom_frame.config(bg=color)
                self.app.status_bar.config(bg=color)
                self.app.stats_frame.config(bg=color)
            except Exception:
                pass
            self._root.after(delay, lambda: fade_in(step + 1))

        def fade_out(step=steps):
            if step < 0:
                try:
                    self.app.chat_text.config(bg="#000000")
                    self._root.config(bg="#000000")
                    self.app.chat_frame.config(bg="#000000")
                    self.app.bottom_frame.config(bg="#000000")
                    self.app.status_bar.config(bg="#0D0000")
                    self.app.stats_frame.config(bg="#0D0000")
                except Exception:
                    pass
                return
            r = int((step / steps) * 74)
            color = f"#{r:02x}0000"
            try:
                self.app.chat_text.config(bg=color)
                self._root.config(bg=color)
                self.app.chat_frame.config(bg=color)
                self.app.bottom_frame.config(bg=color)
                self.app.status_bar.config(bg=color)
                self.app.stats_frame.config(bg=color)
            except Exception:
                pass
            self._root.after(delay, lambda: fade_out(step - 1))

        fade_in()

    def glitch_chat_shake(self):
        steps = 15

        def do_shake(step=0):
            if step >= steps:
                try:
                    self.app.chat_text.pack_configure(padx=0, pady=5)
                    self.app.entry_input.pack_configure(padx=(0, 10))
                except Exception:
                    pass
                return
            dx = random.randint(-8, 8)
            dy = random.randint(-4, 4)
            try:
                self.app.chat_text.pack_configure(padx=max(0, dx), pady=max(0, dy) + 5)
                self.app.entry_input.pack_configure(padx=(max(0, dx), 10))
            except Exception:
                pass
            self._root.after(20, lambda: do_shake(step + 1))

        do_shake()

    def glitch_invert_colors(self):
        widgets = [self._root, self.app.chat_text, self.app.entry_input]
        for w in widgets:
            try:
                w.config(bg="#FFFFFF", fg="#000000")
            except Exception:
                pass

        def revert():
            for w in widgets:
                try:
                    w.config(bg="#000000", fg="#FF0000")
                except Exception:
                    pass
            self.app.chat_text.config(fg="#CC0000")

        self._root.after(100, revert)

    def glitch_widget_melt_frame(self):
        frames = [self.app.bottom_frame, self.app.status_bar, self.app.canvas_ecg]
        for f in frames:
            try:
                orig_pady = f.pack_info().get("pady", 0)
                f.pack_configure(pady=random.randint(int(orig_pady) + 2, int(orig_pady) + 12))
                self._root.after(150, lambda tgt=f, py=orig_pady: tgt.pack_configure(pady=py))
            except Exception:
                pass

    def glitch_heavy_earthquake(self):
        self.physical_shake(range_px=25)

    def glitch_title_corruption(self):
        orig_title = self._root.title()
        titles = _glitch_text(self._lang, "titles")

        def cycle(count=0):
            if count >= 8:
                self._root.title(orig_title)
                return
            self._root.title(random.choice(titles))
            self._root.after(80, lambda: cycle(count + 1))

        cycle()

    def glitch_force_topmost(self):
        self._root.attributes("-topmost", True)
        self._root.after(800, lambda: self._root.attributes("-topmost", False))

    def glitch_dripping_blood(self):
        self._state.dripping_blood_active = True
        self._state.dripping_blood_lines = [
            {"x": random.randint(50, 1000), "y": 0, "speed": random.uniform(1.5, 4.0)}
            for _ in range(5)
        ]
        self._root.after(2000, lambda: setattr(self._state, "dripping_blood_active", False))

    def glitch_flatline(self):
        self._state.ecg_flatline_active = True
        self.app.canvas_ecg.config(bg="#3A0000")

        def restore():
            self._state.ecg_flatline_active = False
            self.app.canvas_ecg.config(bg="#000000")

        self._root.after(600, restore)

    def glitch_scanlines(self):
        self._state.scanlines_active = True
        self._root.after(80, lambda: setattr(self._state, "scanlines_active", False))

    def glitch_snow_noise(self):
        self._state.snow_noise_active = True
        self._root.after(100, lambda: setattr(self._state, "snow_noise_active", False))

    def glitch_subliminal_popup(self):
        popup = tk.Toplevel(self._root)
        popup.overrideredirect(True)
        popup.config(bg="#000000")
        popup.attributes("-topmost", True)
        rx = random.randint(100, max(500, self._root.winfo_screenwidth() - 300))
        ry = random.randint(100, max(400, self._root.winfo_screenheight() - 200))
        popup.geometry(f"+{rx}+{ry}")
        texts = _glitch_text(self._lang, "popup")
        tk.Label(
            popup, text=random.choice(texts), fg="#FF0000", bg="#000000",
            font=_fcjk(18, bold=True),
        ).pack(padx=20, pady=10)
        self._root.after(80, lambda: popup.destroy())

    def glitch_fake_error_flag(self):
        self._state.fake_error_active = True
        self._root.after(1000, lambda: setattr(self._state, "fake_error_active", False))

    def glitch_mouse_attract(self):
        cx = self._root.winfo_x() + self._root.winfo_width() // 2
        cy = self._root.winfo_y() + self._root.winfo_height() // 2

        def pull(step=0):
            if step >= 5:
                return
            cur_x = self._root.winfo_pointerx()
            cur_y = self._root.winfo_pointery()
            nx = cur_x + (cx - cur_x) // 5 + random.randint(-5, 5)
            ny = cur_y + (cy - cur_y) // 5 + random.randint(-5, 5)
            self._root.event_generate(
                "<Motion>", warp=True,
                x=nx - self._root.winfo_x(),
                y=ny - self._root.winfo_y(),
            )
            self._root.after(40, lambda: pull(step + 1))

        pull()

    def glitch_suffocation(self):
        frame = tk.Frame(self._root, bg="#000000")
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        frame.lift()
        tk.Label(
            frame, text=_glitch_text(self._lang, "suffocation"),
            fg="#FF0000", bg="#000000", font=_fcjk(24, bold=True),
        ).pack(expand=True)
        self._root.after(300, lambda: frame.destroy())

    def glitch_dialogue_overlap(self):
        self.app.chat_text.config(state=tk.NORMAL)
        self.app.chat_text.insert(
            tk.END, _glitch_text(self._lang, "overlap"), "glitch_large",
        )
        self.app.chat_text.config(state=tk.DISABLED)

    def glitch_day_loop(self):
        from resources.localization import LOCALIZATION
        from resources.game_constants import normalize_language

        def shift(count=0):
            lang = normalize_language(self._lang)
            if count >= 12:
                self.app.lbl_day.config(
                    text=LOCALIZATION[lang]["day"].format(day=self._state.current_day),
                )
                return
            self.app.lbl_day.config(
                text=LOCALIZATION[lang]["day"].format(day=random.randint(1, 99)),
            )
            self._root.after(50, lambda: shift(count + 1))

        shift()

    # -- Procedural-Pillow overlay glitch effects (22-30) --

    def glitch_blood_overlay(self):
        w, h = get_widget_size(self._root)
        intensity = 0.3 + 0.7 * (self._state.suspicion / 100.0)
        img = ProceduralFX.blood_splatter(w, h, drops=int(30 + intensity * 50), intensity=intensity)
        self._overlay.show(img, duration_ms=random.randint(300, 800))

    def glitch_vignette_squeeze(self):
        w, h = get_widget_size(self._root)
        darkness = 0.35 + 0.45 * (self._state.suspicion / 100.0)
        img = ProceduralFX.vignette(w, h, darkness=darkness)
        self._overlay.show(img, duration_ms=random.randint(600, 1500))

    def glitch_scanline_crt(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.scanlines(w, h, spacing=random.choice([2, 3, 4]), opacity=0.12)
        self._overlay.show(img, duration_ms=random.randint(80, 250))

    def glitch_static_burst(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.static_noise(w, h, intensity=0.2 + random.uniform(0, 0.3))
        self._overlay.show(img, duration_ms=random.randint(60, 200))

    def glitch_chromatic_tear(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.chromatic_aberration(w, h, shift=random.randint(3, 10))
        self._overlay.show(img, duration_ms=random.randint(100, 400))

    def glitch_blood_drips(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.blood_drip_streak(w, h, count=random.randint(3, 10))
        self._overlay.show(img, duration_ms=random.randint(400, 1200))

    def glitch_scream_radial(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.scream_lines(w, h, count=random.randint(15, 40))
        self._overlay.show(img, duration_ms=random.randint(200, 600))

    def glitch_dungeon_grid(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.cell_shade(w, h, grid=random.choice([30, 50, 80]))
        self._overlay.show(img, duration_ms=random.randint(300, 900))

    def glitch_corruption_blocks(self):
        w, h = get_widget_size(self._root)
        img = ProceduralFX.glitch_block(w, h, blocks=random.randint(4, 15))
        self._overlay.show(img, duration_ms=random.randint(100, 500))

    # ========================================================================
    # Combined Carnage Burst (triggers multiple effects at once)
    # ========================================================================

    def carnage_burst(self):
        """Trigger a full suite of horror effects simultaneously."""
        self.psychic_strobe(300, 1300)
        self.obsessive_barrage(1.0)
        self.melt_overlay(1200)
        self.mouse_tremor(1500)
        self.fake_error_popup()
        self.widget_meltdown(1.5)
        self.mouse_magnetic_pull(1.5)
        self.physical_shake(12)
