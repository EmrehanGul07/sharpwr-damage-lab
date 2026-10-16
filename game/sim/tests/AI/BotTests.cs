using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.AI;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Content;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Tests.AI
{
    public class BotTests
    {
        private static string Read(string name) => File.ReadAllText(Path.Combine(System.AppContext.BaseDirectory, "content", name));
        private static UnitDefinition Samira(int level) => new ChampionContent(Read("samira.champion.json")).AtLevel(level);
        private static BotProfile Profile(string difficulty) => BotProfile.Load(Read("duel-bot.profiles.json"), difficulty, "ref.samira");
        private static readonly string[] Difficulties = { "easy", "medium", "hard", "impossible" };

        private static DuelSession BotDuel(int seed, string blue, string red, out int a, out int b)
        {
            var match = new Match();
            a = match.Spawn(Samira(9), Team.Blue, FixVec2.Zero);
            b = match.Spawn(Samira(9), Team.Red, new FixVec2(Fix64.FromInt(900), Fix64.FromInt(seed % 7 * 40 - 120)));
            var session = new DuelSession(match);
            session.AddBot(new BotBrain(Profile(blue), a, b, (ulong)seed));
            session.AddBot(new BotBrain(Profile(red), b, a, (ulong)(seed * 31 + 7)));
            return session;
        }

        private static bool AnyDeath(Match m)
        {
            foreach (CombatEvent e in m.Log.Events) if (e.Kind == CombatEventKind.Death) return true;
            return false;
        }

        [Test]
        public void ProfilesConvertMillisecondsToTicks()
        {
            Assert.That(Profile("easy").ObservationDelayTicks, Is.EqualTo(20));        // 650 ms
            Assert.That(Profile("impossible").ObservationDelayTicks, Is.EqualTo(2));   // 50 ms -> 1.5 ticks, half up
            Assert.That(Profile("impossible").DecisionIntervalTicks, Is.EqualTo(1));
            Assert.That(Profile("hard").UseRange[(int)AbilitySlot.Q].ToDouble(), Is.EqualTo(900));
        }

        [Test]
        public void FiftySeededBotDuelsTerminateDeterministically()
        {
            int deaths = 0;
            for (int seed = 1; seed <= 50; seed++)
            {
                string blue = Difficulties[seed % 4], red = Difficulties[(seed / 4) % 4];
                DuelSession s = BotDuel(seed, blue, red, out _, out _);
                int limit = 180 * SimClock.TicksPerSecond;
                while (s.Match.Tick < limit && !AnyDeath(s.Match)) s.Step();
                if (AnyDeath(s.Match)) deaths++;
            }
            Assert.That(deaths, Is.GreaterThan(0), "bots must actually fight");

            ulong Run(int cloneAt, out ulong cloned)
            {
                DuelSession s = BotDuel(7, "hard", "medium", out _, out _);
                DuelSession copy = null;
                for (int t = 0; t < 1800; t++)
                {
                    if (t == cloneAt) copy = s.Clone();
                    s.Step();
                    copy?.Step();
                }
                cloned = copy.Match.StateHash();
                return s.Match.StateHash();
            }
            ulong first = Run(300, out ulong clonedFirst);
            ulong second = Run(900, out _);
            Assert.That(second, Is.EqualTo(first), "same seed, same match");
            Assert.That(clonedFirst, Is.EqualTo(first), "cloned session continues identically");
        }

        [Test]
        public void DifficultyNeverChangesStats()
        {
            foreach (string difficulty in Difficulties)
            {
                DuelSession s = BotDuel(3, difficulty, "medium", out int a, out int b);
                UnitDefinition before = Samira(9);
                for (int t = 0; t < 900; t++) s.Step();
                foreach (int id in new[] { a, b })
                {
                    UnitDefinition d = s.Match.DefinitionOf(id);
                    Assert.That(d.MaxHealth, Is.EqualTo(before.MaxHealth), difficulty);
                    Assert.That(d.AttackDamage, Is.EqualTo(before.AttackDamage), difficulty);
                    Assert.That(d.AttackSpeed, Is.EqualTo(before.AttackSpeed), difficulty);
                    Assert.That(d.MoveSpeed, Is.EqualTo(before.MoveSpeed), difficulty);
                }
            }
        }

        private static int QHitsOnBot(string difficulty, int shots)
        {
            var match = new Match();
            UnitDefinition shooterDef = Samira(9);
            shooterDef.MaxHealth = Fix64.FromInt(1_000_000);    // test-only: the shooter must survive
            int shooter = match.Spawn(shooterDef, Team.Blue, FixVec2.Zero);
            int bot = match.Spawn(Samira(9), Team.Red, new FixVec2(Fix64.FromInt(800), Fix64.Zero));
            var session = new DuelSession(match);
            BotProfile profile = Profile(difficulty);
            profile.Priority = "";                               // isolate dodging: the bot does not cast
            session.AddBot(new BotBrain(profile, bot, shooter, 11));
            var cast = new List<Command>(1);
            for (int i = 0; i < shots; i++)
            {
                cast.Clear();
                if (match.Get(bot).Alive)
                    cast.Add(new Command(shooter, CommandKind.Cast, bot, match.Get(bot).Position, (byte)AbilitySlot.Q));
                session.Step(cast);
                for (int t = 1; t < 90; t++) session.Step();
            }
            int hits = 0;
            foreach (CombatEvent e in match.Log.Events)
                if (e.Kind == CombatEventKind.DamageApplied && e.Source == shooter && e.Target == bot &&
                    ActionIds.IsAbility(e.ActionId) && ActionIds.SlotOf(e.ActionId) == AbilitySlot.Q) hits++;
            return hits;
        }

        [Test]
        public void HarderBotsDodgeMoreSkillshots()
        {
            const int shots = 20;
            int easy = QHitsOnBot("easy", shots);
            int impossible = QHitsOnBot("impossible", shots);
            TestContext.WriteLine($"REPORT: Q hits: easy {easy}/{shots}, impossible {impossible}/{shots}");
            Assert.That(easy, Is.GreaterThanOrEqualTo(14), "easy bot (8% dodge, 650 ms delay) mostly gets hit");
            Assert.That(impossible, Is.LessThanOrEqualTo(10), "impossible bot dodges most telegraphed Qs");
            Assert.That(impossible, Is.LessThan(easy));
        }
    }
}
