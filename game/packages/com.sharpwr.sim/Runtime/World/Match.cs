using System;
using System.Collections.Generic;
using SharpWR.Sim.Abilities;
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
    /// M1 scope: movement, dashes, basic attacks (windup, projectile, timer), abilities through
    /// champion kits, damage with armor/MR, death and respawn.
    /// Known approximation: walking positions update at the end of each tick; events inside a
    /// tick see the position at the tick start (dash positions are exact, see PositionAt).
    /// </summary>
    public sealed class Match
    {
        /// <summary>Engine rule for the vertical slice (09-vertical-slice.md), not a champion stat.</summary>
        public static readonly SimTime RespawnDelay = new SimTime(5 * SimTime.MicrosPerSecond);

        private static readonly Fix64 FivePerSecond = Fix64.FromInt(5);

        private readonly List<UnitDefinition> _definitions = new List<UnitDefinition>();
        private Unit[] _units = new Unit[16];
        private int _count;
        private CombatScheduler _scheduler = new CombatScheduler();
        private List<Projectile> _projectiles = new List<Projectile>();
        private int _nextProjectileId;
        private SimTime _tickEnd;
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
                SpawnPosition = position, Health = definition.MaxHealth, Mana = definition.MaxMana, Alive = true,
            };
            return id;
        }

        public Unit Get(int id) => _units[id - 1];
        public UnitDefinition DefinitionOf(int id) => _definitions[_units[id - 1].Definition];

        /// <summary>Kits mutate their own unit through this (same assembly only).</summary>
        internal ref Unit Mutable(int id) => ref _units[id - 1];

        public bool IsEnemy(int a, int b) => a != b && _units[a - 1].Team != _units[b - 1].Team;

        /// <summary>Exact position at a time inside the current tick (dashes interpolate).</summary>
        public FixVec2 PositionAt(int id, SimTime time)
        {
            Unit u = _units[id - 1];
            if (!u.Dashing) return u.Position;
            if (time >= u.DashEnd) return u.DashTo;
            if (time <= u.DashStart) return u.DashFrom;
            Fix64 f = Fix64.Ratio(time.Micros - u.DashStart.Micros, u.DashEnd.Micros - u.DashStart.Micros);
            return u.DashFrom + (u.DashTo - u.DashFrom) * f;
        }

        public bool IsDashing(int id, SimTime time) => _units[id - 1].Dashing && time < _units[id - 1].DashEnd;

        // ---- loop -------------------------------------------------------------------------

        /// <summary>Advance one tick. Commands apply at the start of the tick (Input phase).</summary>
        public void Step(IReadOnlyList<Command> commands = null)
        {
            SimTime start = SimClock.TickStart(Tick);
            Tick++;
            SimTime end = SimClock.TickStart(Tick);

            _tickEnd = end;
            if (commands != null)
                for (int i = 0; i < commands.Count; i++) Apply(commands[i], start);

            for (int i = 0; i < _projectiles.Count; i++) Sweep(i, end);
            _projectiles.RemoveAll(p => !p.Active);
            Drain(end);
            MoveUnits(start, end);
            Regenerate(start, end);
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
                    case CombatEventKind.AbilityCast:
                    case CombatEventKind.AbilityImpact:
                    case CombatEventKind.StatusExpired:
                        DefinitionOf(e.Source).Kit?.OnEvent(this, e);
                        break;
                }
            }
        }

        /// <summary>Kits schedule their own follow-up events through this.</summary>
        public void Schedule(SimTime time, EventPhase phase, CombatEventKind kind, int source, int target, int actionId, int param = 0) =>
            _scheduler.Schedule(time, phase, kind, source, target, actionId, param);

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
                    if (c.TargetUnit < 1 || c.TargetUnit > _count || !IsEnemy(u.Id, c.TargetUnit) ||
                        !_units[c.TargetUnit - 1].Alive)
                    {
                        Reject(now, u.Id, RejectReason.InvalidTarget);
                        return;
                    }
                    u.Order = OrderKind.Attack; u.OrderTarget = c.TargetUnit;
                    TryAttack(u.Id, now);
                    break;
                case CommandKind.Cast:
                    TryCast(u.Id, c, now);
                    break;
                default:
                    Reject(now, u.Id, RejectReason.UnsupportedCommand);
                    break;
            }
        }

        // ---- abilities --------------------------------------------------------------------

        public SimTime CooldownReadyAt(int id, AbilitySlot slot)
        {
            Unit u = _units[id - 1];
            switch (slot)
            {
                case AbilitySlot.Q: return u.CooldownQ;
                case AbilitySlot.W: return u.CooldownW;
                case AbilitySlot.E: return u.CooldownE;
                default: return u.CooldownR;
            }
        }

        private void SetCooldown(ref Unit u, AbilitySlot slot, SimTime readyAt)
        {
            switch (slot)
            {
                case AbilitySlot.Q: u.CooldownQ = readyAt; break;
                case AbilitySlot.W: u.CooldownW = readyAt; break;
                case AbilitySlot.E: u.CooldownE = readyAt; break;
                default: u.CooldownR = readyAt; break;
            }
        }

        /// <summary>
        /// Would this cast be accepted right now? Pure (no state change). Bots use it for their
        /// own abilities. Gate order (03-combat-event-model.md §5): lock → kit → rank → cooldown → cost.
        /// </summary>
        public RejectReason? CheckCast(in Command c, SimTime now)
        {
            if (c.Unit < 1 || c.Unit > _count) return RejectReason.UnknownUnit;
            Unit u = _units[c.Unit - 1];
            UnitDefinition d = _definitions[u.Definition];
            if (!u.Alive || !d.CanAct) return RejectReason.CannotAct;
            if (c.Slot > 3 || d.Kit == null || d.Abilities[c.Slot] == null) return RejectReason.UnsupportedCommand;
            var slot = (AbilitySlot)c.Slot;
            if (now < u.CastLockUntil || u.WindingUp) return RejectReason.Locked;
            RejectReason? kitReason = d.Kit.Validate(this, c.Unit, slot, c, now);
            if (kitReason.HasValue) return kitReason;
            if (d.AbilityRanks[c.Slot] <= 0) return RejectReason.NotLearned;
            if (now < CooldownReadyAt(c.Unit, slot)) return RejectReason.OnCooldown;
            if (u.Mana < d.Abilities[c.Slot].ManaCost) return RejectReason.NotEnoughResource;
            return null;
        }

        private void TryCast(int id, in Command c, SimTime now)
        {
            RejectReason? reason = CheckCast(c, now);
            if (reason.HasValue) { Reject(now, id, reason.Value); return; }
            ref Unit u = ref _units[id - 1];
            UnitDefinition d = _definitions[u.Definition];
            var slot = (AbilitySlot)c.Slot;
            AbilityDefinition ability = d.Abilities[c.Slot];
            int rank = d.AbilityRanks[c.Slot];

            u.Mana -= ability.ManaCost;
            Fix64 cooldown = ability.CooldownByRank[rank - 1] * Fix64.Hundred / (Fix64.Hundred + d.AbilityHaste);
            SetCooldown(ref u, slot, now + SimTime.FromSeconds(cooldown));
            u.CastSequence++;
            int actionId = ActionIds.Ability(slot, u.CastSequence);
            Record(now, EventPhase.CastStart, CombatEventKind.AbilityCast, id, c.TargetUnit, actionId, ability.DamageType, Fix64.Zero);
            d.Kit.Execute(this, id, slot, c, now, actionId);
        }

        /// <summary>Raw ability damage for a unit's current rank (no crit, no mitigation).</summary>
        public Fix64 AbilityRawDamage(int id, AbilitySlot slot)
        {
            UnitDefinition d = DefinitionOf(id);
            return d.Abilities[(int)slot].RawDamage(d.AbilityRanks[(int)slot], d.AttackDamage, d.BaseAttackDamage);
        }

        /// <summary>Mitigate and apply one damage component from source to target.</summary>
        public void DealDamage(SimTime time, int source, int target, int actionId, DamageType type, Fix64 raw)
        {
            UnitDefinition t = DefinitionOf(target);
            Fix64 mitigated = type == DamageType.Physical ? CombatMath.Mitigate(raw, t.Armor, Fix64.Zero, Fix64.Zero)
                : type == DamageType.Magic ? CombatMath.Mitigate(raw, t.MagicResist, Fix64.Zero, Fix64.Zero)
                : raw;
            ApplyDamage(time, source, target, actionId, type, mitigated);
        }

        public void StartDash(int id, FixVec2 to, Fix64 speed, SimTime now)
        {
            ref Unit u = ref _units[id - 1];
            FixVec2 from = PositionAt(id, now);
            u.Dashing = true;
            u.DashFrom = from;
            u.DashTo = to;
            u.DashStart = now;
            u.DashEnd = now + SimTime.FromSeconds(FixVec2.Distance(from, to) / speed);
        }

        // ---- projectiles ------------------------------------------------------------------

        public IReadOnlyList<Projectile> Projectiles => _projectiles;

        /// <summary>
        /// Launch a line skillshot that hits the first enemy it reaches; the owner's kit receives
        /// an AbilityImpact (target = hit unit) at the exact hit time.
        /// </summary>
        public void LaunchProjectile(int owner, int actionId, FixVec2 origin, FixVec2 direction, Fix64 speed,
                                     Fix64 range, Fix64 halfWidth, SimTime visible, SimTime release)
        {
            _projectiles.Add(new Projectile
            {
                Id = ++_nextProjectileId, Owner = owner, ActionId = actionId, Origin = origin, Direction = direction,
                Speed = speed, Range = range, HalfWidth = halfWidth, Visible = visible, Release = release,
                Swept = -Fix64.One, Active = true,
            });
            Sweep(_projectiles.Count - 1, _tickEnd);
        }

        private void Sweep(int index, SimTime to)
        {
            Projectile p = _projectiles[index];
            if (!p.Active) return;
            Fix64 reached = Fix64.Min(p.Range, p.Speed * Fix64.Ratio(to.Micros - p.Release.Micros, SimTime.MicrosPerSecond));
            int best = 0;
            Fix64 bestAlong = Fix64.Zero;
            for (int id = 1; id <= _count; id++)
            {
                if (!IsEnemy(p.Owner, id) || !_units[id - 1].Alive) continue;
                FixVec2 relative = PositionAt(id, to) - p.Origin;
                Fix64 along = FixVec2.Dot(relative, p.Direction);
                if (along <= p.Swept || along > reached) continue;
                Fix64 reach = p.HalfWidth + _definitions[_units[id - 1].Definition].Radius;
                if (relative.LengthSquared - along * along > reach * reach) continue;
                if (best == 0 || along < bestAlong) { best = id; bestAlong = along; }
            }
            if (best != 0)
            {
                p.Active = false;
                _scheduler.Schedule(p.Release + SimTime.FromSeconds(Fix64.Max(Fix64.Zero, bestAlong) / p.Speed), EventPhase.Impact,
                                    CombatEventKind.AbilityImpact, p.Owner, best, p.ActionId, 0);
            }
            else
            {
                if (reached > p.Swept) p.Swept = reached;   // before release nothing is swept
                if (reached >= p.Range) p.Active = false;
            }
            _projectiles[index] = p;
        }

        // ---- movement & regeneration ------------------------------------------------------

        private void MoveUnits(SimTime start, SimTime end)
        {
            Fix64 seconds = Fix64.Ratio(end.Micros - start.Micros, SimTime.MicrosPerSecond);
            for (int i = 0; i < _count; i++)
            {
                ref Unit u = ref _units[i];
                UnitDefinition d = _definitions[u.Definition];
                if (!u.Alive) continue;
                if (u.Dashing)
                {
                    u.Position = PositionAt(u.Id, end);
                    if (end >= u.DashEnd) u.Dashing = false;
                    continue;
                }
                if (u.WindingUp || !d.CanAct || end <= u.CastLockUntil) continue;
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

        private void Regenerate(SimTime start, SimTime end)
        {
            Fix64 seconds = Fix64.Ratio(end.Micros - start.Micros, SimTime.MicrosPerSecond);
            for (int i = 0; i < _count; i++)
            {
                ref Unit u = ref _units[i];
                UnitDefinition d = _definitions[u.Definition];
                if (!u.Alive || d.MaxMana <= Fix64.Zero) continue;
                u.Mana = Fix64.Min(d.MaxMana, u.Mana + d.ManaRegenPer5s / FivePerSecond * seconds);
            }
        }

        private Fix64 AttackReach(int attacker, int target) =>
            DefinitionOf(attacker).AttackRange + DefinitionOf(target).Radius;

        private bool InAttackRange(int attacker, int target) =>
            FixVec2.WithinRange(_units[attacker - 1].Position, _units[target - 1].Position, AttackReach(attacker, target));

        // ---- basic attacks ----------------------------------------------------------------

        private SimTime AttackBlockedUntil(int id, SimTime now)
        {
            Unit u = _units[id - 1];
            SimTime until = u.CastLockUntil;
            if (u.Dashing && u.DashEnd > until) until = u.DashEnd;
            IChampionKit kit = _definitions[u.Definition].Kit;
            if (kit != null)
            {
                SimTime kitUntil = kit.AttackBlockedUntil(this, id);
                if (kitUntil > until) until = kitUntil;
            }
            return until;
        }

        private void TryAttack(int id, SimTime now)
        {
            ref Unit u = ref _units[id - 1];
            if (!u.Alive || u.WindingUp || u.Order != OrderKind.Attack) return;
            if (!_units[u.OrderTarget - 1].Alive) { u.Order = OrderKind.None; return; }
            if (!InAttackRange(id, u.OrderTarget)) return;
            SimTime readyAt = u.AttackReadyAt;
            SimTime blocked = AttackBlockedUntil(id, now);
            if (blocked > readyAt) readyAt = blocked;
            if (now < readyAt)
            {
                if (!u.ReadyEventPending)
                {
                    u.ReadyEventPending = true;
                    _scheduler.Schedule(readyAt, EventPhase.CastStart, CombatEventKind.AttackReady, id, u.OrderTarget, 0);
                }
                return;
            }
            StartAttack(ref u, now);
        }

        private Fix64 BonusAs(in Unit u, SimTime now) => now < u.BonusAsBuffUntil ? u.BonusAsBuff : Fix64.Zero;

        private void StartAttack(ref Unit u, SimTime now)
        {
            UnitDefinition d = _definitions[u.Definition];
            Fix64 extra = BonusAs(u, now);
            u.AttackSequence++;
            u.WindingUp = true;
            u.AttackMelee = d.MeleeAttackRange > Fix64.Zero &&
                FixVec2.WithinRange(u.Position, _units[u.OrderTarget - 1].Position, d.MeleeAttackRange);
            u.WindupEndsAt = now + SimTime.FromSeconds(d.WindupSecondsWith(extra));
            u.AttackReadyAt = now + SimTime.FromSeconds(Fix64.One / d.AttackSpeedWith(extra));
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
                SimTime travel = !u.AttackMelee && d.ProjectileSpeed > Fix64.Zero
                    ? SimTime.FromSeconds(FixVec2.Distance(u.Position, target.Position) / d.ProjectileSpeed)
                    : SimTime.Zero;
                _scheduler.Schedule(e.Time + travel, EventPhase.Impact, CombatEventKind.AttackImpact, u.Id, e.Target, e.ActionId,
                                    u.AttackMelee ? 1 : 0);
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
            // Homing projectile: lands if the target is still alive.
            if (!_units[e.Target - 1].Alive) return;
            Fix64 before = _units[e.Target - 1].Health;
            DealDamage(e.Time, e.Source, e.Target, e.ActionId, DamageType.Physical, DefinitionOf(e.Source).AttackDamage);
            DefinitionOf(e.Source).Kit?.OnAttackHit(this, e.Source, e.Target, e.Time, e.Param == 1, e.ActionId, before);
        }

        // ---- damage, death, respawn ------------------------------------------------------

        /// <summary>
        /// Pipeline steps 6–7 for M1 (no shields/reductions yet). The logged amount is the HP
        /// actually removed, matching the Damage Lab log on the killing hit.
        /// </summary>
        public void ApplyDamage(SimTime time, int source, int target, int actionId, DamageType type, Fix64 mitigated)
        {
            ref Unit t = ref _units[target - 1];
            if (!t.Alive || t.Health <= Fix64.Zero || mitigated <= Fix64.Zero) return;
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
            t.Dashing = false;
            t.CastLockUntil = SimTime.Zero;
            t.BonusAsBuffUntil = SimTime.Zero;
            t.RespawnAt = e.Time + RespawnDelay;
            DefinitionOf(e.Target).Kit?.OnDeath(this, e.Target);
            Record(e.Time, EventPhase.Death, CombatEventKind.Death, e.Source, e.Target, 0, DamageType.True, Fix64.Zero);
            _scheduler.Schedule(t.RespawnAt, EventPhase.StatusExpiry, CombatEventKind.Respawn, e.Target, e.Target, 0);
        }

        private void OnRespawn(in ScheduledEvent e)
        {
            ref Unit t = ref _units[e.Target - 1];
            if (t.Alive) return;
            UnitDefinition d = _definitions[t.Definition];
            t.Alive = true;
            t.Health = d.MaxHealth;
            t.Mana = d.MaxMana;
            t.Position = t.SpawnPosition;
            t.AttackReadyAt = e.Time;
            Record(e.Time, EventPhase.StatusExpiry, CombatEventKind.Respawn, e.Target, e.Target, 0, DamageType.True, Fix64.Zero);
        }

        // ---- log, hashing, snapshots ------------------------------------------------------

        public void Reject(SimTime time, int unit, RejectReason reason)
        {
            Record(time, EventPhase.Input, CombatEventKind.Rejected, unit, -1, (int)reason, DamageType.True, Fix64.Zero);
        }

        public void Record(SimTime time, EventPhase phase, CombatEventKind kind, int source, int target, int actionId, DamageType type, Fix64 amount)
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
                h = Mix(h, (ulong)u.Health.Raw); h = Mix(h, (ulong)u.Mana.Raw); h = Mix(h, u.Alive ? 1UL : 0UL);
                h = Mix(h, (ulong)u.Order); h = Mix(h, (ulong)(uint)u.OrderTarget);
                h = Mix(h, (ulong)u.AttackReadyAt.Micros); h = Mix(h, (ulong)(uint)u.AttackSequence);
                h = Mix(h, (ulong)u.CooldownQ.Micros); h = Mix(h, (ulong)u.CooldownW.Micros);
                h = Mix(h, (ulong)u.CooldownE.Micros); h = Mix(h, (ulong)u.CooldownR.Micros);
                h = Mix(h, (ulong)(uint)u.KitStacks); h = Mix(h, (ulong)u.KitChannelUntil.Micros);
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
                _projectiles = new List<Projectile>(_projectiles),
                _nextProjectileId = _nextProjectileId,
                _tickEnd = _tickEnd,
                _logSequence = _logSequence,
                Log = Log.Clone(),
                Tick = Tick,
            };
            copy._definitions.AddRange(_definitions);
            return copy;
        }
    }
}
