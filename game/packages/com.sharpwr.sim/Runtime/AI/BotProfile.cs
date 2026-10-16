using SharpWR.Sim.Abilities;
using SharpWR.Sim.Content;
using SharpWR.Sim.Core;
using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.AI
{
    /// <summary>
    /// Decision policy for one difficulty (content/ai/duel-bot.profiles.json). Difficulty changes
    /// what the bot knows and how fast it reacts, never the unit's stats.
    /// </summary>
    public sealed class BotProfile
    {
        public string Difficulty = "";
        public int ObservationDelayTicks;
        public int DecisionIntervalTicks;
        public Fix64 AimError;
        public Fix64 Prediction;
        public Fix64 DodgeChance;
        public Fix64 PreferredRangeFraction;
        public Fix64 RetreatHealthFraction;
        public Fix64 DodgeMargin;
        public string Priority = "";
        public readonly Fix64[] UseRange = new Fix64[4];   // zero = never cast

        public static BotProfile Load(string json, string difficulty, string championId)
        {
            JsonNode root = JsonNode.Parse(json);
            if (root["schema"]?.Text != "sharpwr.ai-profiles/1") throw new System.FormatException("Not an AI profile file");
            JsonNode p = root["profiles"][difficulty] ?? throw new UnsupportedContentException("unknown difficulty " + difficulty);
            JsonNode shared = root["shared"];
            var profile = new BotProfile
            {
                Difficulty = difficulty,
                ObservationDelayTicks = MillisToTicks(KitData.Int(p["observation_delay_ms"], "observation_delay_ms")),
                DecisionIntervalTicks = System.Math.Max(1, MillisToTicks(KitData.Int(p["decision_interval_ms"], "decision_interval_ms"))),
                AimError = KitData.Fix(p["aim_error"], "aim_error"),
                Prediction = KitData.Fix(p["prediction"], "prediction"),
                DodgeChance = KitData.Fix(p["dodge_chance"], "dodge_chance"),
                PreferredRangeFraction = KitData.Fix(p["preferred_range_fraction"], "preferred_range_fraction"),
                RetreatHealthFraction = KitData.Fix(shared["retreat_health_fraction"], "retreat_health_fraction"),
                DodgeMargin = KitData.Fix(shared["dodge_margin"], "dodge_margin"),
            };
            JsonNode abilities = root["abilities"]?[championId];
            if (abilities != null)
            {
                profile.Priority = abilities["priority"].Text;
                string slots = "QWER";
                for (int i = 0; i < 4; i++)
                {
                    JsonNode range = abilities["use_range"][slots.Substring(i, 1)];
                    if (KitData.IsResolved(range)) profile.UseRange[i] = KitData.Fix(range, "use_range");
                }
            }
            return profile;
        }

        /// <summary>Round half up to whole simulation ticks.</summary>
        public static int MillisToTicks(int millis) => (millis * SimClock.TicksPerSecond + 500) / 1000;

        public static AbilitySlot SlotOf(char c) =>
            c == 'Q' ? AbilitySlot.Q : c == 'W' ? AbilitySlot.W : c == 'E' ? AbilitySlot.E : AbilitySlot.R;
    }
}
