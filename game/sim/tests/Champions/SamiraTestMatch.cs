using System.Collections.Generic;
using System.IO;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Content;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Tests.Champions
{
    /// <summary>Samira (from reference content) vs a dummy, driven by timed commands.</summary>
    internal sealed class SamiraTestMatch
    {
        public readonly Match Match = new Match();
        public readonly int Samira;
        public readonly int Dummy;
        private readonly Dictionary<long, List<Command>> _script = new Dictionary<long, List<Command>>(); // sim-lint n/a (tests)

        public SamiraTestMatch(int level, string distance, string hp, string armor, string mr)
        {
            string json = File.ReadAllText(Path.Combine(System.AppContext.BaseDirectory, "content", "samira.champion.json"));
            Samira = Match.Spawn(new ChampionContent(json).AtLevel(level), Team.Blue, FixVec2.Zero);
            Dummy = Match.Spawn(UnitDefinition.Dummy(Fix64.Parse(hp), Fix64.Parse(armor), Fix64.Parse(mr)), Team.Red,
                                new FixVec2(Fix64.Parse(distance), Fix64.Zero));
        }

        public void At(long tick, Command c)
        {
            if (!_script.TryGetValue(tick, out List<Command> list)) _script[tick] = list = new List<Command>();
            list.Add(c);
        }

        public Command Cast(AbilitySlot slot) =>
            new Command(Samira, CommandKind.Cast, Dummy, Match.Get(Dummy).Position, (byte)slot);

        public void RunUntil(long tick)
        {
            while (Match.Tick < tick)
            {
                _script.TryGetValue(Match.Tick, out List<Command> commands);
                Match.Step(commands);
            }
        }

        public static string Label(int actionId)
        {
            if (!ActionIds.IsAbility(actionId)) return "AA";
            AbilitySlot slot = ActionIds.SlotOf(actionId);
            return slot == AbilitySlot.R ? "R tick" : slot.ToString();
        }

        /// <summary>DamageApplied grouped by (time, ability): the Damage Lab logs one event per hit.</summary>
        public List<(long Micros, string Label, Fix64 Damage)> Hits()
        {
            var hits = new List<(long, string, Fix64)>();
            foreach (CombatEvent e in Match.Log.Events)
            {
                if (e.Kind != CombatEventKind.DamageApplied) continue;
                string label = Label(e.ActionId);
                int last = hits.Count - 1;
                if (last >= 0 && hits[last].Item1 == e.Time.Micros && hits[last].Item2 == label)
                    hits[last] = (hits[last].Item1, label, hits[last].Item3 + e.Amount);
                else
                    hits.Add((e.Time.Micros, label, e.Amount));
            }
            return hits;
        }

        public List<CombatEvent> Rejections()
        {
            var list = new List<CombatEvent>();
            foreach (CombatEvent e in Match.Log.Events) if (e.Kind == CombatEventKind.Rejected) list.Add(e);
            return list;
        }
    }
}
