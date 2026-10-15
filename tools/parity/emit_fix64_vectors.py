"""Emit bit-exact Q32.32 test vectors for the C# Fix64 implementation.

The C# tests (game/sim/tests/Numerics/Fix64VectorTests.cs) must reproduce every `raw` exactly.
Usage: python -I tools/parity/emit_fix64_vectors.py [--check]
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from fixed_point_model import Fix, fsqrt, growth_units, seconds_to_micros  # noqa: E402

OUT = ROOT / "game" / "parity" / "fixtures" / "fix64-vectors-v1.json"
TEXTS = ("0", "1", "-1", "0.5", "-0.5", "0.0175", "0.7025", "1.25", "-3.75", "0.658",
         "101.325", "2327.92", "0.2279635167173252", "2800", "1e-9", "-1e-9", "2147483647.5")


def build():
    parse = [{"text": t, "raw": Fix.parse(t).raw} for t in TEXTS]
    pairs = [(a, b) for a in TEXTS[:14] for b in ("1.5", "-0.658", "100", "0.0175", "3")]
    mul = [{"a": a, "b": b, "raw": (Fix.parse(a) * Fix.parse(b)).raw} for a, b in pairs]
    div = [{"a": a, "b": b, "raw": (Fix.parse(a) / Fix.parse(b)).raw} for a, b in pairs]
    growth = [{"level": lvl, "raw": growth_units(lvl).raw} for lvl in range(1, 16)]
    micros = [{"seconds": t, "micros": seconds_to_micros(Fix.parse(t))}
              for t in ("0.2279635167173252", "0.1875", "1.519756838905775", "-0.0000005")]
    sqrt = [{"text": t, "raw": fsqrt(Fix.parse(t)).raw}
            for t in ("0", "1e-9", "0.0175", "0.25", "2", "100", "525", "275625", "440000000", "2147483647")]
    return {"schema": "sharpwr.fix64-vectors/1", "frac_bits": 32, "parse": parse, "mul": mul,
            "div": div, "growth_units": growth, "seconds_to_micros": micros, "sqrt": sqrt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    text = json.dumps(build(), indent=1) + "\n"
    if ap.parse_args().check:
        ok = OUT.exists() and OUT.read_text() == text
        print("fix64 vectors up to date" if ok else f"{OUT} is stale", file=sys.stdout if ok else sys.stderr)
        return 0 if ok else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
