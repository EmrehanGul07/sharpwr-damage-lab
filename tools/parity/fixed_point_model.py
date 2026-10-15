"""Bit-exact Python model of the C# simulation's Q32.32 fixed-point arithmetic.

Purpose: validate the numeric design (ADR-0002) against the Damage Lab before the C# core is
compiled, and later serve as a cross-check for the C# implementation: both must produce the
same raw int64 values for the same inputs (game/sim/tests/Numerics/Fix64VectorTests.cs uses the
vectors this module emits).

Semantics mirrored from game/packages/com.sharpwr.sim/Runtime/Numerics/Fix64.cs:
- raw value is a signed 64-bit integer, value = raw / 2**32
- Mul: round half up of (a*b) / 2**32, computed exactly (C# uses 128-bit emulation)
- Div: round half away from zero of (a * 2**32) / b, computed exactly
- Any result outside int64 raises OverflowError (C# throws OverflowException)
- Parse: decimal string -> nearest raw, ties away from zero (C# System.Decimal path)
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext
from fractions import Fraction

getcontext().prec = 60

FRAC_BITS = 32
ONE = 1 << FRAC_BITS
INT64_MIN, INT64_MAX = -(1 << 63), (1 << 63) - 1


def _check(raw: int) -> int:
    if not INT64_MIN <= raw <= INT64_MAX:
        raise OverflowError(raw)
    return raw


class Fix:
    __slots__ = ("raw",)

    def __init__(self, raw: int):
        self.raw = _check(int(raw))

    # Construction ---------------------------------------------------------------------
    @staticmethod
    def parse(text) -> "Fix":
        """Content import path: decimal text -> nearest Q32.32 (ties away from zero)."""
        scaled = Decimal(str(text)) * ONE
        return Fix(int(scaled.quantize(Decimal(1), rounding=ROUND_HALF_UP)))

    @staticmethod
    def of_int(value: int) -> "Fix":
        return Fix(value << FRAC_BITS)

    # Arithmetic -----------------------------------------------------------------------
    def __add__(self, other):
        return Fix(self.raw + other.raw)

    def __sub__(self, other):
        return Fix(self.raw - other.raw)

    def __neg__(self):
        return Fix(-self.raw)

    def __mul__(self, other):
        # floor((a*b + 2^31) / 2^32): Python >> on negatives is floor, like C# arithmetic shift.
        return Fix((self.raw * other.raw + (1 << (FRAC_BITS - 1))) >> FRAC_BITS)

    def __truediv__(self, other):
        if other.raw == 0:
            raise ZeroDivisionError
        num = abs(self.raw) << FRAC_BITS
        den = abs(other.raw)
        q, r = divmod(num, den)
        if 2 * r >= den:
            q += 1
        return Fix(q if (self.raw < 0) == (other.raw < 0) else -q)

    def __lt__(self, other):
        return self.raw < other.raw

    def __le__(self, other):
        return self.raw <= other.raw

    def __eq__(self, other):
        return isinstance(other, Fix) and self.raw == other.raw

    def __hash__(self):
        return hash(self.raw)

    def to_float(self) -> float:
        """Diagnostics only: never used inside the simulation."""
        return float(Fraction(self.raw, ONE))

    def __repr__(self):
        return f"Fix({self.to_float()!r}, raw={self.raw})"


ZERO = Fix(0)
ONE_FIX = Fix.of_int(1)
HUNDRED = Fix.of_int(100)
TWO = Fix.of_int(2)


def fmax(a, b):
    return a if b < a else b


def fmin(a, b):
    return a if a < b else b


# Formulas: the same operation order as the C# CombatMath class ---------------------------


def growth_units(level: int) -> Fix:
    # n*(0.7025 + 0.0175n) == n*(281 + 7n)/400: one exact integer product and a single
    # rounding. Composing the parsed decimals instead loses ~1e-8 and is amplified by large
    # growth stats (HP 128/level -> 1e-6 HP), which failed the parity tolerance in the spike.
    n = level - 1
    return Fix.of_int(n * (281 + 7 * n)) / Fix.of_int(400)


def stat_at_level(base: Fix, growth: Fix, level: int) -> Fix:
    return base + growth * growth_units(level)


def effective_resistance(value: Fix, pct: Fix, flat: Fix) -> Fix:
    if value < ZERO:
        return value
    pct = fmin(ONE_FIX, fmax(ZERO, pct))
    return fmax(ZERO, value * (ONE_FIX - pct) - fmax(ZERO, flat))


def resistance_multiplier(value: Fix) -> Fix:
    if ZERO <= value:
        return HUNDRED / (HUNDRED + value)
    return TWO - HUNDRED / (HUNDRED - value)


def scaled_ability(
    base: Fix, total_ad_ratio: Fix, bonus_ad_ratio: Fix, ad: Fix, base_ad: Fix
) -> Fix:
    bonus = fmax(ZERO, ad - base_ad)
    return base + total_ad_ratio * ad + bonus_ad_ratio * bonus


def crit_scaled(raw: Fix, crit_effectiveness: Fix, crit_damage: Fix, is_crit: bool) -> Fix:
    if not is_crit:
        return raw
    return raw * (ONE_FIX + crit_effectiveness * (crit_damage - ONE_FIX))


def fsqrt(v: Fix) -> Fix:
    """Mirror of Fix64.Sqrt: isqrt seed then three Newton steps with a floor halving."""
    import math

    if v.raw <= 0:
        return ZERO
    x = Fix(math.isqrt(v.raw) << 16)
    for _ in range(3):
        x = Fix((x + v / x).raw >> 1)
    return x


# Time: integer microseconds ---------------------------------------------------------------

MICROS = 1_000_000


def seconds_to_micros(seconds: Fix) -> int:
    """Round half up to the microsecond grid."""
    product = seconds.raw * MICROS
    return (product + (1 << (FRAC_BITS - 1))) >> FRAC_BITS


def attack_period_micros(attack_speed: Fix) -> int:
    return seconds_to_micros(ONE_FIX / attack_speed)


def aa_impacts_stationary(
    windup: Fix, attack_speed: Fix, distance: Fix, projectile_speed: Fix, until_micros: int
) -> list[int]:
    """Impact times of a ranged AA loop against a stationary target, from t=0."""
    period = attack_period_micros(attack_speed)
    travel = seconds_to_micros(distance / projectile_speed)
    windup_us = seconds_to_micros(windup)
    impacts, start = [], 0
    while start + windup_us + travel <= until_micros:
        impacts.append(start + windup_us + travel)
        start += period
    return impacts
