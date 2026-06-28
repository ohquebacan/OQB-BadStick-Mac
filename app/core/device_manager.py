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

    # Names that are never real USB drives
    _NAME_BLOCKLIST = {
        "oqb badstick mac",
        "macintosh hd",
        "time machine",
    }
    _NAME_BLOCKLIST_PREFIXES = ("disk image",)
    _MIN_USB_BYTES = 256 * 1024 * 1024   # 256 MB

    def _is_fake_volume(self, name: str, mount_point: str, size_bytes: int) -> bool:
        """Return True if this entry should be excluded from the USB list."""
        name_l = (name or "").lower()
        # Known fake / system names
        if name_l in self._NAME_BLOCKLIST:
            return True
        if any(name_l.startswith(p) for p in self._NAME_BLOCKLIST_PREFIXES):
            return True
        # Mount point inside a .app bundle (PyInstaller virtual disk)
        if ".app" in (mount_point or ""):
            return True
        # Too small to be a real USB drive
        if size_bytes and size_bytes < self._MIN_USB_BYTES:
            return True
        return False

    def _get_bus_protocol_macos(self, identifier: str) -> str:
        """Return the BusProtocol string from diskutil info, or '' on error."""
        try:
            result = subprocess.run(
                ["diskutil", "info", "-plist", f"/dev/{identifier}"],
                capture_output=True, timeout=8,
            )
            if result.returncode == 0:
                info = plistlib.loads(result.stdout)
                return info.get("BusProtocol", "") or ""
        except Exception:
            pass
        return ""

    def _list_usb_macos(self) -> list:
        try:
            # 'external' limits output to removable/external disks only
            result = subprocess.run(
                ["diskutil", "list", "-plist", "external"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            plist_data = plistlib.loads(result.stdout)
            # AllDisksAndPartitions carries size + partition details inline
            all_disks = plist_data.get("AllDisksAndPartitions", [])
            devices = []

            for disk_entry in all_disks:
                identifier = disk_entry.get("DeviceIdentifier", "")
                if not identifier:
                    continue

                size_bytes = disk_entry.get("Size", 0)
                partitions = disk_entry.get("Partitions", [])

                name = ""
                mount_point = ""

                # Walk partitions; skip EFI, take first real volume info found
                for part in partitions:
                    if part.get("Content", "").upper() == "EFI":
                        continue
                    if not name:
                        name = part.get("VolumeName", "")
                    if not mount_point:
                        mount_point = part.get("MountPoint", "")
                    if name and mount_point:
                        break

                # Fallback: query the partition device directly (diskNs1)
                if not name or not mount_point:
                    part_id = f"{identifier}s1"
                    fallback = self._get_disk_info_macos(part_id)
                    if fallback:
                        if not name:
                            name = fallback.get("name", "")
                        if not mount_point:
                            mount_point = fallback.get("mount_point", "")

                # ── Filter: reject fake / system volumes ──────────────────
                if self._is_fake_volume(name, mount_point, size_bytes):
                    continue

                # ── Filter: verify USB bus protocol ───────────────────────
                protocol = self._get_bus_protocol_macos(identifier).lower()
                if protocol and "usb" not in protocol and "disk image" not in protocol:
                    # Non-USB protocol (e.g. Thunderbolt, PCIe) — skip
                    # Allow empty protocol through since some USB hubs omit it
                    continue

                devices.append({
                    "name": name or identifier,
                    "identifier": identifier,
                    "size": self._format_size(size_bytes),
                    "mount_point": mount_point,
                    "size_bytes": size_bytes,
                })

            return devices
        except Exception:
            return []

    def get_raw_diskutil_info(self) -> str:
        """Raw human-readable output of 'diskutil list external' for diagnostics."""
        try:
            result = subprocess.run(
                ["diskutil", "list", "external"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = (result.stdout or "").strip()
            return output if output else "(ningún disco externo detectado por diskutil)"
        except Exception as e:
            return f"Error al ejecutar diskutil: {e}"

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
        command = f"diskutil eraseDisk FAT32 OQB360USB MBRFormat /dev/{identifier}"
        try:
            result = subprocess.run(
                ["osascript", "-e",
                 f'do shell script "{command}" with administrator privileges'],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                stderr = result.stderr or ""
                # osascript error -128 = "User canceled" (native password dialog)
                if "-128" in stderr or "canceled" in stderr.lower() or "cancelled" in stderr.lower():
                    callback("Operación cancelada por el usuario")
                else:
                    for line in (result.stdout + stderr).splitlines():
                        line = line.strip()
                        if line:
                            callback(line)
                return False, ""

            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    callback(line)

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

    def get_filesystem_info(self, identifier: str) -> dict:
        """Returns {"fs_type": str, "size_bytes": int} for the first real partition."""
        if self.system == "Darwin":
            return self._get_fs_macos(identifier)
        elif self.system == "Linux":
            return self._get_fs_linux(identifier)
        return {"fs_type": "unknown", "size_bytes": 0}

    def _get_fs_macos(self, identifier: str) -> dict:
        _FS_MAP = {
            "WINDOWS_FAT_32": "FAT32",
            "WINDOWS_FAT_16": "FAT16",
            "MICROSOFT BASIC DATA": "ExFAT/NTFS",
            "APPLE_HFS": "HFS+",
            "APPLE_APFS": "APFS",
            "FREE SPACE": "Sin formato",
            "": "Sin formato",
        }
        try:
            result = subprocess.run(
                ["diskutil", "list", "-plist", "external"],
                capture_output=True, timeout=10,
            )
            if result.returncode != 0:
                return {"fs_type": "?", "size_bytes": 0}
            for disk in plistlib.loads(result.stdout).get("AllDisksAndPartitions", []):
                if disk.get("DeviceIdentifier") != identifier:
                    continue
                for part in disk.get("Partitions", []):
                    content = part.get("Content", "").upper().strip()
                    if content == "EFI":
                        continue
                    return {
                        "fs_type": _FS_MAP.get(content, content or "Sin formato"),
                        "size_bytes": disk.get("Size", 0),
                    }
            return {"fs_type": "Sin formato", "size_bytes": 0}
        except Exception:
            return {"fs_type": "?", "size_bytes": 0}

    def _get_fs_linux(self, identifier: str) -> dict:
        try:
            result = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,FSTYPE,SIZE", f"/dev/{identifier}"],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for dev in data.get("blockdevices", []):
                    for child in dev.get("children", []):
                        fs = (child.get("fstype") or "Sin formato").upper()
                        return {"fs_type": fs, "size_bytes": 0}
        except Exception:
            pass
        return {"fs_type": "?", "size_bytes": 0}

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "? GB"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"


def scan_usb_installs(usb_path: str, catalog: dict) -> set:
    """Detecta qué items del catalog están instalados en el USB."""
    installed = set()
    for key, entry in catalog.items():
        dest = entry.get("dest", "")
        if not dest:
            continue
        full = os.path.join(usb_path, *dest.replace("\\", "/").split("/"))
        try:
            if os.path.isdir(full) and any(os.scandir(full)):
                installed.add(key)
        except PermissionError:
            pass
    xex_content = os.path.join(usb_path, "Content", "0000000000000000", "C0DE9999")
    if os.path.isdir(xex_content):
        installed.add("xexmenu")
    return installed
