"""
hand_tracker.py — Hand Tracking Module
Uses MediaPipe Hands to detect and track hand landmarks in real time.
"""

import cv2
import mediapipe as mp


class HandTracker:
    """
    Wraps MediaPipe Hands to detect hands and extract landmark positions.
    """

    # MediaPipe landmark indices for key fingertips and knuckles
    TIP_IDS = [4, 8, 12, 16, 20]   # thumb, index, middle, ring, pinky tips
    MCP_IDS = [2, 5, 9, 13, 17]    # corresponding base knuckles

    def __init__(self, max_hands=1, detection_confidence=0.75,
                 tracking_confidence=0.75):
        """
        Args:
            max_hands            : maximum number of hands to detect
            detection_confidence : minimum confidence for initial detection
            tracking_confidence  : minimum confidence for subsequent tracking
        """
        self.mp_hands   = mp.solutions.hands
        self.mp_draw    = mp.solutions.drawing_utils
        self.mp_styles  = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

        self.results    = None   # latest MediaPipe results
        self.landmarks  = []     # list of (x, y) pixel coords for all 21 landmarks

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def find_hands(self, frame, draw=True):
        """
        Process a BGR frame and optionally draw the hand skeleton.

        Returns:
            frame (BGR) with skeleton overlay if draw=True
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.hands.process(rgb)
        rgb.flags.writeable = True

        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style()
                )
        return frame

    def get_landmark_positions(self, frame, hand_index=0):
        """
        Extract pixel (x, y) coordinates for all 21 landmarks of a given hand.

        Args:
            frame      : the current BGR frame (used for dimensions)
            hand_index : which detected hand to use (0 = first)

        Returns:
            list of 21 (x, y) tuples, or empty list if no hand detected
        """
        h, w, _ = frame.shape
        self.landmarks = []

        if (self.results and self.results.multi_hand_landmarks
                and hand_index < len(self.results.multi_hand_landmarks)):
            hand = self.results.multi_hand_landmarks[hand_index]
            for lm in hand.landmark:
                self.landmarks.append((int(lm.x * w), int(lm.y * h)))

        return self.landmarks

    # ------------------------------------------------------------------
    # Gesture helpers
    # ------------------------------------------------------------------

    def fingers_up(self):
        """
        Return a list of 5 booleans indicating which fingers are extended.
        Order: [thumb, index, middle, ring, pinky]

        Detection logic:
          - Thumb  : tip is to the RIGHT of its lower joint (mirrored webcam)
          - Others : tip y-coord is ABOVE (smaller) the MCP knuckle y-coord
        """
        if len(self.landmarks) < 21:
            return [False, False, False, False, False]

        fingers = []

        # Thumb (landmark 4 vs 3 — horizontal check for mirrored feed)
        fingers.append(self.landmarks[4][0] > self.landmarks[3][0])

        # Index → Pinky (vertical check: tip above knuckle)
        for tip, mcp in zip(self.TIP_IDS[1:], self.MCP_IDS[1:]):
            fingers.append(self.landmarks[tip][1] < self.landmarks[mcp][1])

        return fingers

    def get_index_finger_tip(self):
        """
        Returns (x, y) of the index finger tip, or None if no hand detected.
        """
        if len(self.landmarks) >= 9:
            return self.landmarks[8]
        return None

    def get_middle_finger_tip(self):
        """
        Returns (x, y) of the middle finger tip, or None if no hand detected.
        """
        if len(self.landmarks) >= 13:
            return self.landmarks[12]
        return None

    def is_drawing_gesture(self):
        """
        Drawing mode: only index finger is up.
        Returns True if index up and middle finger is down.
        """
        f = self.fingers_up()
        return f[1] and not f[2]

    def is_selection_gesture(self):
        """
        Selection mode: index AND middle fingers are both up.
        Returns True when both are extended.
        """
        f = self.fingers_up()
        return f[1] and f[2]
