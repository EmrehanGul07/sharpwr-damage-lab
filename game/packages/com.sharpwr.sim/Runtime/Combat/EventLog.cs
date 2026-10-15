using System.Collections.Generic;

namespace SharpWR.Sim.Combat
{
    /// <summary>
    /// Append-only log of resolved events plus a running FNV-1a 64 hash over their raw fields.
    /// Two runs with the same inputs must produce the same <see cref="Hash"/>; client/server
    /// compare it per tick to detect desync (docs/moba/04-networking.md).
    /// </summary>
    public sealed class EventLog
    {
        private const ulong OffsetBasis = 14695981039346656037UL;
        private const ulong Prime = 1099511628211UL;

        private readonly List<CombatEvent> _events = new List<CombatEvent>(256);

        public ulong Hash { get; private set; } = OffsetBasis;
        public IReadOnlyList<CombatEvent> Events => _events;

        public void Append(in CombatEvent e)
        {
            _events.Add(e);
            ulong h = Hash;
            h = Mix(h, (ulong)e.Time.Micros);
            h = Mix(h, (ulong)e.Phase);
            h = Mix(h, (ulong)e.Sequence);
            h = Mix(h, (ulong)e.Kind);
            h = Mix(h, (ulong)(uint)e.Source);
            h = Mix(h, (ulong)(uint)e.Target);
            h = Mix(h, (ulong)(uint)e.ActionId);
            h = Mix(h, (ulong)e.DamageType);
            h = Mix(h, (ulong)e.Amount.Raw);
            Hash = h;
        }

        private static ulong Mix(ulong hash, ulong value)
        {
            unchecked
            {
                for (int i = 0; i < 8; i++)
                {
                    hash ^= (byte)(value >> (8 * i));
                    hash *= Prime;
                }
                return hash;
            }
        }
    }
}
