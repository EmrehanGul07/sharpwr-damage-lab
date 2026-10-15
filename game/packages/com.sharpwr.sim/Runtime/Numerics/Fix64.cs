using System;
using System.Globalization;

namespace SharpWR.Sim.Numerics
{
    /// <summary>
    /// Signed Q32.32 fixed-point number. The only numeric type allowed for gameplay values
    /// inside the simulation (ADR-0002). Bit-exact with tools/parity/fixed_point_model.py.
    /// </summary>
    /// <remarks>
    /// Rounding rules (all deterministic, platform independent):
    ///   Mul   : floor((a*b + 2^31) / 2^32)                (round half up)
    ///   Div   : round half away from zero of a*2^32 / b
    ///   Parse : round half away from zero of decimal*2^32
    /// Overflow throws <see cref="OverflowException"/>; it never wraps silently.
    /// </remarks>
    public readonly struct Fix64 : IEquatable<Fix64>, IComparable<Fix64>
    {
        public const int FractionalBits = 32;
        private const long OneRaw = 1L << FractionalBits;
        private const ulong HalfRaw = 1UL << (FractionalBits - 1);

        public readonly long Raw;

        private Fix64(long raw) { Raw = raw; }

        public static readonly Fix64 Zero = new Fix64(0);
        public static readonly Fix64 One = new Fix64(OneRaw);
        public static readonly Fix64 Two = new Fix64(2 * OneRaw);
        public static readonly Fix64 Hundred = new Fix64(100 * OneRaw);
        public static readonly Fix64 MaxValue = new Fix64(long.MaxValue);
        public static readonly Fix64 MinValue = new Fix64(long.MinValue);

        public static Fix64 FromRaw(long raw) => new Fix64(raw);

        public static Fix64 FromInt(int value) => new Fix64((long)value << FractionalBits);

        /// <summary>Exact ratio num/den with a single rounding (preferred for constants).</summary>
        public static Fix64 Ratio(long num, long den) => FromLong(num) / FromLong(den);

        public static Fix64 FromLong(long value)
        {
            if (value > int.MaxValue || value < int.MinValue) throw new OverflowException();
            return new Fix64(value << FractionalBits);
        }

        /// <summary>
        /// Content import only (decimal text from game/content JSON). Never call with values
        /// computed at runtime.
        /// </summary>
        public static Fix64 Parse(string text)
        {
            decimal d = decimal.Parse(text, NumberStyles.Float, CultureInfo.InvariantCulture);
            decimal scaled = System.Math.Round(d * 4294967296m, MidpointRounding.AwayFromZero);
            return new Fix64(decimal.ToInt64(scaled));
        }

        public static Fix64 operator +(Fix64 a, Fix64 b) => new Fix64(checked(a.Raw + b.Raw));
        public static Fix64 operator -(Fix64 a, Fix64 b) => new Fix64(checked(a.Raw - b.Raw));
        public static Fix64 operator -(Fix64 a) => new Fix64(checked(-a.Raw));

        public static Fix64 operator *(Fix64 a, Fix64 b) => new Fix64(MulShiftRound(a.Raw, b.Raw));

        public static Fix64 operator /(Fix64 a, Fix64 b)
        {
            if (b.Raw == 0) throw new DivideByZeroException();
            bool negative = (a.Raw < 0) != (b.Raw < 0);
            ulong ua = Magnitude(a.Raw);
            ulong ub = Magnitude(b.Raw);

            ulong q = ua / ub;
            ulong r = ua % ub;
            if (q >= (1UL << 31)) throw new OverflowException();
            for (int i = 0; i < FractionalBits; i++)
            {
                r <<= 1; // r < ub <= 2^63, so no overflow
                q <<= 1;
                if (r >= ub) { r -= ub; q |= 1; }
            }
            if (r >= ub - r) q++; // 2r >= ub without overflowing
            return new Fix64(ApplySign(q, negative));
        }

        public static bool operator <(Fix64 a, Fix64 b) => a.Raw < b.Raw;
        public static bool operator >(Fix64 a, Fix64 b) => a.Raw > b.Raw;
        public static bool operator <=(Fix64 a, Fix64 b) => a.Raw <= b.Raw;
        public static bool operator >=(Fix64 a, Fix64 b) => a.Raw >= b.Raw;
        public static bool operator ==(Fix64 a, Fix64 b) => a.Raw == b.Raw;
        public static bool operator !=(Fix64 a, Fix64 b) => a.Raw != b.Raw;

        public static Fix64 Max(Fix64 a, Fix64 b) => a.Raw >= b.Raw ? a : b;
        public static Fix64 Min(Fix64 a, Fix64 b) => a.Raw <= b.Raw ? a : b;
        public static Fix64 Clamp(Fix64 v, Fix64 lo, Fix64 hi) => Max(lo, Min(hi, v));

        /// <summary>
        /// Deterministic square root: integer sqrt seed (isqrt(raw) &lt;&lt; 16) then three Newton
        /// steps x = (x + v/x) &gt;&gt; 1. Bit-exact with fixed_point_model.fsqrt. Negative or zero → 0.
        /// </summary>
        public static Fix64 Sqrt(Fix64 v)
        {
            if (v.Raw <= 0) return Zero;
            Fix64 x = new Fix64((long)(ISqrt((ulong)v.Raw) << 16));
            for (int i = 0; i < 3; i++)
                x = new Fix64((x + v / x).Raw >> 1);
            return x;
        }

        /// <summary>floor(sqrt(n)) by the bitwise method.</summary>
        public static ulong ISqrt(ulong n)
        {
            ulong result = 0, bit = 1UL << 62;
            while (bit > n) bit >>= 2;
            while (bit != 0)
            {
                if (n >= result + bit)
                {
                    n -= result + bit;
                    result = (result >> 1) + bit;
                }
                else
                {
                    result >>= 1;
                }
                bit >>= 2;
            }
            return result;
        }

        /// <summary>Round half up of raw * multiplier / 2^32 (used for unit conversion).</summary>
        public static long MulRawToLong(long raw, long multiplier) => MulShiftRound(raw, multiplier);

        /// <summary>Diagnostics, logs and rendering only. Never feed the result back into the sim.</summary>
        public double ToDouble() => Raw / 4294967296.0; // sim-lint: allow(floating-point) diagnostics only

        public bool Equals(Fix64 other) => Raw == other.Raw;
        public override bool Equals(object obj) => obj is Fix64 f && f.Raw == Raw;
        public override int GetHashCode() => Raw.GetHashCode();
        public int CompareTo(Fix64 other) => Raw.CompareTo(other.Raw);
        public override string ToString() => ToDouble().ToString("R", CultureInfo.InvariantCulture);

        // ---- exact 64x64 -> 128 bit helpers ---------------------------------------------

        private static ulong Magnitude(long v) => v < 0 ? (ulong)(-(v + 1)) + 1UL : (ulong)v;

        private static long ApplySign(ulong magnitude, bool negative)
        {
            if (negative)
            {
                if (magnitude > (1UL << 63)) throw new OverflowException();
                return magnitude == (1UL << 63) ? long.MinValue : -(long)magnitude;
            }
            if (magnitude > long.MaxValue) throw new OverflowException();
            return (long)magnitude;
        }

        /// <summary>floor((a*b + 2^31) / 2^32), exact.</summary>
        private static long MulShiftRound(long a, long b)
        {
            bool negative = (a < 0) != (b < 0);
            ulong ua = Magnitude(a), ub = Magnitude(b);
            ulong aHi = ua >> 32, aLo = ua & 0xFFFFFFFFUL;
            ulong bHi = ub >> 32, bLo = ub & 0xFFFFFFFFUL;

            ulong ll = aLo * bLo;
            ulong lh = aLo * bHi;
            ulong hl = aHi * bLo;
            ulong hh = aHi * bHi;

            ulong mid = (ll >> 32) + (lh & 0xFFFFFFFFUL) + (hl & 0xFFFFFFFFUL);
            ulong lo = (ll & 0xFFFFFFFFUL) | (mid << 32);
            ulong hi = hh + (lh >> 32) + (hl >> 32) + (mid >> 32);

            // Positive product P: (P + 2^31) >> 32.  Negative product -P:
            // floor((-P + 2^31) / 2^32) == -((P + 2^31 - 1) >> 32).
            ulong add = negative ? HalfRaw - 1UL : HalfRaw;
            ulong lo2 = lo + add;
            if (lo2 < lo) hi++;

            if ((hi >> 32) != 0) throw new OverflowException();
            ulong magnitude = (hi << 32) | (lo2 >> 32);
            return ApplySign(magnitude, negative);
        }
    }
}
