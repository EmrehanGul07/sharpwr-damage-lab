using System.Linq;
using NUnit.Framework;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Champions
{
    /// <summary>Kit rules that the rotation fixture does not exercise.</summary>
    public class SamiraKitTests
    {
        private static RejectReason Reason(CombatEvent e) => (RejectReason)e.ActionId;

        [Test]
        public void RWithoutStyleIsRejectedAndChangesNothing()
        {
            var m = new SamiraTestMatch(9, "400", "5000", "0", "0");
            m.At(0, m.Cast(AbilitySlot.R));
            m.RunUntil(3);
            Assert.That(m.Rejections().Select(Reason), Is.EqualTo(new[] { RejectReason.RequirementNotMet }));
            Assert.That(m.Match.Get(m.Samira).CooldownR.Micros, Is.EqualTo(0));
            Assert.That(m.Hits(), Is.Empty);
        }

        [Test]
        public void CooldownAndManaGates()
        {
            var m = new SamiraTestMatch(9, "400", "5000", "0", "0");
            Fix64 manaBefore = m.Match.Get(m.Samira).Mana;
            m.At(0, m.Cast(AbilitySlot.Q));
            m.At(15, m.Cast(AbilitySlot.Q));           // 0.5 s: rank-4 cooldown is 2 s
            m.RunUntil(30);
            Assert.That(m.Rejections().Select(Reason), Is.EqualTo(new[] { RejectReason.OnCooldown }));
            Assert.That(m.Match.Get(m.Samira).Mana <= manaBefore, Is.True);
            Assert.That(m.Hits().Count(h => h.Label == "Q"), Is.EqualTo(1));
        }

        [Test]
        public void CastDuringQCastTimeIsLocked()
        {
            var m = new SamiraTestMatch(9, "400", "5000", "0", "0");
            m.At(0, m.Cast(AbilitySlot.Q));
            m.At(3, m.Cast(AbilitySlot.W));           // 0.1 s < 0.25 s cast time
            m.RunUntil(30);
            Assert.That(m.Rejections().Select(Reason), Is.EqualTo(new[] { RejectReason.Locked }));
        }

        [Test]
        public void ESlashRangeQAndMeleeAttackGetPassive()
        {
            // At 150 units: Q becomes the slash (passive), basic attacks are blade attacks (passive, no travel).
            var m = new SamiraTestMatch(9, "150", "5000", "0", "0");
            m.At(0, Command.Attack(m.Samira, m.Dummy));
            m.At(1, Command.StopUnit(m.Samira));
            m.At(30, m.Cast(AbilitySlot.Q));
            m.RunUntil(60);
            var damage = m.Match.Log.Events.Where(e => e.Kind == CombatEventKind.DamageApplied).ToList();
            Assert.That(damage.Count(e => e.DamageType == DamageType.Magic), Is.EqualTo(2), "AA + Q slash passive");
            var aaStart = m.Match.Log.Events.First(e => e.Kind == CombatEventKind.AttackStart);
            var aaHit = damage.First();
            Fix64 windup = m.Match.DefinitionOf(m.Samira).WindupSeconds;
            Assert.That(aaHit.Time.Micros - aaStart.Time.Micros, Is.EqualTo(Core.SimTime.FromSeconds(windup).Micros), "blade attack has no travel");
        }

        [Test]
        public void RCancelsPendingWSecondHit()
        {
            var m = new SamiraTestMatch(9, "400", "100000", "0", "0");   // post-dash gap 250 <= W radius 325
            // Build S Style: AA, Q, AA, E, W (first hit) then R before W's second hit.
            m.At(0, Command.Attack(m.Samira, m.Dummy)); m.At(1, Command.StopUnit(m.Samira));
            m.At(15, m.Cast(AbilitySlot.Q));
            m.At(45, Command.Attack(m.Samira, m.Dummy)); m.At(46, Command.StopUnit(m.Samira));
            m.At(75, m.Cast(AbilitySlot.Q));
            m.At(90, m.Cast(AbilitySlot.E));
            m.At(105, m.Cast(AbilitySlot.W));          // hits at +0.1 s and +0.85 s
            m.At(111, m.Cast(AbilitySlot.R));          // +0.2 s: after W hit 1, before W hit 2
            m.RunUntil(240);
            Assert.That(m.Rejections(), Is.Empty);
            Assert.That(m.Hits().Count(h => h.Label == "W"), Is.EqualTo(1), "second W hit cancelled by R");
            Assert.That(m.Hits().Count(h => h.Label == "R tick"), Is.EqualTo(10));
        }

        [Test]
        public void QDuringEDashIsAnUnsupportedMechanic()
        {
            var m = new SamiraTestMatch(9, "500", "5000", "0", "0");
            m.At(0, m.Cast(AbilitySlot.E));
            m.At(3, m.Cast(AbilitySlot.Q));            // 0.1 s: dash lasts 650/1600 s
            m.RunUntil(30);
            Assert.That(m.Rejections().Select(Reason), Is.EqualTo(new[] { RejectReason.UnsupportedMechanic }));
        }

        [Test]
        public void NotEnoughManaIsRejectedWithoutSpendingCooldown()
        {
            var m = new SamiraTestMatch(9, "400", "5000", "0", "0");
            m.Match.DefinitionOf(m.Samira).MaxMana = Fix64.FromInt(0);   // test-only: empty pool, no regen
            m.Match.DefinitionOf(m.Samira).ManaRegenPer5s = Fix64.Zero;
            m.At(0, m.Cast(AbilitySlot.Q));
            m.RunUntil(3);
            Assert.That(m.Rejections().Select(Reason), Is.EqualTo(new[] { RejectReason.NotEnoughResource }));
            Assert.That(m.Match.Get(m.Samira).CooldownQ.Micros, Is.EqualTo(0));
        }

        [Test]
        public void QMissesWhenAimedAway()
        {
            var m = new SamiraTestMatch(9, "600", "5000", "0", "0");
            m.At(0, new Command(m.Samira, CommandKind.Cast, 0, new FixVec2(Fix64.Zero, Fix64.FromInt(500)), (byte)AbilitySlot.Q));
            m.RunUntil(60);
            Assert.That(m.Hits(), Is.Empty);
        }

        [Test]
        public void DeterministicHash()
        {
            ulong Run()
            {
                var m = new SamiraTestMatch(15, "500", "6000", "60", "40");
                m.At(0, Command.Attack(m.Samira, m.Dummy));
                m.At(20, m.Cast(AbilitySlot.Q));
                m.At(60, m.Cast(AbilitySlot.E));
                m.At(80, m.Cast(AbilitySlot.W));
                m.At(120, Command.Attack(m.Samira, m.Dummy));
                m.RunUntil(600);
                return m.Match.StateHash();
            }
            Assert.That(Run(), Is.EqualTo(Run()));
        }
    }
}
