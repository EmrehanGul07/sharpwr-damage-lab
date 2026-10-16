using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Abilities
{
    /// <summary>
    /// Champion-specific hooks (docs/moba/05-ability-framework.md). Kits are immutable: per-unit
    /// state lives in the Unit struct's Kit* fields so matches stay cloneable and hashable.
    /// Generic gates (lock, rank, cooldown, mana) are checked by Match; the kit adds its own.
    /// </summary>
    public interface IChampionKit
    {
        /// <summary>Kit-specific validation. Must not change any state. Null = allowed.</summary>
        RejectReason? Validate(Match match, int unit, AbilitySlot slot, in Command command, SimTime now);

        /// <summary>Perform a validated cast (costs and cooldown are already paid).</summary>
        void Execute(Match match, int unit, AbilitySlot slot, in Command command, SimTime now, int actionId);

        /// <summary>Events this kit scheduled (AbilityCast/AbilityImpact/StatusExpired).</summary>
        void OnEvent(Match match, in ScheduledEvent e);

        /// <summary>Basic attacks may not start before this time (spins, channels…).</summary>
        SimTime AttackBlockedUntil(Match match, int unit);

        /// <summary>After a basic attack's damage resolved. healthBefore = target HP before it.</summary>
        void OnAttackHit(Match match, int unit, int target, SimTime now, bool melee, int actionId, Fix64 healthBefore);

        /// <summary>Clear kit scratch state when the unit dies.</summary>
        void OnDeath(Match match, int unit);
    }

    /// <summary>Encodes (slot, cast) into event ActionIds so logs group hits by ability.</summary>
    public static class ActionIds
    {
        public const int AbilityBase = 10_000;

        public static int Ability(AbilitySlot slot, int castSequence) =>
            ((int)slot + 1) * AbilityBase + castSequence % AbilityBase;

        public static bool IsAbility(int actionId) => actionId >= AbilityBase;

        public static AbilitySlot SlotOf(int actionId) => (AbilitySlot)(actionId / AbilityBase - 1);
    }
}
