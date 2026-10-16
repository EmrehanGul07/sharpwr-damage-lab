using System.Collections.Generic;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.AI
{
    /// <summary>
    /// 1v1 champion bot (ported policy of assets/marksman-3d/duel-bot.js, docs/duel-bot.md).
    ///
    /// Fairness contract: the bot reads its OWN unit freely, but the opponent only through a
    /// delayed observation buffer (position, alive) and projectiles whose cast telegraph started
    /// at least the observation delay ago. It never reads the opponent's health, cooldowns,
    /// orders or pending events. It acts only by emitting the same Commands a player can.
    /// Known leak: Match.CheckCast validates range against true positions, so a failed check
    /// can reveal that the opponent moved (bounded by use ranges below cast ranges).
    /// </summary>
    public sealed class BotBrain
    {
        public readonly int Self;
        public readonly int Opponent;
        public readonly BotProfile Profile;

        private DeterministicRandom _rng;
        private readonly FixVec2[] _seenPosition;
        private readonly bool[] _seenAlive;
        private readonly long[] _seenTick;
        private readonly List<int> _decidedProjectiles = new List<int>();
        private long _nextDecision;
        private SimTime _dodgeUntil;
        private FixVec2 _home;

        private static readonly Fix64 KiteSlack = Fix64.FromInt(50);
        private static readonly Fix64 DodgeExtra = Fix64.FromInt(40);
        private static readonly SimTime DodgeTail = new SimTime(100_000);

        public BotBrain(BotProfile profile, int self, int opponent, ulong seed)
        {
            Profile = profile;
            Self = self;
            Opponent = opponent;
            _rng = new DeterministicRandom(seed, (ulong)self);
            int size = profile.ObservationDelayTicks + 2;
            _seenPosition = new FixVec2[size];
            _seenAlive = new bool[size];
            _seenTick = new long[size];
            for (int i = 0; i < size; i++) _seenTick[i] = -1;
        }

        private BotBrain(BotBrain other)
        {
            Profile = other.Profile; Self = other.Self; Opponent = other.Opponent; _rng = other._rng;
            _seenPosition = (FixVec2[])other._seenPosition.Clone();
            _seenAlive = (bool[])other._seenAlive.Clone();
            _seenTick = (long[])other._seenTick.Clone();
            _decidedProjectiles.AddRange(other._decidedProjectiles);
            _nextDecision = other._nextDecision; _dodgeUntil = other._dodgeUntil; _home = other._home;
        }

        public BotBrain Clone() => new BotBrain(this);

        /// <summary>Record what is visible at the start of the coming tick.</summary>
        public void Observe(Match match)
        {
            if (match.Tick == 0) _home = match.Get(Self).SpawnPosition;
            int slot = (int)(match.Tick % _seenTick.Length);
            Unit opponent = match.Get(Opponent);
            _seenTick[slot] = match.Tick;
            _seenPosition[slot] = opponent.Position;
            _seenAlive[slot] = opponent.Alive;
        }

        private bool Seen(long tick, out FixVec2 position, out bool alive)
        {
            position = FixVec2.Zero; alive = false;
            if (tick < 0) return false;
            int slot = (int)(tick % _seenTick.Length);
            if (_seenTick[slot] != tick) return false;
            position = _seenPosition[slot];
            alive = _seenAlive[slot];
            return true;
        }

        public void Decide(Match match, List<Command> output)
        {
            long tick = match.Tick;
            if (tick < _nextDecision) return;
            _nextDecision = tick + Profile.DecisionIntervalTicks;
            Unit me = match.Get(Self);
            if (!me.Alive) return;
            UnitDefinition mine = match.DefinitionOf(Self);
            SimTime now = match.Now;
            if (TryDodge(match, me, mine, now, output)) return;
            if (now < _dodgeUntil) return;

            if (me.Health < mine.MaxHealth * Profile.RetreatHealthFraction)
            {
                if (me.Order != OrderKind.Move || !me.OrderPoint.Equals(_home)) output.Add(Command.MoveTo(Self, _home));
                return;
            }

            long seenTick = tick - Profile.ObservationDelayTicks;
            if (!Seen(seenTick, out FixVec2 target, out bool alive) || !alive)
            {
                if (me.Order != OrderKind.None) output.Add(Command.StopUnit(Self));
                return;
            }
            Fix64 distance = FixVec2.Distance(me.Position, target);

            if (TryCast(match, me, target, distance, seenTick, now, output)) return;

            if (me.WindingUp) return;
            Fix64 range = mine.AttackRange;
            if (me.AttackReadyAt <= now && distance <= range)
            {
                if (me.Order != OrderKind.Attack || me.OrderTarget != Opponent) output.Add(Command.Attack(Self, Opponent));
                return;
            }
            Fix64 preferred = range * Profile.PreferredRangeFraction;
            if (distance > range || distance < preferred - KiteSlack)
            {
                // Approach or kite back to the preferred spacing on the line to the opponent.
                FixVec2 away = (me.Position - target).NormalizedOr(new FixVec2(Fix64.One, Fix64.Zero));
                output.Add(Command.MoveTo(Self, target + away * preferred));
            }
            else if (me.Order == OrderKind.Move)
            {
                output.Add(Command.StopUnit(Self));
            }
        }

        private bool TryCast(Match match, Unit me, FixVec2 target, Fix64 distance, long seenTick, SimTime now, List<Command> output)
        {
            foreach (char c in Profile.Priority)
            {
                AbilitySlot slot = BotProfile.SlotOf(c);
                Fix64 useRange = Profile.UseRange[(int)slot];
                if (useRange <= Fix64.Zero || distance > useRange) continue;
                Command cast;
                if (slot == AbilitySlot.Q)
                {
                    // Lead the shot along the observed velocity, then add aim error.
                    FixVec2 aim = target;
                    if (Seen(seenTick - 1, out FixVec2 earlier, out bool _))
                    {
                        FixVec2 velocityPerTick = target - earlier;
                        Fix64 ticksToHit = distance / Fix64.FromInt(2600) * Fix64.FromInt(SimClock.TicksPerSecond)
                                           + Fix64.FromInt(Profile.ObservationDelayTicks);
                        aim = aim + velocityPerTick * (ticksToHit * Profile.Prediction);
                    }
                    aim = aim + new FixVec2(Jitter(), Jitter());
                    cast = new Command(Self, CommandKind.Cast, 0, aim, (byte)slot);
                }
                else
                {
                    cast = new Command(Self, CommandKind.Cast, Opponent, target, (byte)slot);
                }
                if (match.CheckCast(cast, now).HasValue) continue;
                output.Add(cast);
                return true;
            }
            return false;
        }

        private Fix64 Jitter() => Profile.AimError * (Fix64.Two * _rng.NextUnit() - Fix64.One);

        private bool TryDodge(Match match, Unit me, UnitDefinition mine, SimTime now, List<Command> output)
        {
            SimTime seenBefore = new SimTime(now.Micros - (long)Profile.ObservationDelayTicks * SimTime.MicrosPerSecond / SimClock.TicksPerSecond);
            IReadOnlyList<Projectile> projectiles = match.Projectiles;
            for (int i = 0; i < projectiles.Count; i++)
            {
                Projectile p = projectiles[i];
                if (!p.Active || p.Owner != Opponent || p.Visible > seenBefore) continue;
                if (_decidedProjectiles.Contains(p.Id)) continue;
                _decidedProjectiles.Add(p.Id);
                if (_decidedProjectiles.Count > 32) _decidedProjectiles.RemoveAt(0);

                FixVec2 relative = me.Position - p.Origin;
                Fix64 along = FixVec2.Dot(relative, p.Direction);
                if (along < p.Swept || along > p.Range) continue;
                var normal = new FixVec2(-p.Direction.Z, p.Direction.X);
                Fix64 side = FixVec2.Dot(relative, normal);
                Fix64 reach = p.HalfWidth + mine.Radius + Profile.DodgeMargin;
                Fix64 offset = Fix64.Max(side, -side);
                if (offset > reach) continue;                       // not threatened
                if (!_rng.Chance(Profile.DodgeChance)) continue;    // reacts too late / misreads
                Fix64 direction = side >= Fix64.Zero ? Fix64.One : -Fix64.One;
                FixVec2 sidestep = me.Position + normal * (direction * (reach - offset + DodgeExtra));
                output.Add(Command.MoveTo(Self, sidestep));
                _dodgeUntil = p.Release + SimTime.FromSeconds(Fix64.Max(Fix64.Zero, along) / p.Speed) + DodgeTail;
                return true;
            }
            return false;
        }
    }
}
