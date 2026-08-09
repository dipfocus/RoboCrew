"""Lightweight wheel and head helpers for the EggoBot."""

from __future__ import annotations

import time
from typing import Dict, Literal

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode


DEFAULT_SPEED = 10_000
LINEAR_MPS = 0.25
ANGULAR_DPS = 100.0

ACTION_MAP = {
    "forward": {7: 1.0, 8: 0.0, 9: -1.0},
    "backward": {7: -1.0, 8: 0.0, 9: 1.0},
    "strafe_left": {7: -0.15, 8: 1.0, 9: -0.15},
    "strafe_right": {7: 0.15, 8: -1.0, 9: 0.15},
    "turn_left": {7: 1.0, 8: 1.0, 9: 1.0},
    "turn_right": {7: -1.0, 8: -1.0, 9: -1.0},
}

HEAD_SERVO_MAP = {"yaw": 10, "pitch": 11}


HEAD_YAW_LIMIT_DEG = (-120.0, 120.0)
HEAD_PITCH_LIMIT_DEG = (0.0, 90.0)


def _clamp(value: float, bounds: tuple[float, float]) -> float:
    low, high = bounds
    return max(low, min(high, float(value)))


def _default_calibration(ids: tuple[int, ...]) -> Dict[int, MotorCalibration]:
    return {
        sid: MotorCalibration(
            id=sid,
            drive_mode=0,
            homing_offset=0,
            range_min=0,
            range_max=4095,
        )
        for sid in ids
    }


class ServoController:
    """Minimal wheel and head controller."""

    def __init__(
        self,
        usb_port: str,
        *,
        speed: int = DEFAULT_SPEED,
    ) -> None:
        self.usb_port = usb_port
        self.speed = speed
        self._wheel_ids = tuple(list(ACTION_MAP.values())[0].keys())
        self._head_ids = tuple(HEAD_SERVO_MAP.values())

        self.servo_bus = FeetechMotorsBus(
            port=usb_port,
            motors={
                7: Motor(7, "sts3215", MotorNormMode.RANGE_M100_100),
                8: Motor(8, "sts3215", MotorNormMode.RANGE_M100_100),
                9: Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
                HEAD_SERVO_MAP["yaw"]: Motor(HEAD_SERVO_MAP["yaw"], "sts3215", MotorNormMode.DEGREES),
                HEAD_SERVO_MAP["pitch"]: Motor(HEAD_SERVO_MAP["pitch"], "sts3215", MotorNormMode.DEGREES),
            },
            calibration=_default_calibration(self._wheel_ids + self._head_ids),
        )
        self.servo_bus.connect()
        self.apply_wheel_modes()
        self.apply_head_modes()
        self._head_positions = {HEAD_SERVO_MAP["yaw"]: 0.0, HEAD_SERVO_MAP["pitch"]: 0.0}


    def _wheels_stop(self) -> None:
        if not hasattr(self, "servo_bus"):
            print("Warning: servo bus not initialized, cannot stop wheels.")
            return
        payload = {wid: 0 for wid in self._wheel_ids}
        self.servo_bus.sync_write("Goal_Velocity", payload)

    def _wheels_run(self, action: str, duration: float) -> None:
        if duration > 0:
            multipliers = ACTION_MAP[action]
            payload = {wid: int(self.speed * factor) for wid, factor in multipliers.items()}
            self.servo_bus.sync_write("Goal_Velocity", payload)
            time.sleep(duration)
            payload = {wid: 0 for wid in self._wheel_ids}
            self.servo_bus.sync_write("Goal_Velocity", payload)

    def go_forward(self, meters: float) -> None:
        self._wheels_run("forward", float(meters) / LINEAR_MPS)

    def go_backward(self, meters: float) -> None:
        self._wheels_run("backward", float(meters) / LINEAR_MPS)

    def turn_left(self, degrees: float) -> None:
        self._wheels_run("turn_left", float(degrees) / ANGULAR_DPS)

    def turn_right(self, degrees: float) -> None:
        self._wheels_run("turn_right", float(degrees) / ANGULAR_DPS)
    
    def strafe_left(self, meters: float) -> None:
        self._wheels_run("strafe_left", float(meters) / LINEAR_MPS)
    
    def strafe_right(self, meters: float) -> None:
        self._wheels_run("strafe_right", float(meters) / LINEAR_MPS)

    def turn_head_to_vla_position(self, pitch_deg=45) -> str:
        self.turn_head_pitch(pitch_deg)
        self.turn_head_yaw(0)
        time.sleep(0.9)

    def reset_head_position(self) -> str:
        self.turn_head_pitch(45)
        self.turn_head_yaw(0)
        time.sleep(0.9)

    def apply_wheel_modes(self) -> None:
        for wid in self._wheel_ids:
            self.servo_bus.write("Operating_Mode", wid, OperatingMode.VELOCITY.value)

        self.servo_bus.enable_torque(list(self._wheel_ids))

    def _set_position_mode(self, bus: FeetechMotorsBus, ids: tuple[int, ...]) -> None:
        for sid in ids:
            bus.write("Operating_Mode", sid, OperatingMode.POSITION.value)
        bus.enable_torque(list(ids))

    def apply_head_modes(self) -> None:
        self._set_position_mode(self.servo_bus, self._head_ids)

    def _set_bus_torque(self, bus: FeetechMotorsBus, ids: tuple[int, ...], enabled: bool) -> None:
        fn = getattr(bus, "enable_torque" if enabled else "disable_torque", None)
        if fn:
            fn(list(ids))
            return
        for sid in ids:
            bus.write("Torque_Enable", sid, int(enabled))

    def _set_torque(self, enabled: bool, target: Literal["all", "wheels", "head"] = "all") -> None:
        bus = getattr(self, "servo_bus", None)
        groups = {
            "wheels": ((bus, self._wheel_ids),),
            "head": ((bus, self._head_ids),),
        }
        selected = ("wheels", "head") if target == "all" else (target,)
        for key in selected:
            for bus, ids in groups[key]:
                if bus:
                    self._set_bus_torque(bus, ids, enabled)

    def enable_torque(self, target: Literal["all", "wheels", "head"] = "all") -> None:
        """Enable torque for all/wheels/head."""
        self._set_torque(True, target)

    def disable_torque(self, target: Literal["all", "wheels", "head"] = "all") -> None:
        """Disable torque for all/wheels/head."""
        self._set_torque(False, target)

    def turn_head_yaw(self, degrees: float) -> Dict[int, float]:
        payload = {HEAD_SERVO_MAP["yaw"]: _clamp(degrees, HEAD_YAW_LIMIT_DEG)}
        self.servo_bus.sync_write("Goal_Position", payload)
        self._head_positions.update(payload)

    def turn_head_pitch(self, degrees: float) -> Dict[int, float]:
        payload = {HEAD_SERVO_MAP["pitch"]: _clamp(degrees, HEAD_PITCH_LIMIT_DEG)}
        self.servo_bus.sync_write("Goal_Position", payload)
        self._head_positions.update(payload)

    def disconnect(self) -> None:
        if hasattr(self, 'servo_bus'):
            self._wheels_stop()
            time.sleep(0.5)
            self.servo_bus.disconnect()
