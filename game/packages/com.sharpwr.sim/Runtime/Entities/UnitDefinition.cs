using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Entities
{
    /// <summary>
    /// Resolved stats for one unit at one level (built from content by ChampionContent or by
    /// tests). Immutable; buffs/items modify derived values in later milestones.
    /// </summary>
    public sealed class UnitDefinition
    {
        public string Id = "";
        public Fix64 MaxHealth;
        public Fix64 Armor;
        public Fix64 MagicResist;
        public Fix64 BaseAttackDamage;
        public Fix64 AttackDamage;
        public Fix64 BaseAttackSpeed;
        public Fix64 AttackSpeedRatio;
        public Fix64 BonusAttackSpeed;        // fraction, e.g. 0.14 = +14%
        public Fix64 BaseWindupSeconds;
        public Fix64 WindupBonusAsFactor;     // windup = base / (1 + factor * bonusAS)
        public Fix64 AttackRange;             // center-to-center (point targets, see Radius)
        public Fix64 ProjectileSpeed;         // 0 = instant (melee)
        public Fix64 MoveSpeed;
        public Fix64 Radius;                  // gameplay radius; 0 while unresolved in content
        public bool CanAct = true;            // false for practice dummies

        /// <summary>AS = base + ratio * bonus (sharpwr/aa_engine.py). Cap 3.0 (Damage Lab cap).</summary>
        public Fix64 AttackSpeed => Fix64.Min(Fix64.FromInt(3), BaseAttackSpeed + AttackSpeedRatio * BonusAttackSpeed);

        public Fix64 WindupSeconds =>
            BaseWindupSeconds / (Fix64.One + WindupBonusAsFactor * Fix64.Max(Fix64.Zero, BonusAttackSpeed));

        public static UnitDefinition Dummy(Fix64 health, Fix64 armor, Fix64 magicResist) => new UnitDefinition
        {
            Id = "dummy", MaxHealth = health, Armor = armor, MagicResist = magicResist, CanAct = false,
        };
    }
}
