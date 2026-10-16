using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Entities
{
    public enum OrderKind : byte { None = 0, Move = 1, Attack = 2 }

    /// <summary>
    /// Mutable per-unit state. Plain data stored in an array inside <c>Match</c> (no references),
    /// so a whole match can be copied for rollback and hashed. Kit* fields are scratch state
    /// owned by the unit's champion kit (kits themselves are stateless).
    /// </summary>
    public struct Unit
    {
        public int Id;
        public int Definition;          // index into Match definitions
        public Team Team;
        public FixVec2 Position;
        public FixVec2 SpawnPosition;
        public Fix64 Health;
        public Fix64 Mana;
        public bool Alive;
        public SimTime RespawnAt;

        public OrderKind Order;
        public int OrderTarget;
        public FixVec2 OrderPoint;

        // basic attack
        public bool WindingUp;
        public SimTime WindupEndsAt;
        public SimTime AttackReadyAt;
        public int AttackSequence;      // identifies the in-flight attack for stale-event checks
        public bool AttackMelee;        // current attack resolved as melee (no projectile)
        public bool ReadyEventPending;

        public bool HasBufferedCommand; // commands issued during windup apply at windup end
        public Command BufferedCommand;

        // abilities
        public SimTime CooldownQ, CooldownW, CooldownE, CooldownR;
        public SimTime CastLockUntil;   // no attacks, casts or walking (cast times)
        public int CastSequence;
        public Fix64 BonusAsBuff;       // temporary bonus attack speed (fraction)
        public SimTime BonusAsBuffUntil;

        // displacement
        public bool Dashing;
        public FixVec2 DashFrom, DashTo;
        public SimTime DashStart, DashEnd;

        // kit scratch
        public int KitStacks;
        public byte KitLastAction;
        public SimTime KitStacksExpireAt;
        public SimTime KitChannelUntil;
        public int KitChannelCast;
        public SimTime KitSpinUntil;
        public int KitSpinCast;
        public FixVec2 KitAimPoint;
        public int KitAimTarget;
    }
}
