using System.Collections.Generic;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.World;

namespace SharpWR.Sim.AI
{
    /// <summary>
    /// Offline host for a match with bots: player commands first, then each bot's commands in
    /// ascending unit order, then one fixed step. Used by Unity and by tests.
    /// </summary>
    public sealed class DuelSession
    {
        public Match Match { get; private set; }
        public readonly List<BotBrain> Bots = new List<BotBrain>();
        private readonly List<Command> _commands = new List<Command>(16);

        public DuelSession(Match match) { Match = match; }

        public void AddBot(BotBrain bot)
        {
            Bots.Add(bot);
            bot.Observe(Match);
        }

        public void Step(IReadOnlyList<Command> playerCommands = null)
        {
            _commands.Clear();
            if (playerCommands != null) _commands.AddRange(playerCommands);
            for (int i = 0; i < Bots.Count; i++) Bots[i].Decide(Match, _commands);
            Match.Step(_commands);
            for (int i = 0; i < Bots.Count; i++) Bots[i].Observe(Match);
        }

        public DuelSession Clone()
        {
            var copy = new DuelSession(Match.Clone());
            for (int i = 0; i < Bots.Count; i++) copy.Bots.Add(Bots[i].Clone());
            return copy;
        }
    }
}
