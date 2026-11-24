"""Gesture recognition and conversion into scroll-wheel events."""

from __future__ import annotations

import math
import time
from typing import Callable, Optional

from . import config

ScrollCallback = Callable[[int], None]


class HandPinchController:
    """Pinch to scroll; swipe open hand horizontally to switch browser/editor tabs."""

    def __init__(
        self,
        scroll: ScrollCallback,
        hscroll: Optional[ScrollCallback] = None,
        on_next_tab: Optional[Callable[[], None]] = None,
        on_prev_tab: Optional[Callable[[], None]] = None,
    ) -> None:
        self.scroll = scroll
        self.hscroll = hscroll
        self.on_next_tab = on_next_tab
        self.on_prev_tab = on_prev_tab
        self.is_pinching = False
        self.smoothed_y: Optional[float] = None
        self.previous_y: Optional[float] = None
        self.motion_accumulator = 0.0
        self.smoothed_x: Optional[float] = None
        self.previous_x: Optional[float] = None
        self.x_motion_accumulator = 0.0
        self.last_ratio = 1.0
        self.swipe_history: list[tuple[float, float]] = []
        self.last_swipe_time = 0.0

    def reset(self) -> None:
        self.is_pinching = False
        self.smoothed_y = None
        self.previous_y = None
        self.motion_accumulator = 0.0
        self.smoothed_x = None
        self.previous_x = None
        self.x_motion_accumulator = 0.0
        self.last_ratio = 1.0
        self.swipe_history.clear()

    def update(self, landmarks) -> dict:
        if not landmarks or len(landmarks) < 18:
            self.reset()
            return {"pinching": False, "ratio": None, "scroll": ""}

        thumb = landmarks[4]
        index = landmarks[8]
        index_mcp = landmarks[5]
        pinky_mcp = landmarks[17]

        tip_distance = math.hypot(thumb.x - index.x, thumb.y - index.y)
        palm_width = math.hypot(index_mcp.x - pinky_mcp.x, index_mcp.y - pinky_mcp.y)
        ratio = tip_distance / max(palm_width, 1e-5)
        self.last_ratio = ratio

        # Hysteresis: a slightly wider release threshold stops state flicker.
        if not self.is_pinching and ratio < config.PINCH_START_RATIO:
            self.is_pinching = True
            self.smoothed_y = (thumb.y + index.y) / 2.0
            self.previous_y = self.smoothed_y
            self.motion_accumulator = 0.0
            self.smoothed_x = (thumb.x + index.x) / 2.0
            self.previous_x = self.smoothed_x
            self.x_motion_accumulator = 0.0
            self.swipe_history.clear()
        elif self.is_pinching and ratio > config.PINCH_RELEASE_RATIO:
            self.is_pinching = False
            self.previous_y = None
            self.motion_accumulator = 0.0
            self.previous_x = None
            self.x_motion_accumulator = 0.0

        directions = []

        # Open-hand swipe gesture for tab jumping when not pinching
        if not self.is_pinching:
            now = time.monotonic()
            palm_x = (landmarks[0].x + landmarks[9].x) / 2.0
            self.swipe_history.append((now, palm_x))
            max_duration = getattr(config, "SWIPE_MAX_DURATION", 0.35)
            self.swipe_history = [(t, x) for (t, x) in self.swipe_history if now - t <= max_duration]

            if len(self.swipe_history) >= 3:
                start_t, start_x = self.swipe_history[0]
                dt = now - start_t
                dx = palm_x - start_x
                min_dist = getattr(config, "SWIPE_MIN_DISTANCE", 0.18)
                cooldown = getattr(config, "SWIPE_COOLDOWN_SECONDS", 0.60)

                if dt >= 0.08 and abs(dx) >= min_dist:
                    if now - self.last_swipe_time >= cooldown:
                        if dx > 0:
                            directions.append("SWIPE RIGHT: NEXT TAB")
                            if self.on_next_tab:
                                self.on_next_tab()
                        else:
                            directions.append("SWIPE LEFT: PREV TAB")
                            if self.on_prev_tab:
                                self.on_prev_tab()
                        self.last_swipe_time = now
                        self.swipe_history.clear()
        if self.is_pinching:
            raw_y = (thumb.y + index.y) / 2.0
            raw_x = (thumb.x + index.x) / 2.0
            alpha = config.HAND_SMOOTHING_ALPHA

            if self.smoothed_y is None:
                self.smoothed_y = raw_y
            else:
                self.smoothed_y = alpha * raw_y + (1.0 - alpha) * self.smoothed_y

            if self.smoothed_x is None:
                self.smoothed_x = raw_x
            else:
                self.smoothed_x = alpha * raw_x + (1.0 - alpha) * self.smoothed_x

            # Vertical scrolling: moving hand up moves document down
            if self.previous_y is not None:
                self.motion_accumulator += self.previous_y - self.smoothed_y
                step_distance = config.HAND_SCROLL_STEP_DISTANCE

                if self.motion_accumulator >= step_distance:
                    steps = min(
                        config.MAX_SCROLL_STEPS_PER_FRAME,
                        int(self.motion_accumulator / step_distance),
                    )
                    self.scroll(-steps)
                    self.motion_accumulator -= steps * step_distance
                    directions.append("DOWN")
                elif self.motion_accumulator <= -step_distance:
                    steps = min(
                        config.MAX_SCROLL_STEPS_PER_FRAME,
                        int(abs(self.motion_accumulator) / step_distance),
                    )
                    self.scroll(steps)
                    self.motion_accumulator += steps * step_distance
                    directions.append("UP")

            # Horizontal scrolling: moving hand left/right
            if self.previous_x is not None and self.hscroll is not None:
                self.x_motion_accumulator += self.previous_x - self.smoothed_x
                h_step_distance = getattr(config, "HAND_HSCROLL_STEP_DISTANCE", 0.035)

                if self.x_motion_accumulator >= h_step_distance:
                    steps = min(
                        config.MAX_SCROLL_STEPS_PER_FRAME,
                        int(self.x_motion_accumulator / h_step_distance),
                    )
                    self.hscroll(steps)
                    self.x_motion_accumulator -= steps * h_step_distance
                    directions.append("RIGHT")
                elif self.x_motion_accumulator <= -h_step_distance:
                    steps = min(
                        config.MAX_SCROLL_STEPS_PER_FRAME,
                        int(abs(self.x_motion_accumulator) / h_step_distance),
                    )
                    self.hscroll(-steps)
                    self.x_motion_accumulator += steps * h_step_distance
                    directions.append("LEFT")

            self.previous_y = self.smoothed_y
            self.previous_x = self.smoothed_x

        scroll_direction = " + ".join(directions)
        return {"pinching": self.is_pinching, "ratio": ratio, "scroll": scroll_direction}


class BlinkController:
    """A single intentional blink scrolls down; a quick double blink scrolls up."""

    def __init__(self, scroll: ScrollCallback) -> None:
        self.scroll = scroll
        self.eyes_closed = False
        self.closed_since: Optional[float] = None
        self.last_blink_at = 0.0
        self.pending_single_at: Optional[float] = None
        self.last_action = ""

    def reset(self) -> None:
        self.eyes_closed = False
        self.closed_since = None
        self.last_blink_at = 0.0
        self.pending_single_at = None
        self.last_action = ""

    def _register_blink(self, now: float) -> None:
        if self.pending_single_at is None:
            self.pending_single_at = now
            self.last_action = "BLINK DETECTED"
        elif now - self.pending_single_at <= config.DOUBLE_BLINK_WINDOW_SECONDS:
            # The second blink cancels the pending down-scroll and triggers up-scroll.
            self.pending_single_at = None
            self.scroll(config.BLINK_SCROLL_AMOUNT)
            self.last_action = "DOUBLE BLINK: SCROLL UP"
        else:
            # The earlier single blink is already due; queue this blink as a new single.
            self.scroll(-config.BLINK_SCROLL_AMOUNT)
            self.pending_single_at = now
            self.last_action = "BLINK DETECTED"

    def update(self, blink_score: Optional[float]) -> dict:
        now = time.monotonic()

        # Delay a single-blink action so a second blink can override it.
        if (
            self.pending_single_at is not None
            and now - self.pending_single_at > config.SINGLE_BLINK_DELAY_SECONDS
        ):
            self.scroll(-config.BLINK_SCROLL_AMOUNT)
            self.pending_single_at = None
            self.last_action = "SINGLE BLINK: SCROLL DOWN"

        if blink_score is None:
            self.eyes_closed = False
            self.closed_since = None
            return {"closed": False, "score": None, "action": self.last_action}

        if not self.eyes_closed and blink_score >= config.BLINK_START_SCORE:
            self.eyes_closed = True
            self.closed_since = now
        elif self.eyes_closed and blink_score <= config.BLINK_RELEASE_SCORE:
            duration = now - (self.closed_since or now)
            self.eyes_closed = False
            self.closed_since = None
            if (
                config.BLINK_MIN_CLOSED_SECONDS <= duration <= config.BLINK_MAX_CLOSED_SECONDS
                and now - self.last_blink_at >= config.BLINK_REARM_SECONDS
            ):
                self.last_blink_at = now
                self._register_blink(now)

        return {
            "closed": self.eyes_closed,
            "score": blink_score,
            "action": self.last_action,
        }
