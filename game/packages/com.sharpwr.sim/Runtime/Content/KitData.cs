using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Content
{
    /// <summary>Reads provenance fields {value, status, source}; unresolved values throw.</summary>
    public static class KitData
    {
        public static bool IsResolved(JsonNode field) =>
            field != null && field["value"] != null && field["value"].Kind != JsonKind.Null;

        public static Fix64 Fix(JsonNode field, string name)
        {
            if (!IsResolved(field)) throw new UnsupportedContentException("required value " + name + " is unresolved");
            return Fix64.Parse(field["value"].Text);
        }

        public static int Int(JsonNode field, string name)
        {
            Fix64 v = Fix(field, name);
            if (v.Raw % Fix64.One.Raw != 0) throw new UnsupportedContentException(name + " must be an integer");
            return (int)(v.Raw >> Fix64.FractionalBits);
        }
    }
}
