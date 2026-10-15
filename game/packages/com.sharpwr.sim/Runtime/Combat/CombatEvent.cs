using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Combat
{
    public enum DamageType : byte { Physical = 0, Magic = 1, True = 2 }

    /// <summary>
    /// Resolution phase inside one microsecond. Lower phases resolve first; this ordering is
    /// part of the determinism contract (docs/moba/03-combat-event-model.md, section 3).
    /// </summary>
    public enum EventPhase : byte
    {
        Input = 0,          // validated commands for this tick
        CastStart = 10,     // casts begin, costs paid, cooldowns started
        Movement = 20,      // dashes/blinks resolve position
        Impact = 30,        // projectiles / attacks land: damage computed
        Damage = 40,        // shields absorb, HP changes, on-hit/on-damage triggers enqueue
        Death = 50,         // HP <= 0 resolved after all same-time damage
        StatusExpiry = 60,  // buffs/CC end
    }

    public enum CombatEventKind : ushort
    {
        AttackStart = 1,
        AttackImpact = 2,
        AbilityCast = 10,
        AbilityImpact = 11,
        DamageApplied = 20,
        Heal = 21,
        ShieldAbsorbed = 22,
        StatusApplied = 30,
        StatusExpired = 31,
        Death = 40,
        Respawn = 41,
        Rejected = 90,
    }

    /// <summary>One resolved, immutable fact. The event log is the simulation's audit trail.</summary>
    public readonly struct CombatEvent
    {
        public readonly SimTime Time;
        public readonly EventPhase Phase;
        public readonly long Sequence;     // global insertion order: final tie breaker
        public readonly CombatEventKind Kind;
        public readonly int Source;        // entity id
        public readonly int Target;        // entity id or -1
        public readonly int ActionId;      // ability/attack definition id
        public readonly DamageType DamageType;
        public readonly Fix64 Amount;      // post-mitigation amount for DamageApplied

        public CombatEvent(SimTime time, EventPhase phase, long sequence, CombatEventKind kind,
                           int source, int target, int actionId, DamageType damageType, Fix64 amount)
        {
            Time = time; Phase = phase; Sequence = sequence; Kind = kind; Source = source;
            Target = target; ActionId = actionId; DamageType = damageType; Amount = amount;
        }
    }
}
