using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Entities
{
    public enum OrderKind : byte { None = 0, Move = 1, Attack = 2 }

    /// <summary>
    /// Mutable per-unit state. Plain data stored in an array inside <c>Match</c> (struct of
    /// fields, no references), so a whole match can be copied for rollback and hashed.
    /// </summary>
    public struct Unit
    {
        public int Id;
        public int Definition;          // index into Match definitions
        public Team Team;
        public FixVec2 Position;
        public FixVec2 SpawnPosition;
        public Fix64 Health;
        public bool Alive;
        public SimTime RespawnAt;

        public OrderKind Order;
        public int OrderTarget;
        public FixVec2 OrderPoint;

        public bool WindingUp;
        public SimTime WindupEndsAt;
        public SimTime AttackReadyAt;
        public int AttackSequence;      // identifies the in-flight attack for stale-event checks
        public bool ReadyEventPending;

        public bool HasBufferedCommand; // commands issued during windup apply at windup end
        public Command BufferedCommand;
    }
}
