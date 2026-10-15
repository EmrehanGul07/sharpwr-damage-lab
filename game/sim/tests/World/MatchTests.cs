using System.Collections.Generic;
using NUnit.Framework;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Tests.World
{
    /// <summary>Engine behaviour with neutral test units (no champion data involved).</summary>
    public class MatchTests
    {
        private static Fix64 F(string s) => Fix64.Parse(s);
        private static FixVec2 P(string x, string z) => new FixVec2(F(x), F(z));

        private static UnitDefinition Ranged(string moveSpeed = "300") => new UnitDefinition
        {
            Id = "test.ranged", MaxHealth = F("500"), Armor = F("0"), MagicResist = F("0"),
            BaseAttackDamage = F("50"), AttackDamage = F("50"), BaseAttackSpeed = F("1"),
            AttackSpeedRatio = F("1"), BonusAttackSpeed = F("0"), BaseWindupSeconds = F("0.25"),
            WindupBonusAsFactor = F("0.5"), AttackRange = F("500"), ProjectileSpeed = F("2000"),
            MoveSpeed = F(moveSpeed),
        };

        private static UnitDefinition Melee() => new UnitDefinition
        {
            Id = "test.melee", MaxHealth = F("100"), Armor = F("0"), MagicResist = F("0"),
            BaseAttackDamage = F("100"), AttackDamage = F("100"), BaseAttackSpeed = F("1"),
            AttackSpeedRatio = F("1"), BaseWindupSeconds = F("0.3"), WindupBonusAsFactor = F("0.5"),
            AttackRange = F("150"), ProjectileSpeed = F("0"), MoveSpeed = F("300"),
        };

        private static List<CombatEvent> Of(Match m, CombatEventKind kind)
        {
            var list = new List<CombatEvent>();
            foreach (CombatEvent e in m.Log.Events) if (e.Kind == kind) list.Add(e);
            return list;
        }

        private static void Run(Match m, int ticks, params Command[] first)
        {
            m.Step(first);
            for (int i = 1; i < ticks; i++) m.Step();
        }

        [Test]
        public void MoveReachesTargetAtMoveSpeed()
        {
            var m = new Match();
            int a = m.Spawn(Ranged("300"), Team.Blue, P("0", "0"));
            Run(m, 30, Command.MoveTo(a, P("600", "0")));     // 1 s at 300 u/s
            Assert.That(m.Get(a).Position.X.ToDouble(), Is.EqualTo(300).Within(1e-6));
            Run(m, 31);
            Assert.That(m.Get(a).Position.Equals(P("600", "0")), Is.True);
            Assert.That(m.Get(a).Order, Is.EqualTo(OrderKind.None));
        }

        [Test]
        public void AttackStartsImmediatelyInRangeAndRepeatsOnTimer()
        {
            var m = new Match();
            int a = m.Spawn(Ranged(), Team.Blue, P("0", "0"));
            int d = m.Spawn(UnitDefinition.Dummy(F("10000"), F("0"), F("0")), Team.Red, P("400", "0"));
            Run(m, 95, Command.Attack(a, d));                  // ~3.13 s
            List<CombatEvent> starts = Of(m, CombatEventKind.AttackStart);
            Assert.That(starts.Count, Is.EqualTo(4));
            Assert.That(starts[0].Time.Micros, Is.EqualTo(0));
            Assert.That(starts[1].Time.Micros, Is.EqualTo(1_000_000));   // AS 1.0: exact, not tick-quantized
            List<CombatEvent> hits = Of(m, CombatEventKind.DamageApplied);
            Assert.That(hits[0].Time.Micros, Is.EqualTo(250_000 + 200_000)); // windup + 400/2000 s travel
            Assert.That(hits[0].Amount, Is.EqualTo(F("50")));
        }

        [Test]
        public void ChasesIntoRangeThenAttacks()
        {
            var m = new Match();
            int a = m.Spawn(Ranged("300"), Team.Blue, P("0", "0"));
            int d = m.Spawn(UnitDefinition.Dummy(F("10000"), F("0"), F("0")), Team.Red, P("800", "0"));
            Run(m, 45, Command.Attack(a, d));
            Assert.That(m.Get(a).Position.X.ToDouble(), Is.EqualTo(300).Within(1e-6), "stops at range 500");
            Assert.That(Of(m, CombatEventKind.AttackStart).Count, Is.GreaterThan(0));
        }

        [Test]
        public void CommandDuringWindupIsBufferedNotCancelling()
        {
            var m = new Match();
            int a = m.Spawn(Ranged(), Team.Blue, P("0", "0"));
            int d = m.Spawn(UnitDefinition.Dummy(F("10000"), F("0"), F("0")), Team.Red, P("400", "0"));
            m.Step(new[] { Command.Attack(a, d) });
            m.Step(new[] { Command.MoveTo(a, P("0", "500")) });  // windup ends at 0.25 s
            Run(m, 30);
            Assert.That(Of(m, CombatEventKind.DamageApplied).Count, Is.EqualTo(1), "windup attack still lands");
            Assert.That(m.Get(a).Position.Z > F("0"), Is.True, "move applied after windup");
            Assert.That(Of(m, CombatEventKind.AttackStart).Count, Is.EqualTo(1), "attack order replaced");
        }

        [Test]
        public void DeathThenRespawnAfterFiveSecondsAtSpawnWithFullHealth()
        {
            var m = new Match();
            int a = m.Spawn(Ranged(), Team.Blue, P("0", "0"));
            int d = m.Spawn(UnitDefinition.Dummy(F("120"), F("0"), F("0")), Team.Red, P("400", "0"));
            Run(m, 90, Command.Attack(a, d));                  // 3 hits of 50 > 120 HP
            List<CombatEvent> deaths = Of(m, CombatEventKind.Death);
            Assert.That(deaths.Count, Is.EqualTo(1));
            List<CombatEvent> hits = Of(m, CombatEventKind.DamageApplied);
            Assert.That(hits[2].Amount, Is.EqualTo(F("20")), "killing hit logs HP actually removed");
            Assert.That(m.Get(d).Alive, Is.False);
            Assert.That(m.Get(a).Order, Is.EqualTo(OrderKind.None), "attacker drops dead target");
            Run(m, 160);
            Assert.That(m.Get(d).Alive, Is.True);
            Assert.That(m.Get(d).Health, Is.EqualTo(F("120")));
            Assert.That(Of(m, CombatEventKind.Respawn)[0].Time.Micros - deaths[0].Time.Micros, Is.EqualTo(5_000_000));
        }

        [Test]
        public void SimultaneousLethalTradeKillsBoth()
        {
            var m = new Match();
            int a = m.Spawn(Melee(), Team.Blue, P("0", "0"));
            int b = m.Spawn(Melee(), Team.Red, P("100", "0"));
            Run(m, 30, Command.Attack(a, b), Command.Attack(b, a));
            Assert.That(Of(m, CombatEventKind.Death).Count, Is.EqualTo(2));
        }

        [Test]
        public void InvalidCommandsAreRejectedWithoutStateChange()
        {
            var m = new Match();
            int a = m.Spawn(Ranged(), Team.Blue, P("0", "0"));
            int ally = m.Spawn(Ranged(), Team.Blue, P("100", "0"));
            Unit before = m.Get(a);
            m.Step(new[] { Command.Attack(a, ally), Command.Attack(a, a), Command.Attack(99, a) });
            Assert.That(Of(m, CombatEventKind.Rejected).Count, Is.EqualTo(3));
            Unit after = m.Get(a);
            Assert.That(after.Order, Is.EqualTo(before.Order));
            Assert.That(after.Position.Equals(before.Position), Is.True);
        }

        private static ulong Scripted(int ticks, int cloneAt, out ulong cloneHash)
        {
            var m = new Match();
            int a = m.Spawn(Ranged(), Team.Blue, P("0", "0"));
            int b = m.Spawn(Ranged("320"), Team.Red, P("900", "250"));
            Match clone = null;
            for (int t = 0; t < ticks; t++)
            {
                var cmds = new List<Command>();
                if (t == 0) { cmds.Add(Command.Attack(a, b)); cmds.Add(Command.Attack(b, a)); }
                if (t == 40) cmds.Add(Command.MoveTo(b, P("1200", "-300")));
                if (t == 70) cmds.Add(Command.Attack(b, a));
                if (t == cloneAt) clone = m.Clone();
                m.Step(cmds);
                if (clone != null && t >= cloneAt) clone.Step(cmds);
            }
            cloneHash = clone.StateHash();
            return m.StateHash();
        }

        [Test]
        public void DeterministicAndCloneable()
        {
            ulong first = Scripted(600, 200, out ulong cloned);
            ulong second = Scripted(600, 300, out _);
            Assert.That(second, Is.EqualTo(first), "same inputs, same hash");
            Assert.That(cloned, Is.EqualTo(first), "clone continues identically (rollback contract)");
        }
    }
}
