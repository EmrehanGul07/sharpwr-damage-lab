using System;
using System.Collections.Generic;
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
            var d = new UnitDefinition
            {
                Id = Id,
                MaxHealth = CombatMath.StatAtLevel(Stat("base_hp"), Stat("hp_per_level"), level),
                Armor = CombatMath.StatAtLevel(Stat("base_armor"), Stat("armor_per_level"), level),
                MagicResist = CombatMath.StatAtLevel(Stat("base_mr"), Stat("mr_per_level"), level),
                BaseAttackDamage = Stat("base_ad"),
                AttackDamage = CombatMath.StatAtLevel(Stat("base_ad"), Stat("ad_per_level"), level),
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
            return d;
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
