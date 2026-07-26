#!/usr/bin/env python3

import glob
import os
import subprocess
import sys
from pathlib import Path


MODE = os.environ.get("MODE", "0660")
GROUP = os.environ.get("GROUP", "dialout")
EXTRA_SYMLINK_PREFIX = os.environ.get("SYMLINK_PREFIX", "eggobot")
DEFAULT_ALIASES = {
	"video4linux": (os.environ.get("CAMERA_ALIAS", "camera_center"),),
	"tty": (os.environ.get("EGGOBOT_ALIAS", "eggobot"),),
	"sound": (os.environ.get("MIC_ALIAS", "mic_main"),),
}
# RealSense infrared nodes can expose UYVY, so it is not an RGB discriminator.
REALSENSE_RGB_FORMATS = {"YUYV", "YUY2", "MJPG", "RGB3", "BGR3"}


def udevadm(args):
	try:
		out = subprocess.run(
			["udevadm", *args],
			check=False,
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			text=True,
		)
	except FileNotFoundError as exc:
		raise SystemExit("udevadm binary is required to run this script") from exc
	return out.stdout.strip()


def get_props(node):
	props = {}
	for line in udevadm(["info", "-q", "property", "-n", node]).splitlines():
		if "=" in line:
			key, value = line.split("=", 1)
			props[key] = value
	return props


def get_camera_index(kernel):
	idx_file = Path("/sys/class/video4linux") / kernel / "index"
	if idx_file.is_file():
		return idx_file.read_text(encoding="ascii", errors="ignore").strip()
	return None


def get_video_formats(node):
	try:
		out = subprocess.run(
			["v4l2-ctl", "-d", node, "--list-formats"],
			check=False,
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			text=True,
		)
	except FileNotFoundError as exc:
		raise SystemExit(
			"v4l2-ctl binary is required to identify RealSense RGB devices"
		) from exc

	formats = set()
	for line in out.stdout.splitlines():
		parts = line.split("'")
		if len(parts) >= 3:
			formats.add(parts[1].strip())
	return formats


def is_realsense(props):
	return any(
		"realsense" in props.get(key, "").lower()
		for key in ("ID_MODEL", "ID_V4L_PRODUCT", "ID_SERIAL")
	)


def scan(pattern, subsystem, devices, serial_counts, camera_ids):
	for device in sorted(glob.glob(pattern)):
		real_device = os.path.realpath(device)
		sysfs_path = udevadm(["info", "-q", "path", "-n", real_device])
		if not sysfs_path:
			continue

		props = get_props(real_device)
		vendor_id = props.get("ID_VENDOR_ID", "").lower()
		if not vendor_id:
			continue
		product_id = props.get("ID_MODEL_ID", "").lower()
		cam_key = f"{vendor_id}:{product_id}"

		if subsystem == "video4linux":
			camera_ids.add(cam_key)
			idx = get_camera_index(os.path.basename(real_device))
			if idx and idx != "0":
				continue
			realsense = is_realsense(props)
			if realsense and not (get_video_formats(real_device) & REALSENSE_RGB_FORMATS):
				continue
		elif cam_key in camera_ids:
			continue
		else:
			realsense = False

		phys_dir = os.path.dirname(os.path.dirname(sysfs_path))
		phys_path = os.path.basename(phys_dir).split(":", 1)[0]
		id_path = props.get("ID_PATH") or phys_path
		serial_short = props.get("ID_SERIAL_SHORT")
		serial = serial_short or props.get("ID_SERIAL") or None

		devices.append(
			{
				"kernel": os.path.basename(real_device),
				"serial": serial,
				"serial_is_short": bool(serial_short),
				"vendor": vendor_id,
				"product": product_id,
				"id_path": id_path,
				"phys": phys_path,
				"subsystem": subsystem,
				"is_realsense": realsense,
			}
		)

		if serial:
			serial_counts[serial] = serial_counts.get(serial, 0) + 1


def get_link(dev, alias_indexes):
	subsystem = dev["subsystem"]
	index = alias_indexes.get(subsystem, 0)
	alias_indexes[subsystem] = index + 1

	aliases = DEFAULT_ALIASES.get(subsystem, ())
	if index < len(aliases):
		return aliases[index]
	return f"{EXTRA_SYMLINK_PREFIX}-{dev['kernel']}"


def emit_rules(devices, serial_counts):
	alias_indexes = {}
	for dev in devices:
		rule = (
			f'SUBSYSTEM=="{dev["subsystem"]}", '
			f'ATTRS{{idVendor}}=="{dev["vendor"]}", '
			f'ATTRS{{idProduct}}=="{dev["product"]}"'
		)

		if dev["subsystem"] == "video4linux":
			rule += ', ATTR{index}=="0"'
			if dev.get("is_realsense"):
				rule += f', ENV{{ID_PATH}}=="{dev["id_path"]}"'

		link = get_link(dev, alias_indexes)
		serial = dev["serial"]

		if serial and serial != "00000000":
			if dev.get("serial_is_short"):
				rule += f', ATTRS{{serial}}=="{serial}"'
			else:
				rule += f', ENV{{ID_SERIAL}}=="{serial}"'
			if serial_counts.get(serial, 0) > 1:
				rule += f', KERNELS=="{dev["phys"]}"'
		else:
			rule += f', KERNELS=="{dev["phys"]}"'

		rule += f', MODE="{MODE}", GROUP="{GROUP}", SYMLINK+="{link}"'
		print()
		print(rule)
		print()


def main():
	devices = []
	serial_counts = {}
	camera_ids = set()
	scan("/dev/v4l/by-path/*", "video4linux", devices, serial_counts, camera_ids)
	scan("/dev/serial/by-path/*", "tty", devices, serial_counts, camera_ids)
	scan("/dev/snd/controlC*", "sound", devices, serial_counts, camera_ids)
	emit_rules(devices, serial_counts)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:  # pragma: no cover - user convenience
		sys.exit(130)
