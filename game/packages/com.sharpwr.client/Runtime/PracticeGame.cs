using SharpWR.Sim.AI;
using SharpWR.Sim.Content;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Client
{
    /// <summary>
    /// The vertical-slice practice arena: player champion, a practice dummy and one bot
    /// (docs/moba/09-vertical-slice.md). Content arrives as JSON text so this works the same in
    /// Unity (embedded content) and in tests (files).
    /// </summary>
    public sealed class PracticeGame
    {
        /// <summary>Practice dummy values are slice test settings (acceptance #3), not champion stats.</summary>
        public static readonly Fix64 DummyHealth = Fix64.FromInt(2000), DummyArmor = Fix64.FromInt(50), DummyMagicResist = Fix64.FromInt(30);

        public DuelSession Session { get; private set; }
        public int Player { get; private set; }
        public int Dummy { get; private set; }
        public int Bot { get; private set; }
        public ChampionContent Champion { get; private set; }
        public BotProfile BotProfile { get; private set; }

        public static PracticeGame Create(string championJson, string aiProfilesJson, int level, string botDifficulty, ulong seed)
        {
            var champion = new ChampionContent(championJson);
            var game = new PracticeGame { Champion = champion };
            var match = new Match();
            game.Player = match.Spawn(champion.AtLevel(level), Team.Blue, FixVec2.Zero);
            game.Dummy = match.Spawn(UnitDefinition.Dummy(DummyHealth, DummyArmor, DummyMagicResist), Team.Red,
                                     new FixVec2(Fix64.FromInt(600), Fix64.FromInt(300)));
            game.Bot = match.Spawn(champion.AtLevel(level), Team.Red, new FixVec2(Fix64.FromInt(1500), Fix64.FromInt(-300)));
            game.Session = new DuelSession(match);
            game.BotProfile = BotProfile.Load(aiProfilesJson, botDifficulty, champion.Id);
            game.Session.AddBot(new BotBrain(game.BotProfile, game.Bot, game.Player, seed));
            return game;
        }
    }
}
