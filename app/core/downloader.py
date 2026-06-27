import os
import time

import requests

from app.core.config import SOURCES

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "OQB-BadStick-Mac/1.0",
}


class Downloader:
    def get_latest_release_url(self, api_url: str, asset_pattern: str) -> str:
        print(f"[DEBUG] get_latest_release_url api={api_url} pattern={asset_pattern}")
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=15)
            print(f"[DEBUG]   → HTTP {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                assets = [a["name"] for a in data.get("assets", [])]
                print(f"[DEBUG]   → assets disponibles: {assets}")
                for asset in data.get("assets", []):
                    if asset["name"].endswith(asset_pattern):
                        print(f"[DEBUG]   → match: {asset['browser_download_url']}")
                        return asset["browser_download_url"]
                print(f"[DEBUG]   → ningún asset termina en '{asset_pattern}'")
            return None
        except Exception as exc:
            print(f"[DEBUG]   → excepción: {exc}")
            return None

    def download_file(self, url: str, dest_path: str, progress_callback) -> bool:
        print(f"[DEBUG] download_file url={url}")
        """
        progress_callback(downloaded_bytes, total_bytes, speed_bps)
        speed_bps is a rolling average over the last second of data.
        """
        try:
            response = requests.get(
                url,
                stream=True,
                timeout=30,
                headers={"User-Agent": "OQB-BadStick-Mac/1.0"},
            )
            if response.status_code != 200:
                return False

            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 65536  # 64 KB

            # Speed tracking
            window_start = time.monotonic()
            window_bytes = 0
            speed_bps = 0.0

            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        n = len(chunk)
                        downloaded += n
                        window_bytes += n

                        now = time.monotonic()
                        elapsed = now - window_start
                        if elapsed >= 0.5:
                            speed_bps = window_bytes / elapsed
                            window_start = now
                            window_bytes = 0

                        progress_callback(downloaded, total, speed_bps)

            print(f"[DEBUG]   → download_file OK ({downloaded} bytes)")
            return True
        except Exception as exc:
            print(f"[DEBUG]   → download_file EXCEPCIÓN: {exc}")
            return False
