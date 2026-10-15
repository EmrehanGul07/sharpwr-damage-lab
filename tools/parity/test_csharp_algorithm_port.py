"""Fuzz the exact algorithm written in Fix64.cs (transcribed line by line with 64-bit masks)
against the reference model. This checks the C# *algorithm* while no .NET SDK is available;
it does not replace compiling and running game/sim/tests (see docs/moba/06-testing.md).
"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixed_point_model import Fix  # noqa: E402

M64 = (1 << 64) - 1
HALF = 1 << 31


def magnitude(v):  # Fix64.Magnitude
    return ((-(v + 1)) & M64) + 1 if v < 0 else v


def apply_sign(mag, negative):  # Fix64.ApplySign
    if negative:
        if mag > (1 << 63):
            raise OverflowError
        return -(1 << 63) if mag == (1 << 63) else -mag
    if mag > (1 << 63) - 1:
        raise OverflowError
    return mag


def cs_mul(a, b):  # Fix64.MulShiftRound
    negative = (a < 0) != (b < 0)
    ua, ub = magnitude(a), magnitude(b)
    a_hi, a_lo = ua >> 32, ua & 0xFFFFFFFF
    b_hi, b_lo = ub >> 32, ub & 0xFFFFFFFF
    ll, lh, hl, hh = a_lo * b_lo, a_lo * b_hi, a_hi * b_lo, a_hi * b_hi  # each < 2^64
    mid = (ll >> 32) + (lh & 0xFFFFFFFF) + (hl & 0xFFFFFFFF)
    lo = ((ll & 0xFFFFFFFF) | (mid << 32)) & M64
    hi = (hh + (lh >> 32) + (hl >> 32) + (mid >> 32)) & M64
    add = HALF - 1 if negative else HALF
    lo2 = (lo + add) & M64
    if lo2 < lo:
        hi = (hi + 1) & M64
    if hi >> 32:
        raise OverflowError
    return apply_sign(((hi << 32) | (lo2 >> 32)) & M64, negative)


def cs_div(a, b):  # Fix64.operator /
    negative = (a < 0) != (b < 0)
    ua, ub = magnitude(a), magnitude(b)
    q, r = ua // ub, ua % ub
    if q >= (1 << 31):
        raise OverflowError
    for _ in range(32):
        r = (r << 1) & M64
        q = (q << 1) & M64
        if r >= ub:
            r -= ub
            q |= 1
    if r >= ub - r:
        q += 1
    return apply_sign(q, negative)


def model(op, a, b):
    try:
        return (Fix(a) * Fix(b)).raw if op == "mul" else (Fix(a) / Fix(b)).raw
    except OverflowError:
        return "overflow"


def port(op, a, b):
    try:
        return cs_mul(a, b) if op == "mul" else cs_div(a, b)
    except OverflowError:
        return "overflow"


class CSharpAlgorithmPort(unittest.TestCase):
    def test_fuzz_against_model(self):
        rng = random.Random(20261015)
        edge = [0, 1, -1, 1 << 31, -(1 << 31), (1 << 32), -(1 << 32), (1 << 63) - 1, -(1 << 63)]
        samples = []
        for _ in range(40000):
            bits = rng.choice((8, 24, 33, 40, 48, 62))
            samples.append(rng.randrange(-(1 << bits), 1 << bits))
        values = edge + samples
        for i in range(0, len(values) - 1):
            a, b = values[i], values[-i - 1]
            for op in ("mul", "div"):
                if op == "div" and b == 0:
                    continue
                self.assertEqual(port(op, a, b), model(op, a, b), (op, a, b))

    def test_exact_ties(self):
        # Random raws almost never land on a rounding tie, so ties get explicit cases:
        # products whose low 32 bits are exactly 2^31, and quotients ending in exactly .5 ulp.
        for odd in range(1, 400, 2):
            for sign_a in (1, -1):
                for sign_b in (1, -1):
                    a, b = sign_a * odd, sign_b * (1 << 31) * (2 * (odd % 7) + 1)
                    self.assertEqual(port("mul", a, b), model("mul", a, b), ("mul", a, b))
                    a, b = sign_a * odd, sign_b * (2 << 32)  # odd / 2 in ulps -> .5 tie
                    self.assertEqual(port("div", a, b), model("div", a, b), ("div", a, b))


if __name__ == "__main__":
    unittest.main()
