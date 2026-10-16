using SharpWR.Sim.Combat;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Abilities
{
    public enum AbilitySlot : byte { Q = 0, W = 1, E = 2, R = 3 }

    /// <summary>Data part of an ability (from content "abilities.&lt;slot&gt;").</summary>
    public sealed class AbilityDefinition
    {
        public AbilitySlot Slot;
        public string Name = "";
        public DamageType DamageType;
        public Fix64[] BaseDamageByRank = new Fix64[0];
        public Fix64 TotalAdRatio;
        public Fix64 BonusAdRatio;
        public int Hits = 1;
        public Fix64 CritEffectiveness;
        public Fix64[] CooldownByRank = new Fix64[0];
        public Fix64 ManaCost;

        public int MaxRank => BaseDamageByRank.Length;

        /// <summary>Raw (pre-mitigation, non-crit) damage of one hit at a rank.</summary>
        public Fix64 RawDamage(int rank, Fix64 attackDamage, Fix64 baseAttackDamage) =>
            CombatMath.ScaledAbility(BaseDamageByRank[rank - 1], TotalAdRatio, BonusAdRatio, attackDamage, baseAttackDamage);
    }
}
