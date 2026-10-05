"""Every Riot icon the app shows is listed in data/riot/icons.json and bundled under assets/riot/."""

import unittest
from pathlib import Path

from sharpwr import B, F
from sharpwr.champion_database import CHAMPION_DATABASE
from sharpwr.icons import KINDS, manifest
from sharpwr.rune_database import RUNE_DATABASE, RUNE_SLOTS

ROOT = Path(__file__).resolve().parents[1]


def _is_image(data):
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        or data.startswith(b"\xff\xd8\xff")
    )


class LocalIconTests(unittest.TestCase):
    def test_every_record_has_an_icon_entry(self):
        icons = manifest()
        self.assertEqual(set(icons["items"]), set(F))
        self.assertEqual(set(icons["boots"]), set(B))
        self.assertEqual(set(icons["runes"]), set(RUNE_DATABASE))
        self.assertEqual(set(icons["rune_trees"]), set(RUNE_SLOTS))
        self.assertEqual(set(icons["champions"]), set(CHAMPION_DATABASE))

    def test_icons_live_in_the_riot_folder_and_are_images(self):
        for kind in KINDS:
            for name, entry in manifest()[kind].items():
                self.assertTrue(entry["path"].startswith("assets/riot/"), (kind, name))
                path = ROOT / entry["path"]
                # Missing files: run the "Fetch bundled Riot icons" workflow.
                self.assertTrue(path.is_file(), (kind, name))
                self.assertTrue(_is_image(path.read_bytes()[:16]), (kind, name))


if __name__ == "__main__":
    unittest.main()
