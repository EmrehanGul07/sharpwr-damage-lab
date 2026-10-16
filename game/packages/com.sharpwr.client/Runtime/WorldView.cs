using System.Collections.Generic;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Entities;
using SharpWR.Sim.World;

namespace SharpWR.Client
{
    /// <summary>Read-only presentation snapshot of one unit (doubles are display values only).</summary>
    public struct UnitView
    {
        public int Id;
        public Team Team;
        public bool Alive;
        public double X, Z, PreviousX, PreviousZ;
        public double Health, MaxHealth, Mana, MaxMana;
        public double RespawnSeconds;
        public int Style;
        public bool Channeling, Spinning, Dashing, WindingUp;
        public double CooldownQ, CooldownW, CooldownE, CooldownR;

        public double Cooldown(AbilitySlot slot) =>
            slot == AbilitySlot.Q ? CooldownQ : slot == AbilitySlot.W ? CooldownW : slot == AbilitySlot.E ? CooldownE : CooldownR;
    }

    public struct DamageNumber
    {
        public int Target;
        public double Amount;
        public DamageType Type;
        public double X, Z;
        public double Age;     // seconds since it appeared (advanced by the renderer)
    }

    /// <summary>
    /// Captures the match after each tick and interpolates between the last two captures.
    /// Also turns new DamageApplied/Rejected log entries into floating numbers and messages.
    /// </summary>
    public sealed class WorldView
    {
        private UnitView[] _units = new UnitView[0];
        private int _logCursor;

        public readonly List<DamageNumber> DamageNumbers = new List<DamageNumber>();
        public readonly List<string> Messages = new List<string>();   // newest last, capped
        public long Tick { get; private set; }
        public ulong StateHash { get; private set; }

        public IReadOnlyList<UnitView> Units => _units;
        public UnitView View(int id) => _units[id - 1];

        public void Capture(Match match)
        {
            if (_units.Length != match.UnitCount)
            {
                _units = new UnitView[match.UnitCount];
                for (int i = 0; i < _units.Length; i++) _units[i] = Read(match, i + 1, null);
            }
            for (int i = 0; i < _units.Length; i++) _units[i] = Read(match, i + 1, _units[i]);
            Tick = match.Tick;
            StateHash = match.StateHash();
            ReadLog(match);
        }

        private static UnitView Read(Match match, int id, UnitView? previous)
        {
            Unit u = match.Get(id);
            UnitDefinition d = match.DefinitionOf(id);
            long now = match.Now.Micros;
            double Seconds(long until) => until > now ? (until - now) / 1e6 : 0;
            var v = new UnitView
            {
                Id = id, Team = u.Team, Alive = u.Alive,
                X = u.Position.X.ToDouble(), Z = u.Position.Z.ToDouble(),
                Health = u.Health.ToDouble(), MaxHealth = d.MaxHealth.ToDouble(),
                Mana = u.Mana.ToDouble(), MaxMana = d.MaxMana.ToDouble(),
                RespawnSeconds = u.Alive ? 0 : Seconds(u.RespawnAt.Micros),
                Style = u.KitStacks,
                Channeling = u.KitChannelUntil.Micros > now,
                Spinning = u.KitSpinUntil.Micros > now,
                Dashing = u.Dashing,
                WindingUp = u.WindingUp,
                CooldownQ = Seconds(u.CooldownQ.Micros), CooldownW = Seconds(u.CooldownW.Micros),
                CooldownE = Seconds(u.CooldownE.Micros), CooldownR = Seconds(u.CooldownR.Micros),
            };
            // Respawns teleport: do not interpolate across them.
            bool teleported = previous.HasValue && previous.Value.Alive != v.Alive;
            v.PreviousX = previous.HasValue && !teleported ? previous.Value.X : v.X;
            v.PreviousZ = previous.HasValue && !teleported ? previous.Value.Z : v.Z;
            return v;
        }

        /// <summary>Interpolated display position (alpha from FixedStepHost).</summary>
        public (double X, double Z) Position(int id, double alpha)
        {
            UnitView v = _units[id - 1];
            if (alpha < 0) alpha = 0;
            if (alpha > 1) alpha = 1;
            return (v.PreviousX + (v.X - v.PreviousX) * alpha, v.PreviousZ + (v.Z - v.PreviousZ) * alpha);
        }

        public void Age(double seconds, double lifetime = 1.0)
        {
            for (int i = DamageNumbers.Count - 1; i >= 0; i--)
            {
                DamageNumber n = DamageNumbers[i];
                n.Age += seconds;
                if (n.Age > lifetime) DamageNumbers.RemoveAt(i);
                else DamageNumbers[i] = n;
            }
        }

        private void ReadLog(Match match)
        {
            IReadOnlyList<CombatEvent> events = match.Log.Events;
            for (; _logCursor < events.Count; _logCursor++)
            {
                CombatEvent e = events[_logCursor];
                if (e.Kind == CombatEventKind.DamageApplied)
                {
                    UnitView t = _units[e.Target - 1];
                    DamageNumbers.Add(new DamageNumber { Target = e.Target, Amount = e.Amount.ToDouble(), Type = e.DamageType, X = t.X, Z = t.Z });
                }
                else if (e.Kind == CombatEventKind.Rejected)
                {
                    AddMessage($"unit {e.Source}: {(RejectReason)e.ActionId}");
                }
                else if (e.Kind == CombatEventKind.Death)
                {
                    AddMessage($"unit {e.Target} died");
                }
            }
        }

        private void AddMessage(string text)
        {
            Messages.Add(text);
            if (Messages.Count > 8) Messages.RemoveAt(0);
        }
    }
}
