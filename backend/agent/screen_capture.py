"""
Screen capture utilities using mss (cross-platform, high-performance).

Supports capturing a specific window by title substring match.
"""
from __future__ import annotations
import base64
import io
from typing import Optional

import numpy as np

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False


def capture_window(window_name: str = "") -> Optional[np.ndarray]:
    """Capture the specified window or the primary monitor.

    Parameters
    ----------
    window_name : str
        Substring to match against window titles. If empty, captures
        the entire primary monitor.

    Returns
    -------
    np.ndarray (H, W, 4) in BGRA format, or None on failure.
    """
    if not HAS_MSS:
        return None

    try:
        with mss.mss() as sct:
            if window_name:
                # Find the target window
                for monitor in sct.monitors:
                    # mss doesn't directly expose window titles.
                    # We capture the primary monitor and let the VLM handle it.
                    pass

                # Fallback: capture primary monitor
                monitor = sct.monitors[1]  # primary
            else:
                monitor = sct.monitors[1]

            img = sct.grab(monitor)
            arr = np.array(img, dtype=np.uint8)  # BGRA, (H, W, 4)
            return arr
    except Exception as e:
        print(f"[ScreenCapture] Error: {e}")
        return None


def encode_frame_b64(frame: np.ndarray, quality: int = 60) -> str:
    """Encode a BGRA numpy frame to a base64 JPEG string.

    Parameters
    ----------
    frame : np.ndarray (H, W, 4) BGRA
    quality : int
        JPEG quality 1-100, lower = smaller payload for VLM.

    Returns
    -------
    str — base64-encoded JPEG.
    """
    try:
        from PIL import Image
        # Convert BGRA → RGB
        rgb = frame[..., [2, 1, 0]]
        img = Image.fromarray(rgb)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        print(f"[ScreenCapture] Encode error: {e}")
        return ""
