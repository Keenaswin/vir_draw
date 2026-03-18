"""
utils.py — Helper Functions & UI Constants
Defines the toolbar layout, color palette, and drawing utilities.
"""

import cv2
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# UI / Layout constants
# ──────────────────────────────────────────────────────────────────────────────

TOOLBAR_HEIGHT = 80          # pixels reserved for the top toolbar
TOOLBAR_BG     = (30, 30, 30)    # near-black background for toolbar

# Brush thickness options (pixels)
BRUSH_SIZES    = [5, 10, 18, 28]
ERASER_SIZE    = 50

# ──────────────────────────────────────────────────────────────────────────────
# Color palette
# ──────────────────────────────────────────────────────────────────────────────

COLORS = {
    "Red"   : (0,   0,   220),
    "Blue"  : (220, 80,  20),
    "Green" : (20,  200, 50),
    "Yellow": (0,   220, 220),
    "White" : (255, 255, 255),
    "Purple": (200, 50,  180),
    "Orange": (0,   140, 255),
    "Cyan"  : (220, 200, 0),
}

# ──────────────────────────────────────────────────────────────────────────────
# Toolbar button definitions
# ──────────────────────────────────────────────────────────────────────────────
# Each button is a dict with keys:
#   label    : display text / emoji
#   x1, y1   : top-left corner
#   x2, y2   : bottom-right corner
#   action   : string identifier handled in main.py
#   color    : BGR fill color (for color buttons) or None
#   bg_color : background colour of the button itself

def build_toolbar(frame_width):
    """
    Dynamically build toolbar button positions based on the frame width.
    Returns a list of button dicts.
    """
    buttons = []
    pad     = 8        # padding around buttons
    btn_h   = TOOLBAR_HEIGHT - 2 * pad
    x       = pad

    # ── Color swatches ────────────────────────────────────────────────────────
    swatch_w = 48
    for name, bgr in COLORS.items():
        buttons.append({
            "label"   : "",
            "x1"      : x,
            "y1"      : pad,
            "x2"      : x + swatch_w,
            "y2"      : pad + btn_h,
            "action"  : f"color:{name}",
            "color"   : bgr,
            "bg_color": bgr,
        })
        x += swatch_w + 4

    x += 10   # spacer

    # ── Brush size buttons ────────────────────────────────────────────────────
    for size in BRUSH_SIZES:
        buttons.append({
            "label"   : f"{size}",
            "x1"      : x,
            "y1"      : pad,
            "x2"      : x + 42,
            "y2"      : pad + btn_h,
            "action"  : f"brush:{size}",
            "color"   : None,
            "bg_color": (70, 70, 70),
        })
        x += 46

    x += 10   # spacer

    # ── Eraser ────────────────────────────────────────────────────────────────
    buttons.append({
        "label"   : "Eraser",
        "x1"      : x,
        "y1"      : pad,
        "x2"      : x + 70,
        "y2"      : pad + btn_h,
        "action"  : "eraser",
        "color"   : None,
        "bg_color": (60, 60, 90),
    })
    x += 74

    # ── Clear ─────────────────────────────────────────────────────────────────
    buttons.append({
        "label"   : "Clear",
        "x1"      : x,
        "y1"      : pad,
        "x2"      : x + 65,
        "y2"      : pad + btn_h,
        "action"  : "clear",
        "color"   : None,
        "bg_color": (40, 40, 120),
    })
    x += 69

    # ── Save ──────────────────────────────────────────────────────────────────
    buttons.append({
        "label"   : "Save",
        "x1"      : x,
        "y1"      : pad,
        "x2"      : x + 60,
        "y2"      : pad + btn_h,
        "action"  : "save",
        "color"   : None,
        "bg_color": (30, 100, 50),
    })

    return buttons


# ──────────────────────────────────────────────────────────────────────────────
# Drawing helpers
# ──────────────────────────────────────────────────────────────────────────────

def draw_toolbar(frame, buttons, active_color, active_size, active_tool):
    """
    Render the toolbar onto the top portion of *frame* (in-place).
    Highlights the currently selected color swatch and brush size.
    """
    # Background strip
    cv2.rectangle(frame, (0, 0), (frame.shape[1], TOOLBAR_HEIGHT),
                  TOOLBAR_BG, -1)

    for btn in buttons:
        x1, y1, x2, y2 = btn["x1"], btn["y1"], btn["x2"], btn["y2"]
        bg = btn["bg_color"]

        # Highlight active swatch
        is_active = False
        if btn["action"].startswith("color:"):
            bname = btn["action"].split(":")[1]
            if COLORS[bname] == active_color and active_tool == "brush":
                is_active = True
        elif btn["action"].startswith("brush:"):
            bsize = int(btn["action"].split(":")[1])
            if bsize == active_size:
                is_active = True
        elif btn["action"] == "eraser" and active_tool == "eraser":
            is_active = True

        cv2.rectangle(frame, (x1, y1), (x2, y2), bg, -1)

        # Highlight border
        border_col = (255, 255, 255) if is_active else (100, 100, 100)
        border_th  = 3 if is_active else 1
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_col, border_th)

        # Label text
        if btn["label"]:
            font_scale = 0.45
            thickness  = 1
            text       = btn["label"]
            tw, th     = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX,
                                          font_scale, thickness)[0]
            tx = x1 + (x2 - x1 - tw) // 2
            ty = y1 + (y2 - y1 + th) // 2 - 2
            cv2.putText(frame, text, (tx, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        (230, 230, 230), thickness, cv2.LINE_AA)

    return frame


def draw_status_bar(frame, mode, color, size, tool, fps):
    """
    Draw a thin status line at the very bottom of *frame*.
    """
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 24), (w, h), (20, 20, 20), -1)

    mode_text = f"Mode: {mode}  |  Tool: {tool}  |  Size: {size}  |  FPS: {fps:.0f}"
    cv2.putText(frame, mode_text, (10, h - 7),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

    # Small color preview square
    cv2.rectangle(frame, (w - 30, h - 20), (w - 8, h - 4), color, -1)
    cv2.rectangle(frame, (w - 30, h - 20), (w - 8, h - 4), (150, 150, 150), 1)


def point_in_button(px, py, btn):
    """Return True if pixel (px, py) lies inside the button rectangle."""
    return btn["x1"] <= px <= btn["x2"] and btn["y1"] <= py <= btn["y2"]


def smooth_point(prev, curr, alpha=0.5):
    """
    Exponential moving average between two (x,y) points.
    alpha=1.0 → no smoothing; alpha→0 → very smooth (laggy).
    """
    if prev is None:
        return curr
    return (
        int(alpha * curr[0] + (1 - alpha) * prev[0]),
        int(alpha * curr[1] + (1 - alpha) * prev[1]),
    )


def create_canvas(height, width):
    """Return a blank (all-zero / transparent) BGRA canvas."""
    return np.zeros((height, width, 4), dtype=np.uint8)


def overlay_canvas(frame, canvas):
    """
    Blend the BGRA canvas onto a BGR frame using the alpha channel.
    Returns the composited BGR frame.
    """
    # Extract alpha mask from canvas
    alpha = canvas[:, :, 3:4].astype(np.float32) / 255.0
    fg    = canvas[:, :, :3].astype(np.float32)
    bg    = frame.astype(np.float32)

    composited = (fg * alpha + bg * (1.0 - alpha)).astype(np.uint8)
    return composited
