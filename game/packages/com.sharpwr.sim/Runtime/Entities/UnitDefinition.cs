using SharpWR.Sim.Abilities;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Entities
{
    /// <summary>
    /// Resolved stats for one unit at one level (built from content by ChampionContent or by
    /// tests). Immutable during a match; temporary buffs live in <see cref="Unit"/>.
    /// </summary>
    public sealed class UnitDefinition
    {
        public string Id = "";
        public int Level = 1;
        public Fix64 MaxHealth;
        public Fix64 MaxMana;
        public Fix64 ManaRegenPer5s;
        public Fix64 Armor;
        public Fix64 MagicResist;
        public Fix64 BaseAttackDamage;        // AD without items/buffs at this level ("base AD")
        public Fix64 AttackDamage;
        public Fix64 BaseAttackSpeed;
        public Fix64 AttackSpeedRatio;
        public Fix64 BonusAttackSpeed;        // fraction, e.g. 0.14 = +14%
        public Fix64 BaseWindupSeconds;
        public Fix64 WindupBonusAsFactor;     // windup = base / (1 + factor * bonusAS)
        public Fix64 AttackRange;             // center-to-center (point targets, see Radius)
        public Fix64 MeleeAttackRange;        // attacks within this range are melee (0 = never)
        public Fix64 ProjectileSpeed;         // 0 = instant (melee)
        public Fix64 MoveSpeed;
        public Fix64 Radius;                  // gameplay radius; 0 while unresolved in content
        public Fix64 AbilityHaste;
        public bool CanAct = true;            // false for practice dummies

        /// <summary>Q, W, E, R definitions (null entries = no ability).</summary>
        public AbilityDefinition[] Abilities = new AbilityDefinition[4];
        public int[] AbilityRanks = new int[4];
        public IChampionKit Kit;

        public static readonly Fix64 AttackSpeedCap = Fix64.FromInt(3);

        /// <summary>AS = base + ratio * bonus (sharpwr/aa_engine.py), capped at 3.0 (Damage Lab cap).</summary>
        public Fix64 AttackSpeedWith(Fix64 extraBonus) =>
            Fix64.Min(AttackSpeedCap, BaseAttackSpeed + AttackSpeedRatio * (BonusAttackSpeed + extraBonus));

        public Fix64 WindupSecondsWith(Fix64 extraBonus) =>
            BaseWindupSeconds / (Fix64.One + WindupBonusAsFactor * Fix64.Max(Fix64.Zero, BonusAttackSpeed + extraBonus));

        public Fix64 AttackSpeed => AttackSpeedWith(Fix64.Zero);
        public Fix64 WindupSeconds => WindupSecondsWith(Fix64.Zero);

        public static UnitDefinition Dummy(Fix64 health, Fix64 armor, Fix64 magicResist) => new UnitDefinition
        {
            Id = "dummy", MaxHealth = health, Armor = armor, MagicResist = magicResist, CanAct = false,
        };
    }
}
