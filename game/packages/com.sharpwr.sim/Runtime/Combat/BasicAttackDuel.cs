using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Combat
{
    /// <summary>
    /// Spike scenario: one ranged attacker auto-attacking a stationary, non-retaliating dummy,
    /// stepped on the fixed clock. Exists to prove the scheduler + fixed-step loop reproduce the
    /// Python reference timeline (fixture "timeline"). It is replaced by the entity/ability
    /// systems in milestone M1 and kept as a regression test.
    /// </summary>
    public sealed class BasicAttackDuel
    {
        public const int AttackerId = 1;
        public const int DummyId = 2;
        public const int BasicAttackActionId = 0;

        public readonly struct Settings
        {
            public readonly Fix64 AttackDamage, AttackSpeed, WindupSeconds, Distance, ProjectileSpeed,
                                  DummyHealth, DummyArmor;

            public Settings(Fix64 attackDamage, Fix64 attackSpeed, Fix64 windupSeconds, Fix64 distance,
                            Fix64 projectileSpeed, Fix64 dummyHealth, Fix64 dummyArmor)
            {
                AttackDamage = attackDamage; AttackSpeed = attackSpeed; WindupSeconds = windupSeconds;
                Distance = distance; ProjectileSpeed = projectileSpeed; DummyHealth = dummyHealth;
                DummyArmor = dummyArmor;
            }
        }

        private readonly Settings _s;
        private readonly SimTime _period, _windup, _travel;
        private readonly CombatScheduler _scheduler = new CombatScheduler();
        private long _logSequence;

        public EventLog Log { get; } = new EventLog();
        public Fix64 DummyHealth { get; private set; }
        public long Tick { get; private set; }
        public SimTime Now => SimClock.TickStart(Tick);

        public BasicAttackDuel(in Settings settings)
        {
            _s = settings;
            _period = SimTime.FromSeconds(Fix64.One / settings.AttackSpeed);
            _windup = SimTime.FromSeconds(settings.WindupSeconds);
            _travel = SimTime.FromSeconds(settings.Distance / settings.ProjectileSpeed);
            DummyHealth = settings.DummyHealth;
            _scheduler.Schedule(SimTime.Zero, EventPhase.CastStart, CombatEventKind.AttackStart,
                                AttackerId, DummyId, BasicAttackActionId);
        }

        /// <summary>Advance one fixed tick, resolving every event due inside it.</summary>
        public void Step()
        {
            Tick++;
            SimTime end = SimClock.TickStart(Tick);
            while (_scheduler.TryPopDue(end, out ScheduledEvent e))
            {
                switch (e.Kind)
                {
                    case CombatEventKind.AttackStart:
                        Record(e, CombatEventKind.AttackStart, DamageType.Physical, Fix64.Zero);
                        _scheduler.Schedule(e.Time + _windup + _travel, EventPhase.Impact,
                                            CombatEventKind.AttackImpact, e.Source, e.Target, e.ActionId);
                        _scheduler.Schedule(e.Time + _period, EventPhase.CastStart,
                                            CombatEventKind.AttackStart, e.Source, e.Target, e.ActionId);
                        break;
                    case CombatEventKind.AttackImpact:
                        Fix64 dealt = CombatMath.Mitigate(_s.AttackDamage, _s.DummyArmor, Fix64.Zero, Fix64.Zero);
                        DummyHealth -= dealt;
                        Record(e, CombatEventKind.DamageApplied, DamageType.Physical, dealt);
                        break;
                }
            }
        }

        private void Record(in ScheduledEvent e, CombatEventKind kind, DamageType type, Fix64 amount)
        {
            Log.Append(new CombatEvent(e.Time, e.Phase, _logSequence++, kind, e.Source, e.Target,
                                       e.ActionId, type, amount));
        }
    }
}
