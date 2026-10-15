using System;
using System.Collections.Generic;
using System.Text;

namespace SharpWR.Sim.Content
{
    public enum JsonKind : byte { Null, Bool, Number, String, Array, Object }

    /// <summary>
    /// Minimal, allocation-tolerant JSON reader for content loading (load time only, never per
    /// tick). Numbers are kept as their source text so they convert to Fix64 exactly; objects
    /// keep insertion order (no hash-ordered iteration).
    /// </summary>
    public sealed class JsonNode
    {
        public JsonKind Kind;
        public string Text;                                   // string value or number text
        public bool Bool;
        public readonly List<JsonNode> Items = new List<JsonNode>();
        public readonly List<KeyValuePair<string, JsonNode>> Fields = new List<KeyValuePair<string, JsonNode>>();

        public JsonNode this[string key]
        {
            get
            {
                for (int i = 0; i < Fields.Count; i++)
                    if (Fields[i].Key == key) return Fields[i].Value;
                return null;
            }
        }

        public static JsonNode Parse(string text)
        {
            int i = 0;
            JsonNode node = ParseValue(text, ref i);
            SkipWs(text, ref i);
            if (i != text.Length) throw new FormatException("Trailing characters at " + i);
            return node;
        }

        private static JsonNode ParseValue(string s, ref int i)
        {
            SkipWs(s, ref i);
            if (i >= s.Length) throw new FormatException("Unexpected end of JSON");
            char c = s[i];
            if (c == '{') return ParseObject(s, ref i);
            if (c == '[') return ParseArray(s, ref i);
            if (c == '"') return new JsonNode { Kind = JsonKind.String, Text = ParseString(s, ref i) };
            if (Match(s, ref i, "null")) return new JsonNode { Kind = JsonKind.Null };
            if (Match(s, ref i, "true")) return new JsonNode { Kind = JsonKind.Bool, Bool = true };
            if (Match(s, ref i, "false")) return new JsonNode { Kind = JsonKind.Bool, Bool = false };
            int start = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (i == start) throw new FormatException("Unexpected character '" + c + "' at " + i);
            return new JsonNode { Kind = JsonKind.Number, Text = s.Substring(start, i - start) };
        }

        private static JsonNode ParseObject(string s, ref int i)
        {
            var node = new JsonNode { Kind = JsonKind.Object };
            i++;
            SkipWs(s, ref i);
            if (s[i] == '}') { i++; return node; }
            while (true)
            {
                SkipWs(s, ref i);
                string key = ParseString(s, ref i);
                SkipWs(s, ref i);
                Expect(s, ref i, ':');
                node.Fields.Add(new KeyValuePair<string, JsonNode>(key, ParseValue(s, ref i)));
                SkipWs(s, ref i);
                if (s[i] == ',') { i++; continue; }
                Expect(s, ref i, '}');
                return node;
            }
        }

        private static JsonNode ParseArray(string s, ref int i)
        {
            var node = new JsonNode { Kind = JsonKind.Array };
            i++;
            SkipWs(s, ref i);
            if (s[i] == ']') { i++; return node; }
            while (true)
            {
                node.Items.Add(ParseValue(s, ref i));
                SkipWs(s, ref i);
                if (s[i] == ',') { i++; continue; }
                Expect(s, ref i, ']');
                return node;
            }
        }

        private static string ParseString(string s, ref int i)
        {
            Expect(s, ref i, '"');
            var sb = new StringBuilder();
            while (s[i] != '"')
            {
                char c = s[i++];
                if (c != '\\') { sb.Append(c); continue; }
                char e = s[i++];
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'u':
                        sb.Append((char)Convert.ToInt32(s.Substring(i, 4), 16));
                        i += 4;
                        break;
                    default: throw new FormatException("Bad escape at " + i);
                }
            }
            i++;
            return sb.ToString();
        }

        private static bool Match(string s, ref int i, string word)
        {
            if (string.CompareOrdinal(s, i, word, 0, word.Length) != 0) return false;
            i += word.Length;
            return true;
        }

        private static void Expect(string s, ref int i, char c)
        {
            if (i >= s.Length || s[i] != c) throw new FormatException("Expected '" + c + "' at " + i);
            i++;
        }

        private static void SkipWs(string s, ref int i)
        {
            while (i < s.Length && (s[i] == ' ' || s[i] == '\n' || s[i] == '\r' || s[i] == '\t')) i++;
        }
    }
}
