import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from robocrew.core.camera import RobotCamera


class TestRobotCamera(unittest.TestCase):

    @patch("robocrew.core.camera.cv2.VideoCapture")
    def test_capture_image_reports_camera_read_failure(self, mock_video_capture):
        capture = MagicMock()
        capture.read.return_value = (False, None)
        mock_video_capture.return_value = capture
        camera = RobotCamera("/dev/camera_center")

        with self.assertRaisesRegex(RuntimeError, "/dev/camera_center"):
            camera.capture_image()


if __name__ == "__main__":
    unittest.main()
