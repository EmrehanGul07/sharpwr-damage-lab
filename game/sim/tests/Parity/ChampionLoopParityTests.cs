using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NUnit.Framework;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Content;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Tests.Parity
{
    /// <summary>
    /// M1 acceptance #3: Samira (from content) auto-attacks a dummy to death in the full Match
    /// loop; every impact time, damage and the kill time match the Python Damage Lab.
    /// </summary>
    public class ChampionLoopParityTests
    {
        private static readonly JsonElement F = Fixtures.Load("samira-reference-v1.json");

        private static IEnumerable<TestCaseData> Scenarios()
        {
            foreach (JsonElement sc in F.GetProperty("champion_loop").GetProperty("scenarios").EnumerateArray())
                yield return new TestCaseData(sc.GetProperty("name").GetString()).SetName("Loop_" + sc.GetProperty("name").GetString());
        }

        [TestCaseSource(nameof(Scenarios))]
        public void SamiraKillsDummyLikePython(string name)
        {
            JsonElement sc = default;
            foreach (JsonElement s in F.GetProperty("champion_loop").GetProperty("scenarios").EnumerateArray())
                if (s.GetProperty("name").GetString() == name) sc = s;
            JsonElement i = sc.GetProperty("inputs");
            double loopTol = F.GetProperty("tolerance").GetProperty("loop_time_seconds").GetDouble();
            double dmgTol = F.GetProperty("tolerance").GetProperty("damage").GetDouble();

            string json = File.ReadAllText(Path.Combine(System.AppContext.BaseDirectory, "content", "samira.champion.json"));
            UnitDefinition samira = new ChampionContent(json).AtLevel(i.GetProperty("level").GetInt32());
            var m = new Match();
            int a = m.Spawn(samira, Team.Blue, FixVec2.Zero);
            int d = m.Spawn(UnitDefinition.Dummy(Fixtures.Fix(i.GetProperty("dummy_hp")), Fixtures.Fix(i.GetProperty("dummy_armor")), Fix64.Zero),
                            Team.Red, new FixVec2(Fixtures.Fix(i.GetProperty("distance")), Fix64.Zero));
            m.Step(new[] { Command.Attack(a, d) });
            while (m.Get(d).Alive && m.Tick < 30 * 70) m.Step();

            var hits = new List<CombatEvent>();
            foreach (CombatEvent e in m.Log.Events) if (e.Kind == CombatEventKind.DamageApplied) hits.Add(e);
            JsonElement impacts = sc.GetProperty("impacts");
            Assert.That(hits.Count, Is.EqualTo(impacts.GetArrayLength()), name);
            for (int k = 0; k < hits.Count; k++)
            {
                Assert.That(hits[k].Time.ToSecondsDouble(), Is.EqualTo(impacts[k].GetProperty("time").GetDouble()).Within(loopTol), $"{name} hit {k}");
                Assert.That(hits[k].Amount.ToDouble(), Is.EqualTo(impacts[k].GetProperty("damage").GetDouble()).Within(dmgTol), $"{name} hit {k}");
            }
            double maxDt = 0, maxDmg = 0;
            for (int k = 0; k < hits.Count; k++)
            {
                maxDt = System.Math.Max(maxDt, System.Math.Abs(hits[k].Time.ToSecondsDouble() - impacts[k].GetProperty("time").GetDouble()));
                maxDmg = System.Math.Max(maxDmg, System.Math.Abs(hits[k].Amount.ToDouble() - impacts[k].GetProperty("damage").GetDouble()));
            }
            TestContext.WriteLine($"REPORT: AA loop {name}: {hits.Count} hits, kill at {hits[hits.Count - 1].Time.ToSecondsDouble():F6} s, max |dt| {maxDt:E2} s, max |d dmg| {maxDmg:E2} HP");
            if (i.GetProperty("dummy_hp").GetDouble() == 2000 && i.GetProperty("dummy_armor").GetDouble() == 50)
                Assert.That(maxDt, Is.LessThanOrEqualTo(10e-6), "M1 acceptance #3: 2000 HP / 50 armor dummy within 10 us");
            Assert.That(m.Get(d).Alive, Is.False, name);
            Assert.That(hits[hits.Count - 1].Time.ToSecondsDouble(), Is.EqualTo(sc.GetProperty("killed_at").GetDouble()).Within(loopTol));
        }
    }
}
