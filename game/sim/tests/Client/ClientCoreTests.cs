using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using SharpWR.Client;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Tests.Client
{
    public class ClientCoreTests
    {
        private static string Read(string name) => File.ReadAllText(Path.Combine(System.AppContext.BaseDirectory, "content", name));
        private static PracticeGame Practice(string difficulty = "medium", ulong seed = 5) =>
            PracticeGame.Create(Read("samira.champion.json"), Read("duel-bot.profiles.json"), 9, difficulty, seed);

        [Test]
        public void FixedStepHostCapsAndInterpolates()
        {
            var host = new FixedStepHost();
            Assert.That(host.Advance(1.0 / 60), Is.EqualTo(0));
            Assert.That(host.Alpha, Is.EqualTo(0.5).Within(1e-9));
            Assert.That(host.Advance(1.0 / 60), Is.EqualTo(1));
            Assert.That(host.Advance(1.0), Is.EqualTo(3), "a long frame never runs more than 3 ticks");
            Assert.That(host.Alpha, Is.EqualTo(0));
            Assert.That(host.Advance(double.NaN), Is.EqualTo(0));
        }

        [Test]
        public void JoystickDeadZoneThrottleAndRelease()
        {
            PracticeGame g = Practice();
            var input = new InputMapper(g.Player);
            Assert.That(input.Joystick(0.05, 0, g.Session.Match), Is.Null, "dead zone");
            Command? first = input.Joystick(1, 0, g.Session.Match);
            Assert.That(first.HasValue && first.Value.Kind == CommandKind.Move, Is.True);
            Assert.That(first.Value.Point.X.ToDouble(), Is.EqualTo(200).Within(1e-9));
            Assert.That(input.Joystick(1, 0.01, g.Session.Match), Is.Null, "same direction, same tick: throttled");
            Assert.That(input.Joystick(0, 1, g.Session.Match).HasValue, Is.True, "sharp turn reissues");
            Command? stop = input.Joystick(0, 0, g.Session.Match);
            Assert.That(stop.HasValue && stop.Value.Kind == CommandKind.Stop, Is.True);
            Assert.That(input.Joystick(0, 0, g.Session.Match), Is.Null, "stop is sent once");
        }

        [Test]
        public void QuantizationIsExactSixtyFourths()
        {
            Assert.That(InputMapper.Quantize(1.0 / 64).Raw, Is.EqualTo(1L << 26));
            Assert.That(InputMapper.Quantize(-3.5).Raw, Is.EqualTo(Fix64.Parse("-3.5").Raw));
            Assert.That(InputMapper.Quantize(0.004).Raw, Is.EqualTo(0));
        }

        [Test]
        public void ClickAttacksEnemyUnderCursorElseMoves()
        {
            PracticeGame g = Practice();
            var input = new InputMapper(g.Player);
            Command onDummy = input.Click(g.Session.Match, 610, 290);
            Assert.That(onDummy.Kind, Is.EqualTo(CommandKind.AttackUnit));
            Assert.That(onDummy.TargetUnit, Is.EqualTo(g.Dummy));
            Assert.That(input.Click(g.Session.Match, -300, 0).Kind, Is.EqualTo(CommandKind.Move));
            Command e = input.Cast(g.Session.Match, AbilitySlot.E, 650, 250);
            Assert.That(e.TargetUnit, Is.EqualTo(g.Dummy), "targeted ability picks the enemy nearest the aim point");
            Assert.That(input.Cast(g.Session.Match, AbilitySlot.Q, 650, 250).TargetUnit, Is.EqualTo(0), "skillshot aims at a point");
        }

        [Test]
        public void WorldViewInterpolatesAndReportsDamage()
        {
            PracticeGame g = Practice();
            var view = new WorldView();
            var input = new InputMapper(g.Player);
            view.Capture(g.Session.Match);
            g.Session.Step(new[] { input.MoveTo(-1000, 0) });
            view.Capture(g.Session.Match);
            (double x, double _) = view.Position(g.Player, 0.5);
            double moved = view.View(g.Player).X;
            Assert.That(moved, Is.LessThan(0));
            Assert.That(x, Is.EqualTo(moved / 2).Within(1e-9), "half way between the two captures");

            g.Session.Step(new[] { input.Attack(g.Dummy) });
            for (int t = 0; t < 60; t++) { g.Session.Step(); view.Capture(g.Session.Match); }
            Assert.That(view.DamageNumbers.Exists(n => n.Target == g.Dummy), Is.True);
            view.Age(2.0);
            Assert.That(view.DamageNumbers, Is.Empty);
        }

        [Test]
        public void CameraMathFollowsAndRotatesJoystick()
        {
            var cam = new IsometricCamera { YawDegrees = 0, PitchDegrees = 90, Distance = 10 };
            cam.Snap(500, -200);
            var p = cam.Position();
            Assert.That(p.X, Is.EqualTo(5).Within(1e-9));
            Assert.That(p.Y, Is.EqualTo(10).Within(1e-9));
            Assert.That(p.Z, Is.EqualTo(-2).Within(1e-9));
            cam.YawDegrees = 90;
            var d = cam.ScreenToWorldDirection(0, 1);     // stick up = camera forward
            Assert.That(d.Dx, Is.EqualTo(1).Within(1e-9));
            Assert.That(d.Dz, Is.EqualTo(0).Within(1e-9));
        }

        /// <summary>Acceptance #8: a 3-minute recorded input stream replays to the same final hash.</summary>
        [Test]
        public void RecordedInputReplaysToSameHash()
        {
            List<Command>[] Record()
            {
                PracticeGame g = Practice("hard", 9);
                var input = new InputMapper(g.Player);
                var rng = new DeterministicRandom(2026, 1);
                int ticks = 180 * SimClock.TicksPerSecond;
                var recorded = new List<Command>[ticks];
                for (int t = 0; t < ticks; t++)
                {
                    var cmds = new List<Command>();
                    uint r = rng.NextUInt();
                    switch (r % 40)
                    {
                        case 0: cmds.Add(input.MoveTo(r % 1600 - 400.0, (r >> 8) % 1200 - 600.0)); break;
                        case 1: cmds.Add(input.Attack(g.Bot)); break;
                        case 2: cmds.Add(input.Attack(g.Dummy)); break;
                        case 3: cmds.Add(input.QuickCast(g.Session.Match, (AbilitySlot)((r >> 4) % 4))); break;
                    }
                    recorded[t] = cmds;
                    g.Session.Step(cmds);
                }
                return recorded;
            }
            ulong Replay(List<Command>[] stream)
            {
                PracticeGame g = Practice("hard", 9);
                foreach (List<Command> cmds in stream) g.Session.Step(cmds);
                return g.Session.Match.StateHash();
            }
            List<Command>[] stream = Record();
            ulong a = Replay(stream), b = Replay(stream);
            Assert.That(b, Is.EqualTo(a));
            TestContext.WriteLine($"REPORT: 3-minute replay hash {a:X16} ({stream.Length} ticks)");
        }
    }
}
