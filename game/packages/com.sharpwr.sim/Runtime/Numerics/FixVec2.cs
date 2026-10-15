using System;

namespace SharpWR.Sim.Numerics
{
    /// <summary>Ground-plane vector (x, z) in game units. Height is presentation only.</summary>
    public readonly struct FixVec2 : IEquatable<FixVec2>
    {
        public readonly Fix64 X, Z;

        public FixVec2(Fix64 x, Fix64 z) { X = x; Z = z; }

        public static readonly FixVec2 Zero = new FixVec2(Fix64.Zero, Fix64.Zero);

        public static FixVec2 operator +(FixVec2 a, FixVec2 b) => new FixVec2(a.X + b.X, a.Z + b.Z);
        public static FixVec2 operator -(FixVec2 a, FixVec2 b) => new FixVec2(a.X - b.X, a.Z - b.Z);
        public static FixVec2 operator *(FixVec2 a, Fix64 s) => new FixVec2(a.X * s, a.Z * s);

        public Fix64 LengthSquared => X * X + Z * Z;
        public Fix64 Length => Fix64.Sqrt(LengthSquared);

        public static Fix64 Distance(FixVec2 a, FixVec2 b) => (b - a).Length;

        /// <summary>True when |b - a| &lt;= range, without a square root.</summary>
        public static bool WithinRange(FixVec2 a, FixVec2 b, Fix64 range) =>
            range >= Fix64.Zero && (b - a).LengthSquared <= range * range;

        /// <summary>Move from <paramref name="from"/> toward <paramref name="to"/> by at most maxStep.</summary>
        public static FixVec2 MoveTowards(FixVec2 from, FixVec2 to, Fix64 maxStep)
        {
            FixVec2 delta = to - from;
            Fix64 length = delta.Length;
            if (length <= maxStep || length == Fix64.Zero) return to;
            return from + delta * (maxStep / length);
        }

        public bool Equals(FixVec2 other) => X == other.X && Z == other.Z;
        public override bool Equals(object obj) => obj is FixVec2 v && Equals(v);
        public override int GetHashCode() => X.GetHashCode() * 397 ^ Z.GetHashCode();
        public override string ToString() => "(" + X + ", " + Z + ")";
    }
}
