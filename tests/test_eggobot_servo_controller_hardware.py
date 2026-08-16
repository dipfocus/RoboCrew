import os
import time
import unittest

from lerobot.motors.feetech import OperatingMode

from robocrew.robots.EggoBot.servo_controller import HEAD_SERVO_MAP, ServoController


EGGOBOT_USB_PORT = os.environ.get("EGGOBOT_USB_PORT", "/dev/eggobot")
EGGOBOT_TEST_SPEED = int(os.environ.get("EGGOBOT_TEST_SPEED", "2500"))
EGGOBOT_TEST_METERS = float(os.environ.get("EGGOBOT_TEST_METERS", "0.02"))
EGGOBOT_TEST_DEGREES = float(os.environ.get("EGGOBOT_TEST_DEGREES", "5"))


class TestEggoBotServoControllerHardware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servo_controller = ServoController(
            usb_port=EGGOBOT_USB_PORT,
            speed=EGGOBOT_TEST_SPEED,
        )

    @classmethod
    def tearDownClass(cls):
        cls.servo_controller.disconnect()

    def setUp(self):
        self.servo_controller._wheels_stop()

    def tearDown(self):
        self.servo_controller._wheels_stop()

    def test_servo_controller_initializes_expected_modes(self):
        for wheel_id in self.servo_controller._wheel_ids:
            mode = self.servo_controller.servo_bus.read("Operating_Mode", wheel_id, normalize=False)
            self.assertEqual(mode, OperatingMode.VELOCITY.value)

        for head_id in self.servo_controller._head_ids:
            mode = self.servo_controller.servo_bus.read("Operating_Mode", head_id, normalize=False)
            self.assertEqual(mode, OperatingMode.POSITION.value)

    def test_head_yaw_and_pitch_small_motion(self):
        self.servo_controller.turn_head_pitch(30)
        time.sleep(0.4)
        self.servo_controller.turn_head_yaw(-20)
        time.sleep(0.4)
        self.servo_controller.turn_head_yaw(20)
        time.sleep(0.4)
        self.servo_controller.reset_head_position()

        yaw_position = self.servo_controller.servo_bus.read("Present_Position", HEAD_SERVO_MAP["yaw"])
        pitch_position = self.servo_controller.servo_bus.read("Present_Position", HEAD_SERVO_MAP["pitch"])

        self.assertIsInstance(yaw_position, (int, float))
        self.assertIsInstance(pitch_position, (int, float))
        self.assertEqual(self.servo_controller._head_positions[HEAD_SERVO_MAP["yaw"]], 0)
        self.assertEqual(self.servo_controller._head_positions[HEAD_SERVO_MAP["pitch"]], 22)

    def test_small_forward_backward_motion(self):
        self.servo_controller.go_forward(EGGOBOT_TEST_METERS)
        time.sleep(0.2)
        self.servo_controller.go_backward(EGGOBOT_TEST_METERS)

    def test_small_turn_motion(self):
        self.servo_controller.turn_left(EGGOBOT_TEST_DEGREES)
        time.sleep(0.2)
        self.servo_controller.turn_right(EGGOBOT_TEST_DEGREES)

    def test_small_strafe_motion(self):
        self.servo_controller.strafe_left(EGGOBOT_TEST_METERS)
        time.sleep(0.2)
        self.servo_controller.strafe_right(EGGOBOT_TEST_METERS)


if __name__ == "__main__":
    unittest.main()
