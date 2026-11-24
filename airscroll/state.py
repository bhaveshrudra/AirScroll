"""Thread-safe state shared by the webcam loop and global hotkeys."""

from __future__ import annotations

import threading

from . import config


class AppState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mode = "HAND"
        self._paused = False
        self._sensitivity = config.DEFAULT_SENSITIVITY
        self.stop_event = threading.Event()

    def snapshot(self) -> tuple[str, bool, float]:
        with self._lock:
            return self._mode, self._paused, self._sensitivity

    def get_sensitivity(self) -> float:
        with self._lock:
            return self._sensitivity

    def increase_sensitivity(self) -> float:
        with self._lock:
            self._sensitivity = min(
                config.MAX_SENSITIVITY,
                round(self._sensitivity + config.SENSITIVITY_STEP, 2)
            )
            return self._sensitivity

    def decrease_sensitivity(self) -> float:
        with self._lock:
            self._sensitivity = max(
                config.MIN_SENSITIVITY,
                round(self._sensitivity - config.SENSITIVITY_STEP, 2)
            )
            return self._sensitivity

    def reset_sensitivity(self) -> float:
        with self._lock:
            self._sensitivity = config.DEFAULT_SENSITIVITY
            return self._sensitivity

    def set_mode(self, mode: str) -> None:
        normalized = mode.upper()
        if normalized not in {"HAND", "BLINK"}:
            raise ValueError(f"Unsupported mode: {mode}")
        with self._lock:
            self._mode = normalized

    def toggle_pause(self) -> None:
        with self._lock:
            self._paused = not self._paused

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            self._paused = paused

    def stop(self) -> None:
        self.stop_event.set()
