"""Global keyboard shortcuts so the user can keep their reading window focused."""

from __future__ import annotations

from typing import Callable, Optional

from pynput import keyboard

from .state import AppState


class HotkeyManager:
    def __init__(
        self,
        state: AppState,
        on_next_tab: Optional[Callable[[], None]] = None,
        on_prev_tab: Optional[Callable[[], None]] = None,
    ) -> None:
        self.state = state
        hotkeys = {
            "<ctrl>+<shift>+<alt>+1": lambda: self.state.set_mode("HAND"),
            "<ctrl>+<shift>+<alt>+2": lambda: self.state.set_mode("BLINK"),
            "<ctrl>+<shift>+<alt>+p": self.state.toggle_pause,
            "<ctrl>+<shift>+<alt>+=": self.state.increase_sensitivity,
            "<ctrl>+<shift>+<alt>+-": self.state.decrease_sensitivity,
            "<ctrl>+<shift>+<alt>+0": self.state.reset_sensitivity,
            "<ctrl>+<shift>+<alt>+q": self.state.stop,
        }
        if on_next_tab:
            hotkeys["<ctrl>+<shift>+<alt>+right"] = on_next_tab
        if on_prev_tab:
            hotkeys["<ctrl>+<shift>+<alt>+left"] = on_prev_tab
        self.listener = keyboard.GlobalHotKeys(hotkeys)

    def start(self) -> None:
        self.listener.start()

    def stop(self) -> None:
        try:
            self.listener.stop()
        except Exception:
            pass
