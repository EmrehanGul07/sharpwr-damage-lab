namespace SharpWR.Client
{
    /// <summary>
    /// Converts variable frame time into whole simulation ticks (docs/moba/01-architecture.md).
    /// Presentation code may use doubles; the simulation never sees them.
    /// </summary>
    public sealed class FixedStepHost
    {
        public static readonly double TickSeconds = 1.0 / Sim.Core.SimClock.TicksPerSecond;

        /// <summary>At most this many ticks per frame; beyond that the game slows down instead of spiralling.</summary>
        public int MaxStepsPerFrame = 3;

        private double _accumulator;

        /// <summary>0..1 position between the previous and current tick, for view interpolation.</summary>
        public double Alpha => _accumulator / TickSeconds;

        public int Advance(double frameSeconds)
        {
            if (!(frameSeconds > 0)) return 0;   // also rejects NaN
            _accumulator += frameSeconds;
            int steps = (int)(_accumulator / TickSeconds);
            if (steps > MaxStepsPerFrame)
            {
                _accumulator = 0;                 // drop the backlog (slow motion), never fast-forward
                return MaxStepsPerFrame;
            }
            _accumulator -= steps * TickSeconds;
            return steps;
        }
    }
}
