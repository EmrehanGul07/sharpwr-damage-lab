"""Download bundled Riot icons that are listed in data/riot/icons.json but missing locally.

Runs in GitHub Actions (.github/workflows/fetch-riot-icons.yml), which commits the files.
Every download must be a PNG, WebP or JPEG image under 1 MB; the script exits non-zero
when any listed icon is still missing afterwards.
"""

import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sharpwr.icons import KINDS, manifest

USER_AGENT = "SharpWR icon sync (+https://github.com/EmrehanGul07/sharpwr-damage-lab)"
MAX_BYTES = 1_000_000


def is_image(data):
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        or data.startswith(b"\xff\xd8\xff")
    )


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(MAX_BYTES + 1)
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def main():
    fetched, failed = 0, []
    for kind in KINDS:
        for name, entry in manifest()[kind].items():
            path = ROOT / entry["path"]
            if path.is_file():
                continue
            if not entry["source"]:
                failed.append(f"{kind}/{name}: no source URL")
                continue
            try:
                data = download(entry["source"])
            except OSError as error:
                failed.append(f"{kind}/{name}: {error}")
                continue
            if len(data) > MAX_BYTES or not is_image(data):
                failed.append(f"{kind}/{name}: not an image under 1 MB")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            fetched += 1
            print("fetched", entry["path"])
    print(f"{fetched} fetched, {len(failed)} missing")
    for line in failed:
        print("MISSING", line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
