using NUnit.Framework;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Determinism
{
    public class DeterminismTests
    {
        private static BasicAttackDuel Run(int ticks)
        {
            var duel = new BasicAttackDuel(new BasicAttackDuel.Settings(
                Fix64.Parse("83.59"), Fix64.Parse("0.9"), Fix64.Parse("0.2279635167173252"),
                Fix64.Parse("525"), Fix64.Parse("2800"), Fix64.FromInt(2000), Fix64.Parse("48.5")));
            for (int t = 0; t < ticks; t++) duel.Step();
            return duel;
        }

        [Test]
        public void SameInputsSameHash()
        {
            Assert.That(Run(900).Log.Hash, Is.EqualTo(Run(900).Log.Hash));
        }

        [Test]
        public void HashChangesWhenOutcomeChanges()
        {
            BasicAttackDuel a = Run(900);
            var b = new BasicAttackDuel(new BasicAttackDuel.Settings(
                Fix64.Parse("83.59"), Fix64.Parse("0.9"), Fix64.Parse("0.2279635167173252"),
                Fix64.Parse("525"), Fix64.Parse("2800"), Fix64.FromInt(2000), Fix64.Parse("48.6")));
            for (int t = 0; t < 900; t++) b.Step();
            Assert.That(a.Log.Hash, Is.Not.EqualTo(b.Log.Hash));
        }

        [Test]
        public void RandomStreamsAreIndependentAndRepeatable()
        {
            var a = new DeterministicRandom(42, 1);
            var b = new DeterministicRandom(42, 1);
            var c = new DeterministicRandom(42, 2);
            bool differs = false;
            for (int i = 0; i < 1000; i++)
            {
                uint x = a.NextUInt();
                Assert.That(x, Is.EqualTo(b.NextUInt()));
                differs |= x != c.NextUInt();
            }
            Assert.That(differs, Is.True);
        }
    }
}
