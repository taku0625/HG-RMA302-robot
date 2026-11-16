"""ROS-independent validation of joy_linux's Linux XInput mapping.

ROS timestamps validate transport age; monotonic arrival times drive the existing
watchdog. Invalid or disabled input never refreshes a usable driving command.
"""

from dataclasses import dataclass
import math

from .control import InputState


@dataclass(frozen=True)
class JoyMapping:
    left_x: int = 0
    left_y: int = 1
    right_x: int = 3
    right_y: int = 4
    dpad_x: int = 6
    dpad_y: int = 7
    estop: int = 1
    reset: int = 7
    mode: int = 8
    deadman: int = 4

    def __post_init__(self):
        if any(type(value) is not int or value < 0 for value in vars(self).values()):
            raise ValueError('Joy mapping indices must be nonnegative integers')


def decode_joy(axes, buttons, *, received_at, stamp_age_s, timeout_s, mapping=JoyMapping()):
    """All mapped controls are required; never substitute a missing stop button.

    joy_linux negates Linux axes, so +X means left and +Y means forward.
    LB release inhibits input (hard stop), requiring LB + neutral to rearm.
    B remains active even without LB. Start only clears while LB + neutral.
    """
    invalid = InputState(connected=False, last_input_at=received_at)
    axis_indices = (mapping.left_x, mapping.left_y, mapping.right_x,
                    mapping.right_y, mapping.dpad_x, mapping.dpad_y)
    button_indices = (mapping.estop, mapping.reset, mapping.mode, mapping.deadman)
    if (len(axes) <= max(axis_indices) or len(buttons) <= max(button_indices)
            or not math.isfinite(stamp_age_s) or not 0 <= stamp_age_s < timeout_s
            or not math.isfinite(received_at)
            or any(not math.isfinite(value) or not -1 <= value <= 1 for value in axes)
            or any(value not in (0, 1) for value in buttons)):
        return invalid

    def hat(value):
        return 1 if value > .5 else -1 if value < -.5 else 0

    return InputState(
        left_stick=axes[mapping.left_y], right_stick=axes[mapping.right_y],
        left_x=-axes[mapping.left_x], right_x=-axes[mapping.right_x],
        dpad_x=-hat(axes[mapping.dpad_x]), dpad_y=hat(axes[mapping.dpad_y]),
        estop=bool(buttons[mapping.estop]), reset=bool(buttons[mapping.reset]),
        mode_toggle=bool(buttons[mapping.mode]),
        deadman=bool(buttons[mapping.deadman]), last_input_at=received_at,
    )
