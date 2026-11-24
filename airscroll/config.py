"""Central settings for AirScroll."""

APP_NAME = "AirScroll"

# Webcam
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30

# MediaPipe task models. They are downloaded once into ./models on first use.
HAND_MODEL_URL = (
    "https://huggingface.co/litert-community/MediaPipe-HandLandmarker-Full/"
    "resolve/main/hand_landmarker.task"
)
FACE_MODEL_URL = (
    "https://huggingface.co/litert-community/MediaPipe-FaceLandmarker/"
    "resolve/main/face_landmarker.task"
)

# Hand pinch detection uses the distance between thumb tip (4) and index tip (8),
# normalized by palm width. Separate thresholds prevent flickering at the boundary.
PINCH_START_RATIO = 0.38
PINCH_RELEASE_RATIO = 0.52
HAND_SMOOTHING_ALPHA = 0.30
HAND_SCROLL_STEP_DISTANCE = 0.030
HAND_HSCROLL_STEP_DISTANCE = 0.035
MAX_SCROLL_STEPS_PER_FRAME = 4

# Dynamic sensitivity settings
DEFAULT_SENSITIVITY = 1.0
MIN_SENSITIVITY = 0.5
MAX_SENSITIVITY = 2.5
SENSITIVITY_STEP = 0.25

# Gesture navigation (tab jumping with open-hand swipe)
SWIPE_MIN_DISTANCE = 0.18
SWIPE_MAX_DURATION = 0.35
SWIPE_COOLDOWN_SECONDS = 0.60

# Finger count continuous scrolling (1 finger = up, 2 fingers = down)
FINGER_SCROLL_INTERVAL = 0.07  # Seconds between scroll pulses while holding fingers

# Face blendshape thresholds for intentional blinks (calibrated for high accuracy).
BLINK_START_SCORE = 0.50  # Lowered from 0.62 for reliable, natural detection
BLINK_RELEASE_SCORE = 0.28  # Eyelids open threshold
BLINK_MIN_CLOSED_SECONDS = 0.08  # Minimum intentional blink closure duration
BLINK_MAX_CLOSED_SECONDS = 0.85  # Maximum closed duration
BLINK_REARM_SECONDS = 0.15  # Cooldown between consecutive blinks
DOUBLE_BLINK_WINDOW_SECONDS = 0.48  # Window to catch second blink for scroll-up
SINGLE_BLINK_DELAY_SECONDS = 0.40  # Faster response for single blink scroll-down
BLINK_SCROLL_AMOUNT = 5
