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

# Face blendshape thresholds for intentional blinks.
BLINK_START_SCORE = 0.62
BLINK_RELEASE_SCORE = 0.35
BLINK_MIN_CLOSED_SECONDS = 0.09
BLINK_MAX_CLOSED_SECONDS = 0.70
BLINK_REARM_SECONDS = 0.18
DOUBLE_BLINK_WINDOW_SECONDS = 0.58
SINGLE_BLINK_DELAY_SECONDS = 0.64
BLINK_SCROLL_AMOUNT = 5
