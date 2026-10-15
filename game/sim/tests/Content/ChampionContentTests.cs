using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;
using NUnit.Framework;
using SharpWR.Sim.Content;
using SharpWR.Sim.Entities;

namespace SharpWR.Sim.Tests.Content
{
    public class ChampionContentTests
    {
        private static string SamiraJson() =>
            File.ReadAllText(Path.Combine(System.AppContext.BaseDirectory, "content", "samira.champion.json"));

        [Test]
        public void SamiraLevelStatsMatchPythonReference()
        {
            var content = new ChampionContent(SamiraJson());
            JsonElement fixture = Fixtures.Load("samira-reference-v1.json");
            double tol = fixture.GetProperty("tolerance").GetProperty("stat").GetDouble();
            foreach (JsonElement c in fixture.GetProperty("level_stats").GetProperty("cases").EnumerateArray())
            {
                UnitDefinition d = content.AtLevel(c.GetProperty("level").GetInt32());
                Assert.That(d.AttackDamage.ToDouble(), Is.EqualTo(c.GetProperty("ad").GetDouble()).Within(tol));
                Assert.That(d.MaxHealth.ToDouble(), Is.EqualTo(c.GetProperty("hp").GetDouble()).Within(tol));
                Assert.That(d.Armor.ToDouble(), Is.EqualTo(c.GetProperty("armor").GetDouble()).Within(tol));
                Assert.That(d.MagicResist.ToDouble(), Is.EqualTo(c.GetProperty("mr").GetDouble()).Within(tol));
                double bonus = c.GetProperty("base_bonus_as").GetDouble() + c.GetProperty("level_bonus_as").GetDouble();
                Assert.That(d.BonusAttackSpeed.ToDouble(), Is.EqualTo(bonus).Within(tol));
            }
        }

        [Test]
        public void UnresolvedRadiusIsLabelledNotInvented()
        {
            var content = new ChampionContent(SamiraJson());
            UnitDefinition d = content.AtLevel(1);
            Assert.That(d.Radius.Raw, Is.EqualTo(0));
            Assert.That(content.Unsupported.Exists(s => s.StartsWith("gameplay_radius unresolved")), Is.True);
            Assert.That(content.Shippable, Is.False);
        }

        [Test]
        public void UnresolvedRequiredStatThrows()
        {
            string json = Regex.Replace(SamiraJson(), "\"base_ad\":\\s*\\{\\s*\"value\":\\s*\"60\"", "\"base_ad\": {\"value\": null");
            Assert.That(json, Is.Not.EqualTo(SamiraJson()), "test setup edits base_ad");
            var content = new ChampionContent(json);
            Assert.Throws<UnsupportedContentException>(() => content.AtLevel(1));
        }

        [Test]
        public void MiniJsonKeepsNumbersAsText()
        {
            JsonNode n = JsonNode.Parse("{\"a\": [1.25, -3e-2, \"x\\u0041\"], \"b\": {\"c\": true, \"d\": null}}");
            Assert.That(n["a"].Items[0].Text, Is.EqualTo("1.25"));
            Assert.That(n["a"].Items[1].Text, Is.EqualTo("-3e-2"));
            Assert.That(n["a"].Items[2].Text, Is.EqualTo("xA"));
            Assert.That(n["b"]["c"].Bool, Is.True);
            Assert.That(n["b"]["d"].Kind, Is.EqualTo(JsonKind.Null));
        }
    }
}
