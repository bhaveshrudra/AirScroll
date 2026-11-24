"""Download and create MediaPipe Task landmarkers on demand."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .config import HAND_MODEL_URL, FACE_MODEL_URL


ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"


class ModelManager:
    def __init__(self) -> None:
        self._hand_landmarker = None
        self._face_landmarker = None
        self._last_timestamp_ms = 0
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _ensure_model(filename: str, url: str) -> Path:
        model_path = MODELS_DIR / filename
        if model_path.exists() and model_path.stat().st_size > 100_000:
            return model_path

        print(f"[AirScroll] Downloading {filename} (first run only)...")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AirScroll/1.0 (local webcam gesture project)"},
        )
        temporary_path = model_path.with_suffix(model_path.suffix + ".part")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                with temporary_path.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
            if temporary_path.stat().st_size < 100_000:
                raise RuntimeError("Downloaded model file is unexpectedly small.")
            temporary_path.replace(model_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        print(f"[AirScroll] Saved model: {model_path}")
        return model_path

    def get_hand_landmarker(self):
        if self._hand_landmarker is None:
            model_path = self._ensure_model("hand_landmarker.task", HAND_MODEL_URL)
            options = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.55,
                min_hand_presence_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self._hand_landmarker = vision.HandLandmarker.create_from_options(options)
            print("[AirScroll] Hand detection is ready.")
        return self._hand_landmarker

    def get_face_landmarker(self):
        if self._face_landmarker is None:
            model_path = self._ensure_model("face_landmarker.task", FACE_MODEL_URL)
            options = vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                output_face_blendshapes=True,
                min_face_detection_confidence=0.55,
                min_face_presence_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self._face_landmarker = vision.FaceLandmarker.create_from_options(options)
            print("[AirScroll] Blink detection is ready.")
        return self._face_landmarker

    def next_timestamp_ms(self) -> int:
        import time

        now_ms = int(time.monotonic() * 1000)
        self._last_timestamp_ms = max(now_ms, self._last_timestamp_ms + 1)
        return self._last_timestamp_ms

    def close(self) -> None:
        for landmarker in (self._hand_landmarker, self._face_landmarker):
            if landmarker is not None:
                try:
                    landmarker.close()
                except Exception:
                    pass
