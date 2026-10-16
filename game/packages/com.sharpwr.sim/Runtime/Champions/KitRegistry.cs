using SharpWR.Sim.Abilities;
using SharpWR.Sim.Champions.Samira;
using SharpWR.Sim.Content;
using SharpWR.Sim.Entities;

namespace SharpWR.Sim.Champions
{
    /// <summary>Maps content "kit.hook" names to kit implementations.</summary>
    public static class KitRegistry
    {
        public static IChampionKit Create(string hook, JsonNode kit, JsonNode abilities, UnitDefinition definition)
        {
            switch (hook)
            {
                case "samira":
                    var samira = new SamiraKit(kit, abilities);
                    definition.MeleeAttackRange = samira.MeleeAttackRange;
                    return samira;
                default:
                    throw new UnsupportedContentException("no kit implementation for hook '" + hook + "'");
            }
        }
    }
}
