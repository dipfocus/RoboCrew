import cv2
from robocrew.core.utils import basic_augmentation

class RobotCamera:
    def __init__(self, usb_port):
        self.usb_port = usb_port
        self.capture = cv2.VideoCapture(usb_port)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def release(self):
        self.capture.release()
        
    def reopen(self):
        self.capture.open(self.usb_port)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def capture_image(self, camera_fov=120, center_angle=0, navigation_mode="normal"):
        self.capture.grab() # Clear the buffer
        success, frame = self.capture.read()
        if not success or frame is None:
            raise RuntimeError(
                f"Failed to capture image from camera '{self.usb_port}'. "
                "Check that the camera path is correct and the device is available."
            )
        frame = basic_augmentation(frame, h_fov=camera_fov, center_angle=center_angle, navigation_mode=navigation_mode)
        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()
