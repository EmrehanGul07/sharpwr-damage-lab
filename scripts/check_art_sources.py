"""Exit non-zero when a tracked Blender build signature no longer matches its sources.

The signatures are written by the Blender scripts into the tracked manifests; CI uses
this check to decide whether the Ezreal study and skinned roster must be rebuilt.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def recorded(manifest):
    try:
        return json.loads(manifest.read_text()).get('source_sha256')
    except FileNotFoundError:
        return None


def digest(*sources):
    return hashlib.sha256(b''.join(source.read_bytes() for source in sources)).hexdigest()


def roster_digest():
    """Signature of the v2 skinned roster: the shared toolkit, the exporter, every champion
    study and the art direction they read."""
    v2 = ROOT / 'scripts/marksman_v2'
    return digest(v2 / 'core.py', v2 / 'export_studio.py', *sorted((v2 / 'champions').glob('*.py')), ROOT / 'data/marksman-art-direction.json')


CHECKS = {
    'Ezreal study': (
        ROOT / 'assets/marksman-3d/studies/ezreal-v2/manifest.json',
        digest(ROOT / 'scripts/build_ezreal_study.py'),
    ),
    'Skinned roster': (
        ROOT / 'static/marksman-3d/manifest.json',
        roster_digest(),
    ),
}


def stale():
    return [name for name, (manifest, expected) in CHECKS.items() if recorded(manifest) != expected]


if __name__ == '__main__':
    changed = stale()
    for name in changed:
        print(f'{name}: sources changed since the last Blender build')
    sys.exit(1 if changed else 0)
