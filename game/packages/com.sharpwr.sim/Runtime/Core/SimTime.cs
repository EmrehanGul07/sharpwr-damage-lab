using System;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Core
{
    /// <summary>
    /// Simulation time in integer microseconds since match start (ADR-0002).
    /// The fixed step advances whole ticks; combat events are scheduled at exact microseconds
    /// inside a tick and resolved in (time, phase, sequence) order.
    /// </summary>
    public readonly struct SimTime : IEquatable<SimTime>, IComparable<SimTime>
    {
        public const long MicrosPerSecond = 1_000_000;

        public readonly long Micros;

        public SimTime(long micros) { Micros = micros; }

        public static readonly SimTime Zero = new SimTime(0);

        /// <summary>Round half up to the microsecond grid. Bit-exact with seconds_to_micros().</summary>
        public static SimTime FromSeconds(Fix64 seconds) =>
            new SimTime(Fix64.MulRawToLong(seconds.Raw, MicrosPerSecond));

        public static SimTime operator +(SimTime a, SimTime b) => new SimTime(checked(a.Micros + b.Micros));
        public static SimTime operator -(SimTime a, SimTime b) => new SimTime(checked(a.Micros - b.Micros));
        public static bool operator <(SimTime a, SimTime b) => a.Micros < b.Micros;
        public static bool operator >(SimTime a, SimTime b) => a.Micros > b.Micros;
        public static bool operator <=(SimTime a, SimTime b) => a.Micros <= b.Micros;
        public static bool operator >=(SimTime a, SimTime b) => a.Micros >= b.Micros;
        public static bool operator ==(SimTime a, SimTime b) => a.Micros == b.Micros;
        public static bool operator !=(SimTime a, SimTime b) => a.Micros != b.Micros;

        public Fix64 ToSeconds() => Fix64.Ratio(Micros, MicrosPerSecond);
        public double ToSecondsDouble() => Micros / 1e6; // sim-lint: allow(floating-point) diagnostics only

        public bool Equals(SimTime other) => Micros == other.Micros;
        public override bool Equals(object obj) => obj is SimTime t && t.Micros == Micros;
        public override int GetHashCode() => Micros.GetHashCode();
        public int CompareTo(SimTime other) => Micros.CompareTo(other.Micros);
        public override string ToString() => Micros + "us";
    }

    /// <summary>Fixed-step clock. Tick k covers (TickStart(k-1), TickStart(k)].</summary>
    public static class SimClock
    {
        /// <summary>Default 30 Hz (docs/moba/07-performance.md). Must be identical on client and server.</summary>
        public const int TicksPerSecond = 30;

        public static SimTime TickStart(long tick) =>
            new SimTime(checked(tick * SimTime.MicrosPerSecond) / TicksPerSecond);
    }
}
