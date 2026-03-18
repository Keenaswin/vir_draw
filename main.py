"""
main.py — Virtual AI Painter
─────────────────────────────────────────────────────────────────────────────
Draw in mid-air using your index finger!

Controls (gestures):
  • Index finger UP only      → Drawing mode  (draws on canvas)
  • Index + Middle finger UP  → Selection mode (interact with toolbar)
  • All fingers closed        → Pause / lift pen

Keyboard shortcuts:
  Q / ESC  → Quit
  C        → Clear canvas
  S        → Save drawing as PNG
─────────────────────────────────────────────────────────────────────────────
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime

from hand_tracker import HandTracker
from utils import (
    TOOLBAR_HEIGHT, BRUSH_SIZES, ERASER_SIZE, COLORS,
    build_toolbar, draw_toolbar, draw_status_bar,
    point_in_button, smooth_point, create_canvas, overlay_canvas
)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

CAMERA_INDEX   = 0       # change to 1, 2 … if your webcam isn't index 0
FRAME_WIDTH    = 1280
FRAME_HEIGHT   = 720
SMOOTHING      = 0.55    # 0.0 = very smooth / laggy; 1.0 = raw / precise

# Minimum pixel distance the finger must travel to register a stroke
MIN_MOVE_DIST  = 3

# How long (seconds) the finger must hover over a toolbar button to trigger it
HOVER_DELAY    = 0.6


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5


def save_drawing(canvas, frame):
    """Flatten canvas onto a white background and save as PNG."""
    os.makedirs("saved_drawings", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"saved_drawings/drawing_{ts}.png"

    # White background
    bg   = np.ones((canvas.shape[0], canvas.shape[1], 3), dtype=np.uint8) * 255
    comp = overlay_canvas(bg, canvas)
    cv2.imwrite(path, comp)
    print(f"[Saved] {path}")
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Main application
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # ── Camera setup ─────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Use actual captured resolution (may differ from requested)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera] Resolution: {actual_w}×{actual_h}")

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check CAMERA_INDEX in main.py.")
        return

    # ── Hand tracker ─────────────────────────────────────────────────────────
    tracker = HandTracker(max_hands=1,
                          detection_confidence=0.75,
                          tracking_confidence=0.75)

    # ── Toolbar ───────────────────────────────────────────────────────────────
    buttons = build_toolbar(actual_w)

    # ── Drawing state ─────────────────────────────────────────────────────────
    canvas         = create_canvas(actual_h, actual_w)   # BGRA
    active_color   = COLORS["Red"]
    active_size    = BRUSH_SIZES[1]                       # default 10 px
    active_tool    = "brush"                              # "brush" | "eraser"
    prev_point     = None
    smooth_prev    = None
    mode           = "idle"                               # drawing | selection | idle

    # Hover tracking (for toolbar activation without clicking)
    hover_btn      = None
    hover_start    = 0.0

    # FPS tracking
    fps_timer      = time.time()
    fps            = 0
    frame_count    = 0

    # Brief on-screen notification
    notification   = ""
    notify_until   = 0.0

    print("[Ready] Show your hand to the webcam and start painting!")
    print("        Index finger UP       → draw")
    print("        Index + Middle UP     → select toolbar")
    print("        Q / ESC              → quit")
    print("        S                    → save   C → clear")

    # ─────────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame from webcam.")
            break

        # Mirror the frame so movement feels natural
        frame = cv2.flip(frame, 1)

        # ── Hand detection ───────────────────────────────────────────────────
        frame   = tracker.find_hands(frame, draw=True)
        tracker.get_landmark_positions(frame)

        # ── Gesture classification ───────────────────────────────────────────
        drawing_gesture   = tracker.is_drawing_gesture()
        selection_gesture = tracker.is_selection_gesture()

        index_tip  = tracker.get_index_finger_tip()
        middle_tip = tracker.get_middle_finger_tip()

        if drawing_gesture:
            mode = "drawing"
        elif selection_gesture:
            mode = "selection"
        else:
            mode = "idle"
            prev_point  = None
            smooth_prev = None

        # ── Selection mode: toolbar interaction ──────────────────────────────
        if mode == "selection" and index_tip:
            ix, iy = index_tip

            # Draw a circle at the selection cursor
            cv2.circle(frame, (ix, iy), 12, (255, 255, 255), 2)

            # Check if hovering over a button
            hovered = None
            for btn in buttons:
                if point_in_button(ix, iy, btn):
                    hovered = btn
                    break

            if hovered:
                if hovered is not hover_btn:
                    # New button hovered — reset timer
                    hover_btn   = hovered
                    hover_start = time.time()
                else:
                    # Same button — check dwell time
                    elapsed = time.time() - hover_start
                    # Draw progress arc
                    progress = min(elapsed / HOVER_DELAY, 1.0)
                    cx = (hovered["x1"] + hovered["x2"]) // 2
                    cy = (hovered["y1"] + hovered["y2"]) // 2
                    angle = int(360 * progress)
                    cv2.ellipse(frame, (cx, cy), (20, 20), -90,
                                0, angle, (0, 200, 255), 3)

                    if elapsed >= HOVER_DELAY:
                        # ── Execute action ───────────────────────────────
                        action = hovered["action"]

                        if action.startswith("color:"):
                            cname        = action.split(":")[1]
                            active_color = COLORS[cname]
                            active_tool  = "brush"
                            notification = f"Color: {cname}"

                        elif action.startswith("brush:"):
                            active_size  = int(action.split(":")[1])
                            active_tool  = "brush"
                            notification = f"Brush size: {active_size}"

                        elif action == "eraser":
                            active_tool  = "eraser"
                            notification = "Eraser ON"

                        elif action == "clear":
                            canvas       = create_canvas(actual_h, actual_w)
                            notification = "Canvas cleared!"

                        elif action == "save":
                            path         = save_drawing(canvas, frame)
                            notification = f"Saved!"

                        notify_until = time.time() + 1.5
                        hover_btn    = None   # reset so it doesn't fire again
            else:
                hover_btn = None

        # ── Drawing mode ─────────────────────────────────────────────────────
        if mode == "drawing" and index_tip is not None:
            ix, iy = index_tip

            # Apply smoothing
            smooth_curr = smooth_point(smooth_prev, (ix, iy), SMOOTHING)
            smooth_prev = smooth_curr

            # Only draw if we have a previous point AND have moved enough
            if prev_point and dist(prev_point, smooth_curr) > MIN_MOVE_DIST:
                if active_tool == "brush":
                    color_bgra = (*active_color, 255)   # fully opaque
                    cv2.line(canvas, prev_point, smooth_curr,
                             color_bgra, active_size, cv2.LINE_AA)
                else:
                    # Eraser: set alpha to 0 (transparent)
                    cv2.circle(canvas, smooth_curr, ERASER_SIZE, (0,0,0,0), -1)
            prev_point = smooth_curr

            # Visual feedback dot on fingertip
            tip_color = active_color if active_tool == "brush" else (200, 200, 200)
            sz        = active_size if active_tool == "brush" else ERASER_SIZE // 2
            cv2.circle(frame, smooth_curr, sz // 2 + 2, tip_color, -1)

        else:
            prev_point  = None
            smooth_prev = None

        # ── Composite canvas onto frame ───────────────────────────────────────
        frame = overlay_canvas(frame, canvas)

        # ── Draw toolbar ──────────────────────────────────────────────────────
        draw_toolbar(frame, buttons, active_color, active_size, active_tool)

        # ── Mode label ────────────────────────────────────────────────────────
        mode_colors = {
            "drawing"  : (0, 220, 100),
            "selection": (0, 180, 255),
            "idle"     : (120, 120, 120),
        }
        mode_label = {
            "drawing"  : "✏  DRAWING",
            "selection": "☝  SELECTION",
            "idle"     : "  IDLE",
        }
        cv2.putText(frame, mode_label[mode],
                    (10, TOOLBAR_HEIGHT + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    mode_colors[mode], 2, cv2.LINE_AA)

        # ── Notification banner ───────────────────────────────────────────────
        if notification and time.time() < notify_until:
            nw, nh = cv2.getTextSize(notification,
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            nx = (actual_w - nw) // 2
            ny = TOOLBAR_HEIGHT + 55
            cv2.rectangle(frame, (nx - 10, ny - 22),
                          (nx + nw + 10, ny + 8), (20, 20, 20), -1)
            cv2.putText(frame, notification, (nx, ny),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 220, 255), 2, cv2.LINE_AA)

        # ── FPS counter ───────────────────────────────────────────────────────
        frame_count += 1
        now = time.time()
        if now - fps_timer >= 0.5:
            fps       = frame_count / (now - fps_timer)
            fps_timer = now
            frame_count = 0

        draw_status_bar(frame, mode, active_color, active_size, active_tool, fps)

        # ── Display ───────────────────────────────────────────────────────────
        cv2.imshow("Virtual AI Painter  —  Q to quit", frame)

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):          # Q or ESC → quit
            break
        elif key == ord('c'):              # C → clear
            canvas       = create_canvas(actual_h, actual_w)
            notification = "Canvas cleared!"
            notify_until = time.time() + 1.5
        elif key == ord('s'):              # S → save
            path         = save_drawing(canvas, frame)
            notification = "Saved!"
            notify_until = time.time() + 1.5

    # ── Cleanup ───────────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[Done] Virtual AI Painter closed.")


if __name__ == "__main__":
    main()
