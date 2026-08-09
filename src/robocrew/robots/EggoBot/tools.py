import base64
import logging

from langchain_core.tools import tool  # type: ignore[import]

from robocrew.core.utils import stop_listening_during_tool_execution
import time


logger = logging.getLogger(__name__)


def create_move_forward(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def move_forward(distance_meters: float) -> str:
        """Drives the robot forward (or backward) for a specific distance."""

        distance = float(distance_meters)
        direction = "forward" if distance >= 0 else "backward"
        logger.debug("Moving %s %.2f meters...", direction, abs(distance))
        if distance >= 0:
            servo_controller.go_forward(distance)
        else:
            servo_controller.go_backward(-distance)
        return f"Moved {'forward' if distance >= 0 else 'backward'} {abs(distance):.2f} meters."

    return move_forward

def create_move_backward(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def move_backward(distance_meters: float) -> str:
        """Drives the robot forward (or backward) for a specific distance."""

        distance = float(distance_meters)
        logger.debug("Moving backward %s meters...", distance)
        servo_controller.go_backward(distance)
        return f"Moved backward {distance} meters."

    return move_backward

def create_turn_right(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def turn_right(angle_degrees: float) -> str:
        """Turns the robot right by angle in degrees. Use only when robot body not touches any obstacle."""
        angle = float(angle_degrees)
        logger.debug("Turning right %s degrees...", angle)
        servo_controller.turn_right(angle)
        time.sleep(0.4)  # wait a bit after turn for stabilization
        return f"Turned right by {angle} degrees."

    return turn_right

def create_turn_left(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def turn_left(angle_degrees: float) -> str:
        """Turns the robot left by angle in degrees. Use only when robot body not touches any obstacle."""
        angle = float(angle_degrees)
        logger.debug("Turning left %s degrees...", angle)
        servo_controller.turn_left(angle)
        time.sleep(0.4)  # wait a bit after turn for stabilization
        return f"Turned left by {angle} degrees."

    return turn_left


def create_strafe_left(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def strafe_left(distance_meters: float) -> str:
        """Moves the robot sideways left by a specific distance in meters."""
        distance = float(distance_meters)
        logger.debug("Strafing left %s meters...", distance)
        servo_controller.strafe_left(distance)
        return f"Strafed left by {distance} meters."

    return strafe_left

def create_strafe_right(servo_controller, sound_receiver=None):
    @tool
    @stop_listening_during_tool_execution(sound_receiver)
    def strafe_right(distance_meters: float) -> str:
        """Moves the robot sideways right by a specific distance in meters."""
        distance = float(distance_meters)
        logger.debug("Strafing right %s meters...", distance)
        servo_controller.strafe_right(distance)
        return f"Strafed right by {distance} meters."

    return strafe_right

def create_go_to_precision_mode(servo_controller):
    @tool
    def go_to_precision_mode() -> str:
        """Sets the robot to precision movement mode. Use it when close to obstacles or target."""
        logger.debug("Switching to precision movement mode...")
        servo_controller.turn_head_to_vla_position(50)
        return "Robot set to precision movement mode."

    return go_to_precision_mode

def create_go_to_normal_mode(servo_controller):
    @tool
    def go_to_normal_mode() -> str:
        """Sets the robot to normal movement mode for long distance rides."""
        logger.debug("Switching to normal movement mode...")
        servo_controller.reset_head_position()
        return "Robot set to normal movement mode."

    return go_to_normal_mode

def create_look_around(servo_controller, main_camera):
    @tool
    def look_around() -> list:
        """Look around yourself to find a thing you looking for or to understand an envinronment."""
        movement_delay = 0.9  # seconds
        logger.debug("Looking around...")
        servo_controller.turn_head_yaw(-120)
        time.sleep(movement_delay)
        image_1 = main_camera.capture_image(center_angle=-120)
        image_1_64 = base64.b64encode(image_1).decode('utf-8')
        servo_controller.turn_head_yaw(-40)
        time.sleep(movement_delay)
        image_2 = main_camera.capture_image(center_angle=-40)
        image_2_64 = base64.b64encode(image_2).decode('utf-8')  
        servo_controller.turn_head_yaw(40)
        time.sleep(movement_delay)
        image_3 = main_camera.capture_image(center_angle=40)
        image_3_64 = base64.b64encode(image_3).decode('utf-8')
        servo_controller.turn_head_yaw(120)
        time.sleep(movement_delay)
        image_4 = main_camera.capture_image(center_angle=120)
        image_4_64 = base64.b64encode(image_4).decode('utf-8')
        servo_controller.turn_head_yaw(0)  # look forward again
        time.sleep(movement_delay)

        return "Looked around", [
            {"type": "text", "text": "Left"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_1_64}",}},
            {"type": "text", "text": "Left-Center"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_2_64}"}},
            {"type": "text", "text": "Right-Center"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_3_64}"}},
            {"type": "text", "text": "Right"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_4_64}"}},         
        ]
    return look_around
