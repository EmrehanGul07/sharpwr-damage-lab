using System.Text.Json;
using NUnit.Framework;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Numerics
{
    /// <summary>Bit-exact agreement with tools/parity/fixed_point_model.py.</summary>
    public class Fix64VectorTests
    {
        private static readonly JsonElement V = Fixtures.Load("fix64-vectors-v1.json");

        [Test]
        public void ParseMatchesModel()
        {
            foreach (JsonElement c in V.GetProperty("parse").EnumerateArray())
                Assert.That(Fix64.Parse(c.GetProperty("text").GetString()).Raw,
                            Is.EqualTo(c.GetProperty("raw").GetInt64()), c.GetProperty("text").GetString());
        }

        [Test]
        public void MulAndDivMatchModel()
        {
            foreach (string op in new[] { "mul", "div" })
            foreach (JsonElement c in V.GetProperty(op).EnumerateArray())
            {
                Fix64 a = Fix64.Parse(c.GetProperty("a").GetString());
                Fix64 b = Fix64.Parse(c.GetProperty("b").GetString());
                long got = op == "mul" ? (a * b).Raw : (a / b).Raw;
                Assert.That(got, Is.EqualTo(c.GetProperty("raw").GetInt64()), $"{op} {a} {b}");
            }
        }

        [Test]
        public void GrowthUnitsAndMicrosMatchModel()
        {
            foreach (JsonElement c in V.GetProperty("growth_units").EnumerateArray())
                Assert.That(CombatMath.GrowthUnits(c.GetProperty("level").GetInt32()).Raw,
                            Is.EqualTo(c.GetProperty("raw").GetInt64()));
            foreach (JsonElement c in V.GetProperty("seconds_to_micros").EnumerateArray())
                Assert.That(SimTime.FromSeconds(Fix64.Parse(c.GetProperty("seconds").GetString())).Micros,
                            Is.EqualTo(c.GetProperty("micros").GetInt64()));
        }

        [Test]
        public void OverflowThrowsInsteadOfWrapping()
        {
            Fix64 big = Fix64.FromLong(int.MaxValue);
            Assert.Throws<System.OverflowException>(() => { _ = big * big; });
            Assert.Throws<System.OverflowException>(() => { _ = big / Fix64.Parse("0.25"); });
        }
    }
}
