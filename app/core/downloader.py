import os

import requests

from app.core.config import SOURCES

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "OQB-BadStick-Mac/1.0",
}


class Downloader:
    def get_latest_release_url(self, api_url: str, asset_pattern: str) -> str:
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for asset in data.get("assets", []):
                    if asset["name"].endswith(asset_pattern):
                        return asset["browser_download_url"]
            return None
        except Exception:
            return None

    def download_file(self, url: str, dest_path: str, progress_callback) -> bool:
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

            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_callback(downloaded, total)
            return True
        except Exception:
            return False

    def download_all(
        self,
        sources: list,
        dest_dir: str,
        progress_callback,
        log_callback,
    ) -> dict:
        os.makedirs(dest_dir, exist_ok=True)
        results = {}

        for key in sources:
            if key not in SOURCES:
                continue
            source = SOURCES[key]
            name = source["name"]
            log_callback(f"Descargando {name}...")

            url = None
            if "api_url" in source:
                url = self.get_latest_release_url(
                    source["api_url"], source["asset_pattern"]
                )
                if url:
                    log_callback("  → Usando release más reciente")
                else:
                    log_callback("  → API no disponible, usando URL de respaldo")
                    url = source.get("fallback_url")
            elif "direct_url" in source:
                url = source["direct_url"]

            if not url:
                log_callback(f"  ❌ No se pudo obtener URL para {name}")
                continue

            dest_path = os.path.join(dest_dir, f"{key}.zip")

            def _make_cb(src_name):
                def cb(dl, total):
                    progress_callback(src_name, dl / total if total else 0)
                return cb

            success = self.download_file(url, dest_path, _make_cb(name))
            if success:
                log_callback(f"  ✓ {name} descargado")
                results[key] = dest_path
            else:
                log_callback(f"  ❌ Error descargando {name}")

        return results
