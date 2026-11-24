"""AirScroll: touchless scrolling with a laptop webcam."""

from __future__ import annotations

import sys
import time
from typing import Optional

import cv2
import mediapipe as mp
import pyautogui
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController

from airscroll.config import APP_NAME, CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH
from airscroll.gestures import BlinkController, HandPinchController
from airscroll.hotkeys import HotkeyManager
from airscroll.model_manager import ModelManager
from airscroll.state import AppState


# Keep PyAutoGUI's corner fail-safe enabled. Moving the mouse to the top-left
# corner can interrupt automation if something unexpected happens.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

mouse_device = MouseController()
keyboard_device = KeyboardController()


def draw_hud(
    frame,
    mode: str,
    paused: bool,
    sensitivity: float,
    message: str,
    detail: str = "",
) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (frame.shape[1] - 10, 154), (18, 22, 30), -1)
    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

    title = f"{APP_NAME}  |  {mode} MODE  |  {sensitivity:.2f}x SPEED"
    cv2.putText(frame, title, (24, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (245, 248, 255), 2)
    status = "PAUSED" if paused else "ACTIVE"
    status_color = (80, 190, 255) if paused else (100, 235, 150)
    cv2.putText(frame, status, (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.58, status_color, 2)
    cv2.putText(frame, message[:70], (24, 99), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 235, 245), 1)
    if detail:
        cv2.putText(frame, detail[:70], (24, 124), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 195, 215), 1)
    cv2.putText(
        frame,
        "Pinch: Scroll | Swipe: Tabs | Ctrl+Shift+Alt: 1/2 Mode | +/- Spd | Q Quit",
        (24, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (175, 190, 210),
        1,
    )


def get_blink_score(face_result) -> Optional[float]:
    if not face_result.face_blendshapes:
        return None

    categories = face_result.face_blendshapes[0]
    scores = {
        category.category_name: category.score
        for category in categories
    }
    left = scores.get("eyeBlinkLeft", 0.0)
    right = scores.get("eyeBlinkRight", 0.0)
    return (left + right) / 2.0


def open_camera():
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        raise RuntimeError(
            "Could not open the webcam. Close other apps using the camera or change CAMERA_INDEX in airscroll/config.py."
        )
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return camera


def main() -> int:
    state = AppState()
    models = ModelManager()
    hand_controller = HandPinchController(
        scroll=lambda amount: safe_scroll(amount, state),
        hscroll=lambda amount: safe_hscroll(amount, state),
        on_next_tab=safe_next_tab,
        on_prev_tab=safe_prev_tab,
    )
    blink_controller = BlinkController(lambda amount: safe_scroll(amount, state))
    hotkeys = HotkeyManager(
        state,
        on_next_tab=safe_next_tab,
        on_prev_tab=safe_prev_tab,
    )

    camera = None
    current_mode = "HAND"
    last_message = "Make a pinch with thumb + index finger, then move your hand."
    detail = ""

    print("\nAirScroll is starting...")
    print("Global shortcuts work while your browser or PDF reader is focused:")
    print("  Ctrl+Shift+Alt+1  -> Hand Pinch mode")
    print("  Ctrl+Shift+Alt+2  -> Blink mode")
    print("  Ctrl+Shift+Alt+=  -> Increase sensitivity (+)")
    print("  Ctrl+Shift+Alt+-  -> Decrease sensitivity (-)")
    print("  Ctrl+Shift+Alt+0  -> Reset sensitivity (1.0x)")
    print("  Ctrl+Shift+Alt+P  -> Pause / resume")
    print("  Ctrl+Shift+Alt+Q  -> Quit\n")
    print("Camera frames are processed locally; no video is uploaded or recorded.\n")

    try:
        camera = open_camera()
        hotkeys.start()
        cv2.namedWindow(APP_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(APP_NAME, FRAME_WIDTH, FRAME_HEIGHT)
        try:
            cv2.setWindowProperty(APP_NAME, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass

        while not state.stop_event.is_set():
            ok, frame = camera.read()
            if not ok:
                last_message = "Webcam frame unavailable. Check the camera connection."
                time.sleep(0.05)
                continue

            # Mirror the preview so gestures feel natural, like looking in a mirror.
            frame = cv2.flip(frame, 1)
            mode, paused, sensitivity = state.snapshot()

            if mode != current_mode:
                hand_controller.reset()
                blink_controller.reset()
                current_mode = mode
                last_message = (
                    "Pinch thumb + index, then move up/down/left/right."
                    if mode == "HAND"
                    else "Blink once to scroll down; double-blink to scroll up."
                )
                detail = ""

            if paused:
                draw_hud(frame, mode, True, sensitivity, "Paused. Use Ctrl+Shift+Alt+P to resume.")
            else:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = models.next_timestamp_ms()

                try:
                    if mode == "HAND":
                        landmarker = models.get_hand_landmarker()
                        result = landmarker.detect_for_video(mp_image, timestamp_ms)
                        hand = result.hand_landmarks[0] if result.hand_landmarks else None
                        gesture = hand_controller.update(hand)

                        if hand:
                            thumb = hand[4]
                            index = hand[8]
                            h, w = frame.shape[:2]
                            thumb_point = (int(thumb.x * w), int(thumb.y * h))
                            index_point = (int(index.x * w), int(index.y * h))
                            cv2.line(frame, thumb_point, index_point, (80, 220, 255), 2)
                            cv2.circle(frame, thumb_point, 8, (80, 220, 255), -1)
                            cv2.circle(frame, index_point, 8, (80, 220, 255), -1)

                        if gesture["pinching"]:
                            last_message = "PINCH LOCKED — move hand up/down to scroll"
                        elif hand:
                            last_message = "Hand detected — bring thumb and index finger together."
                        else:
                            last_message = "Show one hand to the webcam."

                        if gesture["scroll"]:
                            detail = f"Scrolling {gesture['scroll'].lower()}"
                        elif gesture["ratio"] is not None:
                            detail = f"Pinch ratio: {gesture['ratio']:.2f}"

                    else:
                        landmarker = models.get_face_landmarker()
                        result = landmarker.detect_for_video(mp_image, timestamp_ms)
                        face_score = get_blink_score(result)
                        gesture = blink_controller.update(face_score)

                        if face_score is None:
                            last_message = "Keep your face visible and look toward the webcam."
                            detail = "Waiting for face detection..."
                        else:
                            last_message = "Blink once = down | quick double-blink = up"
                            detail = f"Eye blink score: {face_score:.2f}"
                            if gesture["closed"]:
                                cv2.putText(
                                    frame,
                                    "EYES CLOSED",
                                    (24, frame.shape[0] - 28),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.65,
                                    (80, 220, 255),
                                    2,
                                )
                            if gesture["action"]:
                                detail = gesture["action"]

                except pyautogui.FailSafeException:
                    state.set_paused(True)
                    last_message = "Safety stop triggered. Move the pointer away from the top-left corner, then resume."

                draw_hud(frame, mode, False, sensitivity, last_message, detail)

            cv2.imshow(APP_NAME, frame)
            # Allows the preview window to repaint. Global controls use pynput.
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # Esc also quits when the preview window is focused.
                state.stop()

            try:
                # Returns -1 when the user closes the window with the 'X' button
                if cv2.getWindowProperty(APP_NAME, cv2.WND_PROP_VISIBLE) < 0:
                    state.stop()
            except cv2.error:
                state.stop()

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"\n[AirScroll error] {exc}", file=sys.stderr)
        print("Tip: check the setup steps in README.md and make sure the webcam is available.", file=sys.stderr)
        return 1
    finally:
        state.stop()
        hotkeys.stop()
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()
        models.close()
        print("\nAirScroll stopped. Webcam released.")

    return 0


def safe_scroll(amount: int, state: AppState) -> None:
    """Send a vertical wheel event to the window under the mouse pointer."""
    try:
        steps = int(round(amount * state.get_sensitivity()))
        if steps != 0:
            mouse_device.scroll(0, steps)
    except Exception:
        try:
            pyautogui.scroll(amount * 120)
        except Exception:
            pass


def safe_hscroll(amount: int, state: AppState) -> None:
    """Send a horizontal wheel event to the window under the mouse pointer."""
    try:
        steps = int(round(amount * state.get_sensitivity()))
        if steps != 0:
            mouse_device.scroll(steps, 0)
    except Exception:
        try:
            pyautogui.hscroll(amount * 120)
        except Exception:
            pass


def safe_next_tab() -> None:
    """Switch to next tab (Ctrl + Tab)."""
    try:
        with keyboard_device.pressed(Key.ctrl):
            keyboard_device.press(Key.tab)
            keyboard_device.release(Key.tab)
    except Exception:
        pass


def safe_prev_tab() -> None:
    """Switch to previous tab (Ctrl + Shift + Tab)."""
    try:
        with keyboard_device.pressed(Key.ctrl):
            with keyboard_device.pressed(Key.shift):
                keyboard_device.press(Key.tab)
                keyboard_device.release(Key.tab)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
