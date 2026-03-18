# vir_draw
Virtual AI Painter that allows users to draw in the air using hand gestures detected through MediaPipe and OpenCV.

# vir_draw

Virtual AI Painter that allows users to draw in the air using hand gestures using computer vision.

The application detects hand landmarks in real time using MediaPipe and allows the user to draw on a virtual canvas with finger movements.

---

## Features

- Real-time hand tracking
- Air drawing using index finger
- Gesture based mode switching
- Color selection toolbar
- Adjustable brush sizes
- Eraser tool
- Save drawings as PNG
- Smooth drawing algorithm
- FPS monitoring

---

## Gestures

| Gesture | Action |
|------|------|
| Index finger up | Drawing mode |
| Index + Middle finger up | Selection mode |
| Hand closed | Idle |

---

## Keyboard Shortcuts

| Key | Action |
|----|----|
| Q / ESC | Quit |
| C | Clear canvas |
| S | Save drawing |

---

## Installation

1. Install Python (Recommended: 3.11)
2. Clone the Repository
3. Create a Virtual Environment (venv)
4. Activate Virtual Environment
5. Upgrade pip
6. Install Required Libraries
pip install opencv-python mediapipe numpy
7. Run the Project
python main.py
