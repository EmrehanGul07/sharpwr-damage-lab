using System;
using System.Collections.Generic;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.World
{
    /// <summary>
    /// One match: units, scheduler, event log and the fixed-step loop
    /// (docs/moba/03-combat-event-model.md §1). Pure function of (definitions, spawns, commands).
    ///
    /// M1 scope: movement, basic attacks (windup, projectile, timer), damage with armor/MR,
    /// death and respawn. Abilities plug in through the ability framework (next step).
    /// </summary>
    public sealed class Match
    {
        /// <summary>Engine rule for the vertical slice (09-vertical-slice.md), not a champion stat.</summary>
        public static readonly SimTime RespawnDelay = new SimTime(5 * SimTime.MicrosPerSecond);

        private readonly List<UnitDefinition> _definitions = new List<UnitDefinition>();
        private Unit[] _units = new Unit[16];
        private int _count;
        private CombatScheduler _scheduler = new CombatScheduler();
        private long _logSequence;

        public EventLog Log { get; private set; } = new EventLog();
        public long Tick { get; private set; }
        public SimTime Now => SimClock.TickStart(Tick);
        public int UnitCount => _count;

        // ---- setup ------------------------------------------------------------------------

        public int Spawn(UnitDefinition definition, Team team, FixVec2 position)
        {
            if (Tick != 0) throw new InvalidOperationException("Spawn units before the first step.");
            _definitions.Add(definition);
            if (_count == _units.Length) Array.Resize(ref _units, _units.Length * 2);
            int id = _count + 1;
            _units[_count++] = new Unit
            {
                Id = id, Definition = _definitions.Count - 1, Team = team, Position = position,
                SpawnPosition = position, Health = definition.MaxHealth, Alive = true,
            };
            return id;
        }

        public Unit Get(int id) => _units[id - 1];
        public UnitDefinition DefinitionOf(int id) => _definitions[_units[id - 1].Definition];

        // ---- loop -------------------------------------------------------------------------

        /// <summary>Advance one tick. Commands apply at the start of the tick (Input phase).</summary>
        public void Step(IReadOnlyList<Command> commands = null)
        {
            SimTime start = SimClock.TickStart(Tick);
            Tick++;
            SimTime end = SimClock.TickStart(Tick);

            if (commands != null)
                for (int i = 0; i < commands.Count; i++) Apply(commands[i], start);

            Drain(end);
            MoveUnits(start, end);
            for (int id = 1; id <= _count; id++) TryAttack(id, end);
        }

        private void Drain(SimTime end)
        {
            while (_scheduler.TryPopDue(end, out ScheduledEvent e))
            {
                switch (e.Kind)
                {
                    case CombatEventKind.AttackReady: OnAttackReady(e); break;
                    case CombatEventKind.AttackWindupEnd: OnWindupEnd(e); break;
                    case CombatEventKind.AttackImpact: OnImpact(e); break;
                    case CombatEventKind.Death: OnDeath(e); break;
                    case CombatEventKind.Respawn: OnRespawn(e); break;
                }
            }
        }

        // ---- commands ---------------------------------------------------------------------

        private void Apply(in Command c, SimTime now)
        {
            if (c.Unit < 1 || c.Unit > _count) { Reject(now, c.Unit, RejectReason.UnknownUnit); return; }
            ref Unit u = ref _units[c.Unit - 1];
            if (!u.Alive || !_definitions[u.Definition].CanAct) { Reject(now, c.Unit, RejectReason.CannotAct); return; }
            if (u.WindingUp)
            {
                // Damage Lab rule (user WR confirmation): issuing commands does not cancel a windup.
                u.HasBufferedCommand = true;
                u.BufferedCommand = c;
                return;
            }
            ApplyOrder(ref u, c, now);
        }

        private void ApplyOrder(ref Unit u, in Command c, SimTime now)
        {
            switch (c.Kind)
            {
                case CommandKind.Move:
                    u.Order = OrderKind.Move; u.OrderPoint = c.Point; u.OrderTarget = 0;
                    break;
                case CommandKind.Stop:
                    u.Order = OrderKind.None; u.OrderTarget = 0;
                    break;
                case CommandKind.AttackUnit:
                    if (c.TargetUnit < 1 || c.TargetUnit > _count || c.TargetUnit == u.Id ||
                        !_units[c.TargetUnit - 1].Alive || _units[c.TargetUnit - 1].Team == u.Team)
                    {
                        Reject(now, u.Id, RejectReason.InvalidTarget);
                        return;
                    }
                    u.Order = OrderKind.Attack; u.OrderTarget = c.TargetUnit;
                    TryAttack(u.Id, now);
                    break;
                default:
                    Reject(now, u.Id, RejectReason.UnsupportedCommand);
                    break;
            }
        }

        // ---- movement ---------------------------------------------------------------------

        private void MoveUnits(SimTime start, SimTime end)
        {
            Fix64 seconds = Fix64.Ratio(end.Micros - start.Micros, SimTime.MicrosPerSecond);
            for (int i = 0; i < _count; i++)
            {
                ref Unit u = ref _units[i];
                UnitDefinition d = _definitions[u.Definition];
                if (!u.Alive || u.WindingUp || !d.CanAct) continue;
                if (u.Order == OrderKind.Attack && !_units[u.OrderTarget - 1].Alive) { u.Order = OrderKind.None; continue; }
                FixVec2 goal;
                if (u.Order == OrderKind.Move) goal = u.OrderPoint;
                else if (u.Order == OrderKind.Attack && !InAttackRange(u.Id, u.OrderTarget)) goal = _units[u.OrderTarget - 1].Position;
                else continue;
                Fix64 step = d.MoveSpeed * seconds;
                if (u.Order == OrderKind.Attack)
                {
                    // Stop exactly at attack range instead of walking onto the target.
                    Fix64 gap = FixVec2.Distance(u.Position, goal) - AttackReach(u.Id, u.OrderTarget);
                    step = Fix64.Min(step, Fix64.Max(Fix64.Zero, gap));
                }
                u.Position = FixVec2.MoveTowards(u.Position, goal, step);
                if (u.Order == OrderKind.Move && u.Position.Equals(u.OrderPoint)) u.Order = OrderKind.None;
            }
        }

        private Fix64 AttackReach(int attacker, int target) =>
            DefinitionOf(attacker).AttackRange + DefinitionOf(target).Radius;

        private bool InAttackRange(int attacker, int target) =>
            FixVec2.WithinRange(_units[attacker - 1].Position, _units[target - 1].Position, AttackReach(attacker, target));

        // ---- basic attacks ----------------------------------------------------------------

        private void TryAttack(int id, SimTime now)
        {
            ref Unit u = ref _units[id - 1];
            if (!u.Alive || u.WindingUp || u.Order != OrderKind.Attack) return;
            if (!_units[u.OrderTarget - 1].Alive) { u.Order = OrderKind.None; return; }
            if (!InAttackRange(id, u.OrderTarget)) return;
            if (now < u.AttackReadyAt)
            {
                if (!u.ReadyEventPending)
                {
                    u.ReadyEventPending = true;
                    _scheduler.Schedule(u.AttackReadyAt, EventPhase.CastStart, CombatEventKind.AttackReady, id, u.OrderTarget, 0);
                }
                return;
            }
            StartAttack(ref u, now);
        }

        private void StartAttack(ref Unit u, SimTime now)
        {
            UnitDefinition d = _definitions[u.Definition];
            u.AttackSequence++;
            u.WindingUp = true;
            u.WindupEndsAt = now + SimTime.FromSeconds(d.WindupSeconds);
            u.AttackReadyAt = now + SimTime.FromSeconds(Fix64.One / d.AttackSpeed);
            Record(now, EventPhase.CastStart, CombatEventKind.AttackStart, u.Id, u.OrderTarget, u.AttackSequence, DamageType.Physical, Fix64.Zero);
            _scheduler.Schedule(u.WindupEndsAt, EventPhase.CastStart, CombatEventKind.AttackWindupEnd, u.Id, u.OrderTarget, u.AttackSequence);
        }

        private void OnAttackReady(in ScheduledEvent e)
        {
            _units[e.Source - 1].ReadyEventPending = false;
            TryAttack(e.Source, e.Time);
        }

        private void OnWindupEnd(in ScheduledEvent e)
        {
            ref Unit u = ref _units[e.Source - 1];
            if (!u.WindingUp || u.AttackSequence != e.ActionId) return;
            u.WindingUp = false;
            Unit target = _units[e.Target - 1];
            if (u.Alive && target.Alive)
            {
                UnitDefinition d = _definitions[u.Definition];
                SimTime travel = d.ProjectileSpeed > Fix64.Zero
                    ? SimTime.FromSeconds(FixVec2.Distance(u.Position, target.Position) / d.ProjectileSpeed)
                    : SimTime.Zero;
                _scheduler.Schedule(e.Time + travel, EventPhase.Impact, CombatEventKind.AttackImpact, u.Id, e.Target, e.ActionId);
            }
            if (u.HasBufferedCommand)
            {
                u.HasBufferedCommand = false;
                Command c = u.BufferedCommand;
                ApplyOrder(ref u, c, e.Time);
            }
            TryAttack(u.Id, e.Time);
        }

        private void OnImpact(in ScheduledEvent e)
        {
            // Homing projectile: lands if the target is still alive (M1; dodge rules arrive with skillshots).
            if (!_units[e.Target - 1].Alive) return;
            UnitDefinition source = DefinitionOf(e.Source);
            UnitDefinition target = DefinitionOf(e.Target);
            Fix64 dealt = CombatMath.Mitigate(source.AttackDamage, target.Armor, Fix64.Zero, Fix64.Zero);
            ApplyDamage(e.Time, e.Source, e.Target, e.ActionId, DamageType.Physical, dealt);
        }

        // ---- damage, death, respawn ------------------------------------------------------

        /// <summary>
        /// Pipeline steps 6–7 for M1 (no shields/reductions yet). The logged amount is the HP
        /// actually removed, matching the Damage Lab log on the killing hit.
        /// </summary>
        public void ApplyDamage(SimTime time, int source, int target, int actionId, DamageType type, Fix64 mitigated)
        {
            ref Unit t = ref _units[target - 1];
            if (!t.Alive || mitigated <= Fix64.Zero) return;
            Fix64 removed = Fix64.Min(mitigated, t.Health);
            t.Health -= removed;
            Record(time, EventPhase.Damage, CombatEventKind.DamageApplied, source, target, actionId, type, removed);
            if (t.Health <= Fix64.Zero)
                _scheduler.Schedule(time, EventPhase.Death, CombatEventKind.Death, source, target, 0);
        }

        private void OnDeath(in ScheduledEvent e)
        {
            ref Unit t = ref _units[e.Target - 1];
            if (!t.Alive) return;
            t.Alive = false;
            t.Order = OrderKind.None;
            t.WindingUp = false;
            t.HasBufferedCommand = false;
            t.RespawnAt = e.Time + RespawnDelay;
            Record(e.Time, EventPhase.Death, CombatEventKind.Death, e.Source, e.Target, 0, DamageType.True, Fix64.Zero);
            _scheduler.Schedule(t.RespawnAt, EventPhase.StatusExpiry, CombatEventKind.Respawn, e.Target, e.Target, 0);
        }

        private void OnRespawn(in ScheduledEvent e)
        {
            ref Unit t = ref _units[e.Target - 1];
            if (t.Alive) return;
            t.Alive = true;
            t.Health = _definitions[t.Definition].MaxHealth;
            t.Position = t.SpawnPosition;
            t.AttackReadyAt = e.Time;
            Record(e.Time, EventPhase.StatusExpiry, CombatEventKind.Respawn, e.Target, e.Target, 0, DamageType.True, Fix64.Zero);
        }

        // ---- log, hashing, snapshots ------------------------------------------------------

        private void Reject(SimTime time, int unit, RejectReason reason)
        {
            Record(time, EventPhase.Input, CombatEventKind.Rejected, unit, -1, (int)reason, DamageType.True, Fix64.Zero);
        }

        private void Record(SimTime time, EventPhase phase, CombatEventKind kind, int source, int target, int actionId, DamageType type, Fix64 amount)
        {
            Log.Append(new CombatEvent(time, phase, _logSequence++, kind, source, target, actionId, type, amount));
        }

        /// <summary>FNV-1a 64 over every unit's state plus the event-log hash.</summary>
        public ulong StateHash()
        {
            ulong h = Log.Hash;
            for (int i = 0; i < _count; i++)
            {
                Unit u = _units[i];
                h = Mix(h, (ulong)u.Position.X.Raw); h = Mix(h, (ulong)u.Position.Z.Raw);
                h = Mix(h, (ulong)u.Health.Raw); h = Mix(h, u.Alive ? 1UL : 0UL);
                h = Mix(h, (ulong)u.Order); h = Mix(h, (ulong)(uint)u.OrderTarget);
                h = Mix(h, (ulong)u.AttackReadyAt.Micros); h = Mix(h, (ulong)(uint)u.AttackSequence);
            }
            return Mix(h, (ulong)Tick);
        }

        private static ulong Mix(ulong h, ulong v)
        {
            unchecked
            {
                for (int i = 0; i < 8; i++) { h ^= (byte)(v >> (8 * i)); h *= 1099511628211UL; }
                return h;
            }
        }

        /// <summary>Deep copy for rollback/reconciliation and desync dumps (04-networking.md).</summary>
        public Match Clone()
        {
            var copy = new Match
            {
                _units = (Unit[])_units.Clone(),
                _count = _count,
                _scheduler = _scheduler.Clone(),
                _logSequence = _logSequence,
                Log = Log.Clone(),
                Tick = Tick,
            };
            copy._definitions.AddRange(_definitions);
            return copy;
        }
    }
}
