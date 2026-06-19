"""
The simplest example of agent that can drive EggoBot.
"""

from robocrew.core.camera import RobotCamera
from robocrew.robots.EggoBot.eggo_bot_agent import EggoBotAgent
from robocrew.robots.EggoBot.tools import create_move_forward, create_turn_right, create_turn_left
from robocrew.robots.EggoBot.servo_controller import ServoController

# set up main camera
main_camera = RobotCamera("/dev/camera_center") # camera usb port Eg: /dev/video0

#set up servo controller
eggobot_usb = "/dev/eggobot"    # provide your EggoBot USB port. Eg: /dev/ttyACM0
servo_controller = ServoController(usb_port=eggobot_usb)

#set up tools
move_forward = create_move_forward(servo_controller)
turn_left = create_turn_left(servo_controller)
turn_right = create_turn_right(servo_controller)

# init agent
agent = EggoBotAgent(
    model="google_genai:gemini-3-flash-preview",
    tools=[
        move_forward,
        turn_left,
        turn_right,
    ],
    main_camera=main_camera,
    servo_controler=servo_controller,
)

agent.task = "Approach a human."

agent.go()
