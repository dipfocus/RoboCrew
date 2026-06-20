# EggoBot 使用指南

本目录提供 EggoBot 接入 RoboCrew 的最小示例。示例会使用前置摄像头获取画面，用 LLM 规划动作，并通过 Feetech 舵机总线控制 EggoBot 前进、后退和转向。

## 前置条件

- 一台已接好摄像头、主控板和舵机总线的 EggoBot。
- Linux 环境，且系统中可用 `udevadm`。
- Python 3.10 或更高版本。
- 可访问所选 LLM 的 API。默认示例使用 `google_genai:gemini-3-flash-preview`，通常需要配置 `GOOGLE_API_KEY`。

## 安装

在本仓库源码中使用可编辑安装：

```bash
pip install -e .
```

## 配置 USB 设备别名

EggoBot 示例默认使用以下设备路径：

| 设备 | 默认别名 | 示例真实路径 |
| --- | --- | --- |
| 前置摄像头 | `/dev/camera_center` | `/dev/video0` |
| EggoBot 舵机控制板 | `/dev/eggobot` | `/dev/ttyACM0` |
| 主麦克风 | `/dev/mic_main` | `/dev/snd/controlC*` |

推荐先运行自动配置脚本。它会引导你逐个插入设备，并把 udev 规则写入 `/etc/udev/rules.d/99-eggobot.rules`：

```bash
eggobot-setup-usb-modules
```

脚本流程：

1. 根据提示先断开所有 EggoBot 相关 USB 设备。
2. 按顺序插入 `camera_center`、`eggobot`、`mic_main` 对应设备。
3. 如果某个设备暂时不需要，输入 `s` 跳过。
4. 默认设备配置完成后，可输入 `a` 增加更多自定义别名。

如果不想让脚本顺带设置 Wi-Fi 优先级：

```bash
eggobot-setup-usb-modules --no-wifi-priority
```

配置完成后，可以检查别名是否存在：

```bash
ls -l /dev/camera_center /dev/eggobot /dev/mic_main
```

## 配置 LLM API Key

最小示例默认使用 Gemini 模型。可以在当前 shell 中设置：

```bash
export GOOGLE_API_KEY="your-api-key"
```

也可以在项目根目录创建 `.env` 文件：

```bash
GOOGLE_API_KEY=your-api-key
```

RoboCrew 会自动读取 `.env`。

## 运行最小示例

确认 USB 别名和 API Key 都准备好后，运行：

```bash
python examples/eggobot/0_eggobot_bare_minimum.py
```

示例代码会：

1. 打开 `/dev/camera_center` 摄像头。
2. 连接 `/dev/eggobot` 舵机控制板。
3. 创建 `move_forward`、`turn_left`、`turn_right` 三个工具。
4. 初始化 `EggoBotAgent`。
5. 设置任务 `Approach a human.` 并开始执行。

停止程序时，在终端按 `Ctrl+C`。程序退出前会断开舵机控制器连接。

## 最小示例代码

```python
from robocrew.core.camera import RobotCamera
from robocrew.robots.EggoBot.eggo_bot_agent import EggoBotAgent
from robocrew.robots.EggoBot.tools import create_move_forward, create_turn_right, create_turn_left
from robocrew.robots.EggoBot.servo_controller import ServoController

main_camera = RobotCamera("/dev/camera_center")

eggobot_usb = "/dev/eggobot"
servo_controller = ServoController(usb_port=eggobot_usb)

move_forward = create_move_forward(servo_controller)
turn_left = create_turn_left(servo_controller)
turn_right = create_turn_right(servo_controller)

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
```

## 可用运动工具

`robocrew.robots.EggoBot.tools` 中提供了多个可交给 Agent 调用的工具：

| 工具工厂函数 | Agent 工具名 | 作用 |
| --- | --- | --- |
| `create_move_forward` | `move_forward` | 按米数前进；传入负数时后退 |
| `create_move_backward` | `move_backward` | 按米数后退 |
| `create_turn_left` | `turn_left` | 按角度左转 |
| `create_turn_right` | `turn_right` | 按角度右转 |
| `create_strafe_left` | `strafe_left` | 按米数左平移 |
| `create_strafe_right` | `strafe_right` | 按米数右平移 |
| `create_look_around` | `look_around` | 转动头部并采集多方向图像 |
| `create_go_to_precision_mode` | `go_to_precision_mode` | 切换到精细移动视角 |
| `create_go_to_normal_mode` | `go_to_normal_mode` | 恢复普通移动视角 |

如果要让 Agent 使用更多能力，把对应工具加入 `tools` 列表即可。例如增加环顾能力：

```python
from robocrew.robots.EggoBot.tools import create_look_around

look_around = create_look_around(servo_controller, main_camera)

agent = EggoBotAgent(
    model="google_genai:gemini-3-flash-preview",
    tools=[
        move_forward,
        turn_left,
        turn_right,
        look_around,
    ],
    main_camera=main_camera,
    servo_controler=servo_controller,
)
```

## 设备与运动参数

EggoBot 的舵机控制器在 `ServoController` 中定义：

- 轮子舵机 ID：`7`、`8`、`9`
- 头部 yaw 舵机 ID：`10`
- 头部 pitch 舵机 ID：`11`
- 默认线速度估计：`0.25 m/s`
- 默认角速度估计：`100 deg/s`
- 头部 yaw 限制：`-120` 到 `120` 度
- 头部 pitch 限制：`0` 到 `85` 度

如果机器人实际运动距离或角度偏差较大，需要在 `src/robocrew/robots/EggoBot/servo_controller.py` 中校准 `LINEAR_MPS`、`ANGULAR_DPS` 或舵机方向映射。

## 常见问题

### 找不到 `/dev/eggobot`

先确认设备是否被系统识别：

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

如果真实设备存在但别名不存在，重新运行：

```bash
eggobot-setup-usb-modules
```

### 找不到 `/dev/camera_center`

检查摄像头：

```bash
ls /dev/video*
ls -l /dev/v4l/by-path/
```

然后重新运行 USB 配置脚本，把摄像头绑定到 `camera_center`。

### 普通用户没有设备权限

udev 规则默认使用 `MODE="0660"` 和 `GROUP="dialout"`。如果当前用户不在 `dialout` 组，可执行：

```bash
sudo usermod -aG dialout $USER
```

执行后需要重新登录终端会话。

### Agent 没有响应或模型报错

检查 API Key 是否已加载：

```bash
echo $GOOGLE_API_KEY
```

如果使用 `.env`，请确认程序从项目根目录启动，或者 `.env` 位于 `python-dotenv` 能找到的位置。
