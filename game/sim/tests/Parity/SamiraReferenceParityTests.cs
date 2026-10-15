using System;
using System.Collections.Generic;
using System.Text.Json;
using NUnit.Framework;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Parity
{
    /// <summary>
    /// C# sim vs Python Damage Lab (fixture samira-reference-v1.json). Reference-only Riot data:
    /// lives in tests, never in shippable content (docs/moba/10-legal-and-ip.md).
    /// </summary>
    public class SamiraReferenceParityTests
    {
        private static readonly JsonElement F = Fixtures.Load("samira-reference-v1.json");
        private static double Tol(string kind) => F.GetProperty("tolerance").GetProperty(kind).GetDouble();

        // Inputs exactly as the content importer will provide them (decimal text).
        private static readonly Dictionary<string, (string[] Base, string TotalAd, string BonusAd, string Crit)> Skills =
            new Dictionary<string, (string[], string, string, string)>
            {
                ["Q"] = (new[] { "15", "20", "25", "30" }, "1.25", "0", "0.5"),
                ["W"] = (new[] { "20", "40", "60", "80" }, "0", "0.5", "0"),
                ["E"] = (new[] { "45", "60", "75", "90" }, "0", "0.2", "0"),
                ["R"] = (new[] { "20", "40", "60" }, "0.5", "0", "1"),
            };

        [Test]
        public void LevelStats()
        {
            var p = new Dictionary<string, (string Base, string Growth)>
            {
                ["ad"] = ("60", "3.5"), ["hp"] = ("630", "128"), ["armor"] = ("35", "5"), ["mr"] = ("30", "1.4"),
            };
            foreach (JsonElement c in F.GetProperty("level_stats").GetProperty("cases").EnumerateArray())
            foreach (var kv in p)
            {
                double got = CombatMath.StatAtLevel(Fix64.Parse(kv.Value.Base), Fix64.Parse(kv.Value.Growth),
                                                    c.GetProperty("level").GetInt32()).ToDouble();
                Assert.That(got, Is.EqualTo(c.GetProperty(kv.Key).GetDouble()).Within(Tol("stat")), kv.Key);
            }
        }

        [Test]
        public void Resistance()
        {
            foreach (JsonElement c in F.GetProperty("resistance").GetProperty("cases").EnumerateArray())
            {
                Fix64 eff = CombatMath.EffectiveResistance(Fixtures.Fix(c.GetProperty("resistance")),
                    Fixtures.Fix(c.GetProperty("pct_pen")), Fixtures.Fix(c.GetProperty("flat_pen")));
                Assert.That(eff.ToDouble(), Is.EqualTo(c.GetProperty("effective").GetDouble()).Within(Tol("stat")));
                Assert.That(CombatMath.ResistanceMultiplier(eff).ToDouble(),
                            Is.EqualTo(c.GetProperty("multiplier").GetDouble()).Within(Tol("multiplier")));
            }
        }

        [Test]
        public void AbilityDamage()
        {
            int checkedCases = 0;
            foreach (JsonElement c in F.GetProperty("skills").GetProperty("cases").EnumerateArray())
            {
                var s = Skills[c.GetProperty("slot").GetString()];
                int rank = c.GetProperty("rank").GetInt32();
                bool magic = c.GetProperty("slot").GetString() == "E";
                Fix64 raw = CombatMath.ScaledAbility(Fix64.Parse(s.Base[rank - 1]), Fix64.Parse(s.TotalAd),
                    Fix64.Parse(s.BonusAd), Fixtures.Fix(c.GetProperty("ad")), Fixtures.Fix(c.GetProperty("base_ad")));
                Fix64 hit = CombatMath.CritScaled(raw, Fix64.Parse(s.Crit), Fixtures.Fix(c.GetProperty("crit_damage")),
                                                  c.GetProperty("outcome").GetString() == "Critical");
                Fix64 resist = Fixtures.Fix(c.GetProperty(magic ? "mr" : "armor"));
                Fix64 total = Fix64.Zero;
                for (int i = 0; i < c.GetProperty("hits").GetInt32(); i++)
                    total += CombatMath.Mitigate(hit, resist, Fix64.Zero, Fix64.Zero);
                Assert.That(total.ToDouble(), Is.EqualTo(c.GetProperty("dealt_total").GetDouble()).Within(Tol("damage")),
                            c.GetRawText());
                checkedCases++;
            }
            Assert.That(checkedCases, Is.EqualTo(270));
        }

        [Test]
        public void BasicAttackTimelineOnFixedClock()
        {
            foreach (JsonElement sc in F.GetProperty("timeline").GetProperty("scenarios").EnumerateArray())
            {
                JsonElement i = sc.GetProperty("inputs");
                var duel = new BasicAttackDuel(new BasicAttackDuel.Settings(
                    Fixtures.Fix(i.GetProperty("ad")), Fixtures.Fix(i.GetProperty("attack_speed")),
                    Fixtures.Fix(i.GetProperty("aa_windup_seconds")), Fixtures.Fix(i.GetProperty("distance")),
                    Fixtures.Fix(i.GetProperty("projectile_speed")), Fix64.FromInt(10_000),
                    Fixtures.Fix(i.GetProperty("target_armor"))));
                long untilMicros = (long)System.Math.Round(i.GetProperty("until_seconds").GetDouble() * 1e6);
                while (duel.Now.Micros < untilMicros) duel.Step();

                var damage = new List<CombatEvent>();
                foreach (CombatEvent e in duel.Log.Events)
                    if (e.Kind == CombatEventKind.DamageApplied && e.Time.Micros <= untilMicros) damage.Add(e);

                var expected = new List<JsonElement>();
                foreach (JsonElement e in sc.GetProperty("impacts").EnumerateArray())
                    if (e.GetProperty("action").GetString() == "AA") expected.Add(e);

                string name = sc.GetProperty("name").GetString();
                Assert.That(damage.Count, Is.EqualTo(expected.Count), name);
                for (int k = 0; k < damage.Count; k++)
                {
                    Assert.That(damage[k].Time.ToSecondsDouble(),
                                Is.EqualTo(expected[k].GetProperty("time").GetDouble()).Within(Tol("time_seconds")), name);
                    Assert.That(damage[k].Amount.ToDouble(),
                                Is.EqualTo(expected[k].GetProperty("damage").GetDouble()).Within(Tol("damage")), name);
                }
            }
        }
    }
}
