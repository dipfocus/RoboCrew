import os
import unittest

from robocrew.robots.EggoBot import tools as eggobot_tools
from robocrew.robots.EggoBot.servo_controller import ServoController


EGGOBOT_USB_PORT = os.environ.get("EGGOBOT_USB_PORT", "/dev/eggobot")
EGGOBOT_TEST_SPEED = int(os.environ.get("EGGOBOT_TEST_SPEED", "2500"))
EGGOBOT_TEST_DEGREES = float(os.environ.get("EGGOBOT_TEST_DEGREES", "5"))


class TestEggoBotMovementTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servo_controller = ServoController(
            usb_port=EGGOBOT_USB_PORT,
            speed=EGGOBOT_TEST_SPEED,
        )
        cls.addClassCleanup(cls.servo_controller.disconnect)
        cls.servo_controller._wheels_stop()

    def setUp(self):
        self.addCleanup(self.servo_controller._wheels_stop)
        self.servo_controller._wheels_stop()

    def _assert_distance_limited(self, factory, expected_result):
        movement_tool = factory(self.servo_controller)

        result = movement_tool.invoke({"distance_meters": 0.3})

        self.assertEqual(result, expected_result)

    def test_move_forward_limits_distance(self):
        self._assert_distance_limited(
            eggobot_tools.create_move_forward,
            "Moved forward 0.05 meters.",
        )

    def test_move_backward_limits_distance(self):
        self._assert_distance_limited(
            eggobot_tools.create_move_backward,
            "Moved backward 0.05 meters.",
        )

    def test_strafe_left_limits_distance(self):
        self._assert_distance_limited(
            eggobot_tools.create_strafe_left,
            "Strafed left by 0.05 meters.",
        )

    def test_strafe_right_limits_distance(self):
        self._assert_distance_limited(
            eggobot_tools.create_strafe_right,
            "Strafed right by 0.05 meters.",
        )

    def test_turn_left(self):
        movement_tool = eggobot_tools.create_turn_left(self.servo_controller)

        result = movement_tool.invoke({"angle_degrees": EGGOBOT_TEST_DEGREES})

        self.assertEqual(
            result,
            f"Turned left by {EGGOBOT_TEST_DEGREES} degrees.",
        )

    def test_turn_right(self):
        movement_tool = eggobot_tools.create_turn_right(self.servo_controller)

        result = movement_tool.invoke({"angle_degrees": EGGOBOT_TEST_DEGREES})

        self.assertEqual(
            result,
            f"Turned right by {EGGOBOT_TEST_DEGREES} degrees.",
        )

    def test_negative_move_forward_limits_backward_distance(self):
        movement_tool = eggobot_tools.create_move_forward(self.servo_controller)

        result = movement_tool.invoke({"distance_meters": -0.3})

        self.assertEqual(result, "Moved backward 0.05 meters.")

    def test_distance_below_limit_is_unchanged(self):
        movement_tool = eggobot_tools.create_move_forward(self.servo_controller)

        result = movement_tool.invoke({"distance_meters": 0.03})

        self.assertEqual(result, "Moved forward 0.03 meters.")


if __name__ == "__main__":
    unittest.main()
