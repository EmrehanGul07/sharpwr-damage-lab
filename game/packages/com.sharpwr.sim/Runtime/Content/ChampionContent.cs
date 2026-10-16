using System;
using System.Collections.Generic;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Champions;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Content
{
    /// <summary>Thrown when content lacks a value the requested feature needs.</summary>
    public sealed class UnsupportedContentException : Exception
    {
        public UnsupportedContentException(string message) : base(message) { }
    }

    /// <summary>
    /// Builds a <see cref="UnitDefinition"/> from a champion content file (schema
    /// sharpwr.champion/1) at a level. Required fields that are "unresolved" throw; optional
    /// ones fall back to a labelled engine default and are listed in <see cref="Unsupported"/>.
    /// </summary>
    public sealed class ChampionContent
    {
        public readonly string Id;
        public readonly string DisplayName;
        public readonly bool Shippable;
        private readonly JsonNode _root;

        /// <summary>Human-readable list of gaps the game must show (never silently filled).</summary>
        public readonly List<string> Unsupported = new List<string>();

        public ChampionContent(string json)
        {
            _root = JsonNode.Parse(json);
            if (_root["schema"]?.Text != "sharpwr.champion/1")
                throw new FormatException("Not a sharpwr.champion/1 file");
            Id = _root["id"].Text;
            DisplayName = _root["display_name"].Text;
            Shippable = _root["shippable"]?.Bool == true;
            JsonNode list = _root["unsupported_mechanics"];
            if (list != null) foreach (JsonNode item in list.Items) Unsupported.Add(item.Text);
        }

        public UnitDefinition AtLevel(int level)
        {
            Fix64 bonusAs = Stat("bonus_attack_speed_level1") + Stat("bonus_attack_speed_per_level") * CombatMath.GrowthUnits(level);
            Fix64 attackDamage = CombatMath.StatAtLevel(Stat("base_ad"), Stat("ad_per_level"), level);
            var d = new UnitDefinition
            {
                Id = Id,
                Level = level,
                MaxHealth = CombatMath.StatAtLevel(Stat("base_hp"), Stat("hp_per_level"), level),
                MaxMana = CombatMath.StatAtLevel(Stat("base_mana"), Stat("mana_per_level"), level),
                ManaRegenPer5s = CombatMath.StatAtLevel(Stat("mana_regen_per_5s"), Stat("mana_regen_per_5s_per_level"), level),
                Armor = CombatMath.StatAtLevel(Stat("base_armor"), Stat("armor_per_level"), level),
                MagicResist = CombatMath.StatAtLevel(Stat("base_mr"), Stat("mr_per_level"), level),
                // Level growth is base AD; bonus AD comes only from items/buffs (none in M1).
                BaseAttackDamage = attackDamage,
                AttackDamage = attackDamage,
                BaseAttackSpeed = Stat("base_attack_speed"),
                AttackSpeedRatio = Stat("attack_speed_ratio"),
                BonusAttackSpeed = bonusAs,
                BaseWindupSeconds = Stat("attack_windup_seconds"),
                WindupBonusAsFactor = Stat("attack_windup_bonus_as_factor"),
                AttackRange = Stat("attack_range"),
                ProjectileSpeed = Stat("attack_projectile_speed"),
                MoveSpeed = Stat("movement_speed"),
                Radius = OptionalStat("gameplay_radius", Fix64.Zero,
                    "gameplay_radius unresolved: units are point targets for range checks (Damage Lab approximation)"),
            };
            LoadAbilities(d, level);
            return d;
        }

        private void LoadAbilities(UnitDefinition d, int level)
        {
            JsonNode abilities = _root["abilities"];
            JsonNode kit = _root["kit"];
            if (abilities == null || kit == null) return;   // stats-only content: basic attacks only
            string slots = "QWER";
            for (int i = 0; i < 4; i++)
            {
                JsonNode a = abilities[slots.Substring(i, 1)];
                if (a == null) continue;
                d.Abilities[i] = new AbilityDefinition
                {
                    Slot = (AbilitySlot)i,
                    Name = a["name"].Text,
                    DamageType = a["damage_type"].Text == "magic" ? DamageType.Magic : DamageType.Physical,
                    BaseDamageByRank = FixList(a["base_damage_by_rank"], "base_damage_by_rank"),
                    TotalAdRatio = KitData.Fix(a["total_ad_ratio"], "total_ad_ratio"),
                    BonusAdRatio = KitData.Fix(a["bonus_ad_ratio"], "bonus_ad_ratio"),
                    Hits = int.Parse(a["hits"].Text, System.Globalization.CultureInfo.InvariantCulture),
                    CritEffectiveness = KitData.Fix(a["crit_effectiveness"], "crit_effectiveness"),
                    CooldownByRank = FixList(a["cooldown_by_rank"], "cooldown_by_rank"),
                    ManaCost = KitData.Fix(a["mana_cost"], "mana_cost"),
                };
            }
            string order = _root["skill_order"]?["order"]?.Text;
            if (order == null) throw new UnsupportedContentException(Id + ": skill_order missing");
            for (int i = 0; i < level && i < order.Length; i++)
                d.AbilityRanks[slots.IndexOf(order[i])]++;
            d.Kit = KitRegistry.Create(kit["hook"].Text, kit, abilities, d);
        }

        private static Fix64[] FixList(JsonNode list, string name)
        {
            var values = new Fix64[list.Items.Count];
            for (int i = 0; i < values.Length; i++) values[i] = KitData.Fix(list.Items[i], name);
            return values;
        }

        private JsonNode Field(string name)
        {
            JsonNode f = _root["stats"]?[name];
            if (f == null) throw new UnsupportedContentException(Id + ": missing stat " + name);
            return f;
        }

        private Fix64 Stat(string name)
        {
            JsonNode f = Field(name);
            JsonNode value = f["value"];
            if (value == null || value.Kind == JsonKind.Null)
                throw new UnsupportedContentException(Id + ": required stat " + name + " is unresolved");
            return Fix64.Parse(value.Text);
        }

        private Fix64 OptionalStat(string name, Fix64 fallback, string label)
        {
            JsonNode value = Field(name)["value"];
            if (value != null && value.Kind != JsonKind.Null) return Fix64.Parse(value.Text);
            if (!Unsupported.Contains(label)) Unsupported.Add(label);
            return fallback;
        }
    }
}
