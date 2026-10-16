using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.World
{
    /// <summary>
    /// A line skillshot in flight. Swept every tick against unit positions; the hit time is the
    /// moment the projectile centre passes the target's projection on its path (for a target
    /// standing on the path this equals distance / speed, the Damage Lab arrival time).
    /// </summary>
    public struct Projectile
    {
        public int Id;
        public int Owner;
        public int ActionId;
        public FixVec2 Origin;
        public FixVec2 Direction;      // unit vector
        public Fix64 Speed;
        public Fix64 Range;
        public Fix64 HalfWidth;
        public SimTime Visible;        // cast start: the telegraph opponents can react to
        public SimTime Release;        // projectile leaves the caster
        public Fix64 Swept;            // distance already checked
        public bool Active;

        public FixVec2 PositionAt(SimTime time)
        {
            Fix64 travelled = Fix64.Min(Range, Speed * Fix64.Ratio(time.Micros - Release.Micros, SimTime.MicrosPerSecond));
            return Origin + Direction * travelled;
        }
    }
}
