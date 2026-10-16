using System;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Client
{
    /// <summary>
    /// Turns player intents (joystick, taps, clicks, key presses) into simulation Commands.
    /// Touch and desktop produce the same command types. World coordinates are game units on the
    /// ground plane (x, z); the Unity layer converts screen input to these.
    /// </summary>
    public sealed class InputMapper
    {
        public double DeadZone = 0.15;
        public double JoystickLookahead = 200;      // game units ahead of the champion
        public int JoystickReissueTicks = 6;        // keep the move target ahead while held
        public double JoystickReissueAngle = 0.17;  // ~10 degrees

        private readonly int _unit;
        private bool _joystickActive;
        private double _lastDx, _lastDz;
        private long _lastIssueTick = -1_000_000;

        public InputMapper(int unit) { _unit = unit; }

        /// <summary>Round to 1/64 unit and convert to Fix64 (exact; commands carry raw values).</summary>
        public static Fix64 Quantize(double value) => Fix64.FromRaw((long)Math.Round(value * 64) << 26);

        public static FixVec2 Point(double x, double z) => new FixVec2(Quantize(x), Quantize(z));

        /// <summary>
        /// Joystick in world directions (dx, dz) with magnitude 0..1. Returns a command or null.
        /// Release (inside the dead zone) stops once.
        /// </summary>
        public Command? Joystick(double dx, double dz, Match match)
        {
            double magnitude = Math.Sqrt(dx * dx + dz * dz);
            if (magnitude < DeadZone)
            {
                if (!_joystickActive) return null;
                _joystickActive = false;
                return Command.StopUnit(_unit);
            }
            dx /= magnitude; dz /= magnitude;
            double turn = Math.Acos(Math.Max(-1, Math.Min(1, dx * _lastDx + dz * _lastDz)));
            bool fresh = !_joystickActive || turn > JoystickReissueAngle || match.Tick - _lastIssueTick >= JoystickReissueTicks;
            if (!fresh) return null;
            _joystickActive = true;
            _lastDx = dx; _lastDz = dz; _lastIssueTick = match.Tick;
            FixVec2 me = match.Get(_unit).Position;
            return Command.MoveTo(_unit, Point(me.X.ToDouble() + dx * JoystickLookahead, me.Z.ToDouble() + dz * JoystickLookahead));
        }

        public Command MoveTo(double x, double z) => Command.MoveTo(_unit, Point(x, z));

        public Command Attack(int target) => Command.Attack(_unit, target);

        /// <summary>Ground click: attack an enemy under the cursor (within pickRadius), else move.</summary>
        public Command Click(Match match, double x, double z, double pickRadius = 80)
        {
            int enemy = NearestEnemy(match, x, z, pickRadius);
            return enemy != 0 ? Attack(enemy) : MoveTo(x, z);
        }

        /// <summary>
        /// Cast at a world point. Targeted abilities (E) pick the enemy nearest the aim point;
        /// skillshots fly toward the point; self casts ignore it.
        /// </summary>
        public Command Cast(Match match, AbilitySlot slot, double x, double z, double pickRadius = 400)
        {
            int target = NearestEnemy(match, x, z, pickRadius);
            return new Command(_unit, CommandKind.Cast, slot == AbilitySlot.Q ? 0 : target, Point(x, z), (byte)slot);
        }

        /// <summary>Quick cast (tap without dragging): aim at the nearest enemy champion or dummy.</summary>
        public Command QuickCast(Match match, AbilitySlot slot)
        {
            FixVec2 me = match.Get(_unit).Position;
            int target = NearestEnemy(match, me.X.ToDouble(), me.Z.ToDouble(), double.MaxValue);
            FixVec2 aim = target != 0 ? match.Get(target).Position : new FixVec2(me.X + Fix64.FromInt(300), me.Z);
            return new Command(_unit, CommandKind.Cast, slot == AbilitySlot.Q ? 0 : target, aim, (byte)slot);
        }

        public int NearestEnemy(Match match, double x, double z, double maxDistance)
        {
            int best = 0;
            double bestSq = maxDistance == double.MaxValue ? double.MaxValue : maxDistance * maxDistance;
            for (int id = 1; id <= match.UnitCount; id++)
            {
                if (!match.IsEnemy(_unit, id) || !match.Get(id).Alive) continue;
                FixVec2 p = match.Get(id).Position;
                double ddx = p.X.ToDouble() - x, ddz = p.Z.ToDouble() - z;
                double sq = ddx * ddx + ddz * ddz;
                if (sq <= bestSq) { best = id; bestSq = sq; }
            }
            return best;
        }
    }
}
