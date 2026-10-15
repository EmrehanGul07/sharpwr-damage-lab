import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_content import CONTENT, validate  # noqa: E402


def champ(**over):
    data = {
        "schema": "sharpwr.champion/1", "id": "orig.test", "display_name": "Test",
        "ip": "original", "shippable": True,
        "stats": {"base_ad": {"value": "55", "status": "original_design", "source": "design doc"}},
        "abilities": {},
    }
    data.update(over)
    return data


class ValidateContent(unittest.TestCase):
    def run_with(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, data in files.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(json.dumps(data))
            return validate(root)

    def test_repository_content_is_valid(self):
        self.assertEqual(validate(CONTENT), [])

    def test_original_champion_ok(self):
        self.assertEqual(self.run_with({"champions/t.champion.json": champ()}), [])

    def test_invented_value_without_source_rejected(self):
        bad = champ(stats={"base_ad": {"value": "55", "status": "original_design", "source": ""}})
        self.assertTrue(any("missing source" in e for e in self.run_with({"champions/t.json": bad})))

    def test_unresolved_must_be_null(self):
        bad = champ(stats={"x": {"value": "1", "status": "unresolved", "source": "s"}})
        self.assertTrue(any("must have value null" in e for e in self.run_with({"c/t.json": bad})))

    def test_riot_numbers_cannot_leak_into_original_content(self):
        bad = champ(stats={"x": {"value": "60", "status": "wr_wiki", "source": "wiki"}})
        self.assertTrue(any("not allowed" in e for e in self.run_with({"c/t.json": bad})))

    def test_reference_content_cannot_be_rostered(self):
        ref = champ(id="ref.x", ip="riot-reference", shippable=False,
                    stats={"x": {"value": "60", "status": "wr_wiki", "source": "wiki"}})
        roster = {"schema": "sharpwr.roster/1", "distribution": "public", "champions": ["ref.x"]}
        errors = self.run_with({"reference-riot/champions/x.json": ref, "rosters/r.json": roster})
        self.assertTrue(any("not shippable" in e for e in errors), errors)
        personal = dict(roster, distribution="personal")
        self.assertEqual(self.run_with({"reference-riot/champions/x.json": ref, "rosters/r.json": personal}), [])
        missing = {"schema": "sharpwr.roster/1", "champions": []}
        self.assertTrue(any("distribution" in e for e in self.run_with({"rosters/r.json": missing})))

    def test_reference_area_requires_reference_ip(self):
        errors = self.run_with({"reference-riot/champions/x.json": champ()})
        self.assertTrue(any("R4" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
