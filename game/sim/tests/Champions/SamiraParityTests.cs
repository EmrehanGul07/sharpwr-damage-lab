using System.Collections.Generic;
using System.Text.Json;
using NUnit.Framework;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Champions
{
    /// <summary>
    /// M1 acceptance #4: scripted Q/W/E/R rotation reproduces the Python Damage Lab event by
    /// event (fixture ability_script): times, damage per hit, Style progression, R gate,
    /// and the rejected Q during R.
    /// </summary>
    public class SamiraParityTests
    {
        private static readonly JsonElement F = Fixtures.Load("samira-reference-v1.json");

        private static SamiraTestMatch RunScript(out JsonElement fixture)
        {
            fixture = F.GetProperty("ability_script");
            JsonElement i = fixture.GetProperty("inputs");
            var m = new SamiraTestMatch(i.GetProperty("level").GetInt32(), i.GetProperty("distance").GetRawText(),
                                        i.GetProperty("dummy_hp").GetRawText(), i.GetProperty("dummy_armor").GetRawText(),
                                        i.GetProperty("dummy_mr").GetRawText());
            foreach (JsonElement step in i.GetProperty("script").EnumerateArray())
            {
                long tick = (long)System.Math.Round(step.GetProperty("time").GetDouble() * SimClock.TicksPerSecond);
                Assert.That(SimClock.TickStart(tick).Micros, Is.EqualTo((long)System.Math.Round(step.GetProperty("time").GetDouble() * 1e6)),
                            "script times must fall on tick starts");
                switch (step.GetProperty("action").GetString())
                {
                    case "AA":
                        // The Damage Lab fires exactly one attack per scripted AA: attack, then a stop
                        // that is buffered until the windup ends.
                        m.At(tick, Command.Attack(m.Samira, m.Dummy));
                        m.At(tick + 1, Command.StopUnit(m.Samira));
                        break;
                    case "Q": m.At(tick, m.Cast(AbilitySlot.Q)); break;
                    case "W": m.At(tick, m.Cast(AbilitySlot.W)); break;
                    case "E": m.At(tick, m.Cast(AbilitySlot.E)); break;
                    case "R": m.At(tick, m.Cast(AbilitySlot.R)); break;
                }
            }
            m.RunUntil(SimClock.TicksPerSecond * 8);
            return m;
        }

        [Test]
        public void ScriptedRotationMatchesPython()
        {
            SamiraTestMatch m = RunScript(out JsonElement fx);
            double timeTol = F.GetProperty("tolerance").GetProperty("time_seconds").GetDouble();
            double dmgTol = F.GetProperty("tolerance").GetProperty("damage").GetDouble();
            List<(long Micros, string Label, Fix64 Damage)> hits = m.Hits();
            JsonElement impacts = fx.GetProperty("impacts");
            var report = new System.Text.StringBuilder();
            foreach (var h in hits) report.Append($"{h.Micros / 1e6:F6} {h.Label} {h.Damage.ToDouble():F4}\n");
            Assert.That(hits.Count, Is.EqualTo(impacts.GetArrayLength()), "C# hits:\n" + report);
            double maxTime = 0, maxDamage = 0;
            for (int k = 0; k < hits.Count; k++)
            {
                maxTime = System.Math.Max(maxTime, System.Math.Abs(hits[k].Micros / 1e6 - impacts[k].GetProperty("time").GetDouble()));
                maxDamage = System.Math.Max(maxDamage, System.Math.Abs(hits[k].Damage.ToDouble() - impacts[k].GetProperty("damage").GetDouble()));
            }
            TestContext.WriteLine($"REPORT: Samira rotation parity: {hits.Count} hits, max |dt| {maxTime:E2} s, max |d dmg| {maxDamage:E2} HP");
            for (int k = 0; k < hits.Count; k++)
            {
                JsonElement want = impacts[k];
                string ctx = $"hit {k}: C# {report.ToString().Split('\n')[k]} vs Python {want.GetRawText()}";
                Assert.That(hits[k].Label, Is.EqualTo(want.GetProperty("action").GetString()), ctx);
                Assert.That(hits[k].Micros / 1e6, Is.EqualTo(want.GetProperty("time").GetDouble()).Within(timeTol), ctx);
                Assert.That(hits[k].Damage.ToDouble(), Is.EqualTo(want.GetProperty("damage").GetDouble()).Within(dmgTol), ctx);
            }
        }

        [Test]
        public void RejectedCastsMatchPython()
        {
            SamiraTestMatch m = RunScript(out JsonElement fx);
            var rejected = m.Rejections();
            JsonElement want = fx.GetProperty("rejected");
            Assert.That(rejected.Count, Is.EqualTo(want.GetArrayLength()));
            Assert.That(rejected[0].Time.Micros / 1e6, Is.EqualTo(want[0].GetProperty("time").GetDouble()).Within(1e-9));
            Assert.That((RejectReason)rejected[0].ActionId, Is.EqualTo(RejectReason.Locked), "Q during R channel");
        }

        [Test]
        public void StyleIsConsumedAtChannelEnd()
        {
            SamiraTestMatch m = RunScript(out _);
            Assert.That(m.Match.Get(m.Samira).KitStacks, Is.EqualTo(0));
        }
    }
}
