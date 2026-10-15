namespace SharpWR.Sim.Numerics
{
    /// <summary>
    /// PCG32 (XSH-RR). One stream per purpose (e.g. crit rolls per entity) so adding a consumer
    /// never shifts another consumer's sequence. Never use System.Random or UnityEngine.Random
    /// inside the simulation.
    /// </summary>
    public struct DeterministicRandom
    {
        private const ulong Multiplier = 6364136223846793005UL;
        private ulong _state;
        private readonly ulong _increment;

        public DeterministicRandom(ulong seed, ulong stream)
        {
            _state = 0;
            _increment = (stream << 1) | 1UL;
            NextUInt();
            _state += seed;
            NextUInt();
        }

        public uint NextUInt()
        {
            ulong old = _state;
            _state = unchecked(old * Multiplier + _increment);
            uint xorshifted = (uint)(((old >> 18) ^ old) >> 27);
            int rot = (int)(old >> 59);
            return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
        }

        /// <summary>Uniform in [0, 1) with 32 fractional bits, exactly representable as Fix64.</summary>
        public Fix64 NextUnit() => Fix64.FromRaw(NextUInt());

        /// <summary>True with probability p (p clamped to [0, 1]).</summary>
        public bool Chance(Fix64 p) => NextUnit() < Fix64.Clamp(p, Fix64.Zero, Fix64.One);
    }
}
