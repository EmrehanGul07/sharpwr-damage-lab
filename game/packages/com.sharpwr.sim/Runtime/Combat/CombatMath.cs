using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Combat
{
    /// <summary>
    /// Pure combat formulas. Operation order is part of the contract: it must match
    /// tools/parity/fixed_point_model.py exactly, and the Python Damage Lab within tolerance.
    /// Reference: sharpwr/aa_engine.py (gu, rm, effective_resistance),
    /// sharpwr/champion_skill_data.py (samira_skill).
    /// </summary>
    public static class CombatMath
    {
        /// <summary>
        /// App growth curve n*(0.7025 + 0.0175n) == n*(281 + 7n)/400, n = level - 1.
        /// Status: Damage Lab curve, Wild Rift level audit still open.
        /// </summary>
        public static Fix64 GrowthUnits(int level)
        {
            if (level < 1 || level > 15) throw new System.ArgumentOutOfRangeException(nameof(level));
            long n = level - 1;
            return Fix64.Ratio(n * (281 + 7 * n), 400);
        }

        public static Fix64 StatAtLevel(Fix64 baseValue, Fix64 growth, int level) =>
            baseValue + growth * GrowthUnits(level);

        /// <summary>Percent then flat penetration; never turns positive resistance negative.</summary>
        public static Fix64 EffectiveResistance(Fix64 value, Fix64 percentPen, Fix64 flatPen)
        {
            if (value < Fix64.Zero) return value;
            Fix64 pct = Fix64.Clamp(percentPen, Fix64.Zero, Fix64.One);
            return Fix64.Max(Fix64.Zero, value * (Fix64.One - pct) - Fix64.Max(Fix64.Zero, flatPen));
        }

        public static Fix64 ResistanceMultiplier(Fix64 effectiveResistance)
        {
            if (effectiveResistance >= Fix64.Zero)
                return Fix64.Hundred / (Fix64.Hundred + effectiveResistance);
            return Fix64.Two - Fix64.Hundred / (Fix64.Hundred - effectiveResistance);
        }

        /// <summary>base + totalAdRatio*AD + bonusAdRatio*max(0, AD - baseAD).</summary>
        public static Fix64 ScaledAbility(Fix64 baseDamage, Fix64 totalAdRatio, Fix64 bonusAdRatio,
                                          Fix64 attackDamage, Fix64 baseAttackDamage)
        {
            Fix64 bonus = Fix64.Max(Fix64.Zero, attackDamage - baseAttackDamage);
            return baseDamage + totalAdRatio * attackDamage + bonusAdRatio * bonus;
        }

        /// <summary>raw * (1 + critEffectiveness * (critDamage - 1)) when the hit crits.</summary>
        public static Fix64 CritScaled(Fix64 raw, Fix64 critEffectiveness, Fix64 critDamage, bool isCrit)
        {
            if (!isCrit) return raw;
            return raw * (Fix64.One + critEffectiveness * (critDamage - Fix64.One));
        }

        public static Fix64 Mitigate(Fix64 raw, Fix64 resistance, Fix64 percentPen, Fix64 flatPen) =>
            raw * ResistanceMultiplier(EffectiveResistance(resistance, percentPen, flatPen));
    }
}
