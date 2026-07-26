import os
import sys
import unittest

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from robocrew.core.camera import RobotCamera


class TestRobotCamera(unittest.TestCase):
    def setUp(self):
        self.camera = RobotCamera("/dev/camera_center")

    def tearDown(self):
        self.camera.release()

    def test_capture_image_from_real_camera(self):
        image = self.camera.capture_image()

        self.assertIsInstance(image, bytes)
        self.assertGreater(len(image), 0)
        frame = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR)
        self.assertIsNotNone(frame)


if __name__ == "__main__":
    unittest.main()
