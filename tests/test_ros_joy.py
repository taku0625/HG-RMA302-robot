import math
import unittest

from hg_rma302.control import DriveController, DriveSettings
from hg_rma302.joy_input import JoyMapping, decode_joy


def sample(now=1.0, *, axes=None, held=(4,), age=0.0):
    buttons = [int(index in held) for index in range(11)]
    return decode_joy(axes or [0.0] * 8, buttons, received_at=now,
                      stamp_age_s=age, timeout_s=.5)


class JoyTests(unittest.TestCase):
    def test_linux_xinput_signs_and_buttons(self):
        result = sample(axes=[-.3, .8, 1., -.7, .2, 1., -1., 1.], held=(1, 4, 7, 8))
        self.assertAlmostEqual(result.left_x, .3)
        self.assertAlmostEqual(result.left_stick, .8)
        self.assertAlmostEqual(result.right_x, .7)
        self.assertEqual((result.dpad_x, result.dpad_y), (1, 1))
        self.assertTrue(result.estop and result.reset and result.mode_toggle and result.connected)

    def test_missing_bad_and_stale_packets_disconnect(self):
        cases = [([], [0] * 11, 0), ([0.] * 8, [], 0),
                 ([math.nan] * 8, [0] * 11, 0), ([1.1] * 8, [0] * 11, 0),
                 ([0.] * 8, [2] * 11, 0), ([0.] * 8, [0] * 11, .5),
                 ([0.] * 8, [0] * 11, -.01), ([0.] * 8, [0] * 11, math.inf)]
        for axes, buttons, age in cases:
            with self.subTest(axes=axes, buttons=buttons, age=age):
                result = decode_joy(axes, buttons, received_at=1., stamp_age_s=age, timeout_s=.5)
                self.assertFalse(result.connected)

    def test_deadman_and_neutral_rearm(self):
        controller = DriveController(DriveSettings(control_mode='joystick'))
        axes = [0., 1., 0., 0., 0., 0., 0., 0.]
        self.assertEqual(controller.update(sample(axes=axes), 1.).reason, 'CENTER_CONTROLS')
        controller.update(sample(1.01), 1.01)
        self.assertTrue(controller.update(sample(1.02, axes=axes), 1.02).enabled)
        self.assertEqual(controller.update(sample(1.03, axes=axes, held=()), 1.03).reason,
                         'DEADMAN_RELEASED')
        self.assertFalse(controller.update(sample(1.04, axes=axes), 1.04).enabled)
        controller.update(sample(1.05), 1.05)
        self.assertTrue(controller.update(sample(1.06, axes=axes), 1.06).enabled)

    def test_b_latches_even_without_deadman_and_start_requires_neutral(self):
        controller = DriveController(DriveSettings(control_mode='joystick'))
        controller.update(sample(held=(1,)), 1.)
        self.assertEqual(controller.update(sample(1.01), 1.01).reason, 'STOP_LATCHED')
        moving = [0., 1., 0., 0., 0., 0., 0., 0.]
        self.assertFalse(controller.update(sample(1.02, axes=moving, held=(4, 7)), 1.02).enabled)
        controller.update(sample(1.03), 1.03)
        controller.update(sample(1.04, held=(4, 7)), 1.04)
        self.assertTrue(controller.update(sample(1.05, axes=moving), 1.05).enabled)

    def test_polling_does_not_refresh_watchdog(self):
        controller = DriveController(DriveSettings())
        state = sample()
        controller.update(state, 1.)
        for now in (1.1, 1.2, 1.3, 1.4):
            controller.update(state, now)
        self.assertEqual(controller.update(state, 1.51).reason, 'INPUT_TIMEOUT')

    def test_mapping_rejects_negative_indices(self):
        with self.assertRaises(ValueError):
            JoyMapping(estop=-1)


if __name__ == '__main__':
    unittest.main()
