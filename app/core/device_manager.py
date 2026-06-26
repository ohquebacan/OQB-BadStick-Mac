import json
import os
import platform
import plistlib
import subprocess
import time


class DeviceManager:
    def __init__(self):
        self.system = platform.system()

    def list_usb_devices(self) -> list:
        if self.system == "Darwin":
            return self._list_usb_macos()
        elif self.system == "Linux":
            return self._list_usb_linux()
        return []

    def _list_usb_macos(self) -> list:
        try:
            result = subprocess.run(
                ["diskutil", "list", "-plist"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            plist_data = plistlib.loads(result.stdout)
            external_ids = plist_data.get("ExternalDisks", [])
            devices = []
            for disk_id in external_ids:
                info = self._get_disk_info_macos(disk_id)
                if info:
                    devices.append(info)
            return devices
        except Exception:
            return []

    def _get_disk_info_macos(self, identifier: str) -> dict:
        try:
            result = subprocess.run(
                ["diskutil", "info", "-plist", f"/dev/{identifier}"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None

            info = plistlib.loads(result.stdout)
            size_bytes = info.get("TotalSize", 0)
            volume_name = info.get("VolumeName", "") or identifier
            mount_point = info.get("MountPoint", "")

            return {
                "name": volume_name,
                "identifier": identifier,
                "size": self._format_size(size_bytes),
                "mount_point": mount_point,
                "size_bytes": size_bytes,
            }
        except Exception:
            return None

    def _list_usb_linux(self) -> list:
        try:
            result = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,LABEL,HOTPLUG"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            devices = []
            for device in data.get("blockdevices", []):
                hotplug = device.get("hotplug")
                if hotplug not in (True, "1", 1) or device.get("type") != "disk":
                    continue

                name = device.get("name", "")
                label = device.get("label") or name
                size = device.get("size", "?")
                mount_point = device.get("mountpoint", "") or ""

                if not mount_point:
                    for child in device.get("children", []):
                        if child.get("mountpoint"):
                            mount_point = child["mountpoint"]
                            if not device.get("label"):
                                label = child.get("label") or label
                            break

                devices.append({
                    "name": label,
                    "identifier": name,
                    "size": size,
                    "mount_point": mount_point,
                    "size_bytes": 0,
                })
            return devices
        except Exception:
            return []

    def format_device(self, identifier: str, callback) -> tuple:
        """Returns (success: bool, mount_point: str)"""
        if self.system == "Darwin":
            return self._format_macos(identifier, callback)
        elif self.system == "Linux":
            return self._format_linux(identifier, callback)
        return False, ""

    def _format_macos(self, identifier: str, callback) -> tuple:
        cmd = (
            f"diskutil eraseDisk FAT32 OQB360USB MBRFormat /dev/{identifier}"
        )
        script = f'do shell script "{cmd}" with administrator privileges'
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            for line in (result.stdout + result.stderr).splitlines():
                line = line.strip()
                if line:
                    callback(line)

            if result.returncode != 0:
                return False, ""

            callback("Esperando montaje del volumen...")
            time.sleep(2)
            mount_point = self.get_mount_point(identifier)
            return True, mount_point

        except subprocess.TimeoutExpired:
            callback("Error: timeout al formatear")
            return False, ""
        except Exception as e:
            callback(f"Error: {e}")
            return False, ""

    def _format_linux(self, identifier: str, callback) -> tuple:
        try:
            process = subprocess.Popen(
                ["sudo", "mkfs.vfat", "-F", "32", "-n", "OQB360USB", f"/dev/{identifier}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in process.stdout:
                line = line.strip()
                if line:
                    callback(line)
            process.wait(timeout=120)
            if process.returncode != 0:
                return False, ""
            time.sleep(1)
            mount_point = self.get_mount_point(identifier)
            return True, mount_point
        except Exception as e:
            callback(f"Error: {e}")
            return False, ""

    def get_mount_point(self, identifier: str) -> str:
        if self.system == "Darwin":
            try:
                result = subprocess.run(
                    ["diskutil", "info", "-plist", f"/dev/{identifier}"],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    info = plistlib.loads(result.stdout)
                    mp = info.get("MountPoint", "")
                    if mp:
                        return mp
            except Exception:
                pass
            # Fallback: check standard Volumes path
            vol_path = "/Volumes/OQB360USB"
            if os.path.exists(vol_path):
                return vol_path
            return ""

        elif self.system == "Linux":
            try:
                result = subprocess.run(
                    ["lsblk", "-J", "-o", "NAME,MOUNTPOINT", f"/dev/{identifier}"],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for dev in data.get("blockdevices", []):
                        if dev.get("mountpoint"):
                            return dev["mountpoint"]
                        for child in dev.get("children", []):
                            if child.get("mountpoint"):
                                return child["mountpoint"]
            except Exception:
                pass
            return ""

        return ""

    def eject_device(self, identifier: str):
        try:
            if self.system == "Darwin":
                subprocess.run(
                    ["diskutil", "eject", f"/dev/{identifier}"],
                    capture_output=True,
                    timeout=30,
                )
            elif self.system == "Linux":
                subprocess.run(
                    ["udisksctl", "power-off", "-b", f"/dev/{identifier}"],
                    capture_output=True,
                    timeout=30,
                )
        except Exception:
            pass

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "? GB"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
