using System.Collections.Generic;
using SharpWR.Client;
using SharpWR.Sim.Abilities;
using SharpWR.Sim.Contracts;
using UnityEngine;

namespace SharpWR.Unity
{
    /// <summary>
    /// Vertical-slice practice arena (docs/moba/09-vertical-slice.md): Samira vs a dummy and one
    /// bot, isometric camera, touch joystick + drag-aim skill buttons, desktop mouse/keys.
    ///
    /// This class only turns input into Commands and draws snapshots. All rules run in the
    /// simulation (com.sharpwr.sim) at a fixed 30 Hz; the view interpolates between ticks.
    /// Placeholder art: capsules (Riot models may later go in Assets/SharpWR/Reference/).
    /// </summary>
    public sealed class SharpWRGame : MonoBehaviour
    {
        private const int Level = 9;
        private static readonly string[] Difficulties = { "easy", "medium", "hard", "impossible" };
        private static readonly AbilitySlot[] Slots = { AbilitySlot.Q, AbilitySlot.W, AbilitySlot.E, AbilitySlot.R };
        private const double QAimDistance = 800, EAimDistance = 500, DragThresholdPx = 25;

        private PracticeGame _game;
        private readonly FixedStepHost _host = new FixedStepHost();
        private WorldView _view;
        private InputMapper _input;
        private readonly IsometricCamera _cameraRig = new IsometricCamera();
        private readonly PointerInput _pointers = new PointerInput();
        private readonly List<Command> _pending = new List<Command>();
        private Camera _camera;
        private Transform[] _unitObjects = new Transform[0];
        private string _difficulty = "medium";
        private ulong _seed = 1;
        private bool _showDebug;

        // touch state
        private int _joystickFinger = int.MinValue;
        private Vector2 _joystickOrigin, _joystickKnob;
        private int _aimFinger = int.MinValue;
        private AbilitySlot _aimSlot;
        private Vector2 _aimOrigin, _aimCurrent;

        private float U => Screen.height / 720f;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            _camera = Camera.main;
            if (_camera == null)
            {
                var go = new GameObject("Main Camera") { tag = "MainCamera" };
                _camera = go.AddComponent<Camera>();
            }
            _camera.clearFlags = CameraClearFlags.SolidColor;
            _camera.backgroundColor = new Color(0.08f, 0.1f, 0.12f);
            if (Object.FindAnyObjectByType<Light>() == null)
            {
                var sun = new GameObject("Sun").AddComponent<Light>();
                sun.type = LightType.Directional;
                sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            }
            GameObject ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground";
            ground.transform.localScale = new Vector3(6f, 1f, 6f);    // 60 m = 6000 game units
            ground.transform.position = new Vector3(5f, 0f, 0f);
            ground.GetComponent<Renderer>().material.color = new Color(0.22f, 0.3f, 0.22f);
            NewGame();
        }

        private void NewGame()
        {
            foreach (Transform t in _unitObjects) if (t != null) Destroy(t.gameObject);
            _game = PracticeGame.Create(EmbeddedReferenceContent.SamiraJson, EmbeddedContent.DuelBotProfilesJson, Level, _difficulty, _seed++);
            _view = new WorldView();
            _input = new InputMapper(_game.Player);
            _pending.Clear();
            _view.Capture(_game.Session.Match);
            _unitObjects = new Transform[_view.Units.Count];
            for (int i = 0; i < _unitObjects.Length; i++)
            {
                int id = i + 1;
                GameObject body = GameObject.CreatePrimitive(id == _game.Dummy ? PrimitiveType.Cylinder : PrimitiveType.Capsule);
                body.name = id == _game.Player ? "Player (Samira)" : id == _game.Bot ? "Bot (Samira)" : "Practice dummy";
                Destroy(body.GetComponent<Collider>());
                body.transform.localScale = new Vector3(0.8f, 0.9f, 0.8f);
                body.GetComponent<Renderer>().material.color =
                    id == _game.Player ? new Color(0.25f, 0.55f, 1f) : id == _game.Bot ? new Color(1f, 0.3f, 0.25f) : new Color(0.6f, 0.6f, 0.6f);
                _unitObjects[i] = body.transform;
            }
            UnitView player = _view.View(_game.Player);
            _cameraRig.Snap(player.X, player.Z);
        }

        // ---- frame ----------------------------------------------------------------------

        private void Update()
        {
            _pointers.Poll();
            ReadInput();
            int steps = _host.Advance(Time.deltaTime);
            for (int i = 0; i < steps; i++)
            {
                _game.Session.Step(i == 0 ? _pending : null);
                _view.Capture(_game.Session.Match);
            }
            if (steps > 0) _pending.Clear();
            _view.Age(Time.deltaTime);
            Render();
        }

        private void Render()
        {
            double alpha = _host.Alpha;
            for (int i = 0; i < _unitObjects.Length; i++)
            {
                UnitView v = _view.Units[i];
                Transform t = _unitObjects[i];
                t.gameObject.SetActive(v.Alive);
                (double x, double z) = _view.Position(v.Id, alpha);
                Vector3 next = ToWorld(x, z) + Vector3.up * 0.9f;
                Vector3 delta = next - t.position;
                delta.y = 0f;
                if (delta.sqrMagnitude > 1e-6f) t.rotation = Quaternion.LookRotation(delta);
                t.position = next;
            }
            (double px, double pz) = _view.Position(_game.Player, alpha);
            _cameraRig.Follow(px, pz, Time.deltaTime);
            var pose = _cameraRig.Position();
            _camera.transform.position = new Vector3((float)pose.X, (float)pose.Y, (float)pose.Z);
            _camera.transform.LookAt(new Vector3((float)_cameraRig.FocusX, 0f, (float)_cameraRig.FocusZ));
        }

        private static Vector3 ToWorld(double unitX, double unitZ) =>
            new Vector3((float)(unitX * IsometricCamera.MetresPerUnit), 0f, (float)(unitZ * IsometricCamera.MetresPerUnit));

        /// <summary>Screen pixel → ground point in game units (ray / y=0 plane), or null if the ray misses.</summary>
        private bool ScreenToGround(Vector2 screen, out double unitX, out double unitZ)
        {
            Ray ray = _camera.ScreenPointToRay(screen);
            unitX = unitZ = 0;
            if (Mathf.Abs(ray.direction.y) < 1e-5f) return false;
            float t = -ray.origin.y / ray.direction.y;
            if (t < 0f) return false;
            Vector3 p = ray.origin + ray.direction * t;
            unitX = p.x / IsometricCamera.MetresPerUnit;
            unitZ = p.z / IsometricCamera.MetresPerUnit;
            return true;
        }

        // ---- input ----------------------------------------------------------------------

        private void ReadInput()
        {
            var match = _game.Session.Match;
            if (_pointers.ToggleDebug) _showDebug = !_showDebug;
            bool cursorOnGround = ScreenToGround(_pointers.MousePosition, out double cx, out double cz);
            if (_pointers.RightClick && cursorOnGround) _pending.Add(_input.Click(match, cx, cz));
            if (_pointers.KeyS) _pending.Add(Command.StopUnit(_game.Player));
            if (_pointers.KeyA && cursorOnGround)
            {
                int target = _input.NearestEnemy(match, cx, cz, 2000);
                if (target != 0) _pending.Add(_input.Attack(target));
            }
            bool[] keys = { _pointers.KeyQ, _pointers.KeyW, _pointers.KeyE, _pointers.KeyR };
            for (int i = 0; i < 4; i++)
                if (keys[i] && cursorOnGround) _pending.Add(_input.Cast(match, Slots[i], cx, cz));

            foreach (Pointer p in _pointers.Pointers) HandlePointer(p);

            if (_joystickFinger != int.MinValue)
            {
                Vector2 v = (_joystickKnob - _joystickOrigin) / (110f * U);
                if (v.sqrMagnitude > 1f) v.Normalize();
                (double dx, double dz) = _cameraRig.ScreenToWorldDirection(v.x, v.y);
                Command? move = _input.Joystick(dx * v.magnitude, dz * v.magnitude, match);
                if (move.HasValue) _pending.Add(move.Value);
            }
        }

        private void HandlePointer(Pointer p)
        {
            var match = _game.Session.Match;
            if (p.Phase == PointerPhase.Began)
            {
                if (HitButton(AttackButtonCenter(), 80f, p.Position))
                {
                    UnitView me = _view.View(_game.Player);
                    int target = _input.NearestEnemy(match, me.X, me.Z, double.MaxValue);
                    if (target != 0) _pending.Add(_input.Attack(target));
                    return;
                }
                for (int i = 0; i < 4; i++)
                {
                    if (!HitButton(SkillButtonCenter(i), 55f, p.Position)) continue;
                    _aimFinger = p.Id; _aimSlot = Slots[i]; _aimOrigin = _aimCurrent = p.Position;
                    return;
                }
                if (p.Position.x < Screen.width * 0.4f && p.Position.y < Screen.height * 0.6f && _joystickFinger == int.MinValue)
                {
                    _joystickFinger = p.Id; _joystickOrigin = _joystickKnob = p.Position;
                }
                return;
            }
            if (p.Id == _joystickFinger)
            {
                _joystickKnob = p.Position;
                if (p.Phase == PointerPhase.Ended)
                {
                    _joystickFinger = int.MinValue;
                    Command? stop = _input.Joystick(0, 0, match);
                    if (stop.HasValue) _pending.Add(stop.Value);
                }
                return;
            }
            if (p.Id == _aimFinger)
            {
                _aimCurrent = p.Position;
                if (p.Phase != PointerPhase.Ended) return;
                _aimFinger = int.MinValue;
                if (InCancelZone(p.Position)) return;
                Vector2 drag = _aimCurrent - _aimOrigin;
                if (drag.magnitude < DragThresholdPx * U || _aimSlot == AbilitySlot.W || _aimSlot == AbilitySlot.R)
                {
                    _pending.Add(_input.QuickCast(match, _aimSlot));
                    return;
                }
                drag.Normalize();
                (double dx, double dz) = _cameraRig.ScreenToWorldDirection(drag.x, drag.y);
                UnitView me = _view.View(_game.Player);
                double reach = _aimSlot == AbilitySlot.Q ? QAimDistance : EAimDistance;
                _pending.Add(_input.Cast(match, _aimSlot, me.X + dx * reach, me.Z + dz * reach));
            }
        }

        // ---- layout (pixels, bottom-left origin) --------------------------------------------

        private Vector2 AttackButtonCenter() => new Vector2(Screen.width - 150f * U, 150f * U);

        private Vector2 SkillButtonCenter(int i)
        {
            switch (i)
            {
                case 0: return new Vector2(Screen.width - 330f * U, 110f * U);
                case 1: return new Vector2(Screen.width - 300f * U, 260f * U);
                case 2: return new Vector2(Screen.width - 160f * U, 320f * U);
                default: return new Vector2(Screen.width - 440f * U, 230f * U);
            }
        }

        private bool HitButton(Vector2 center, float radius, Vector2 point) => (point - center).sqrMagnitude <= radius * radius * U * U;

        private bool InCancelZone(Vector2 point) =>
            point.x > Screen.width * 0.4f && point.x < Screen.width * 0.6f && point.y > Screen.height - 140f * U;

        // ---- HUD (IMGUI: no scene or UI assets needed) --------------------------------------

        private static readonly Color Panel = new Color(0f, 0f, 0f, 0.55f);

        private void OnGUI()
        {
            if (_game == null) return;
            float u = U;
            var label = new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt(18 * u), alignment = TextAnchor.MiddleCenter };
            var small = new GUIStyle(label) { fontSize = Mathf.RoundToInt(14 * u), alignment = TextAnchor.UpperLeft };

            for (int i = 0; i < _view.Units.Count; i++) DrawUnitBars(_view.Units[i], u, label);
            foreach (DamageNumber n in _view.DamageNumbers)
            {
                Vector3 s = _camera.WorldToScreenPoint(ToWorld(n.X, n.Z) + Vector3.up * (2.3f + (float)n.Age));
                if (s.z <= 0) continue;
                GUI.color = n.Type == Sim.Combat.DamageType.Magic ? new Color(0.6f, 0.6f, 1f) : new Color(1f, 0.85f, 0.4f);
                GUI.Label(new Rect(s.x - 50 * u, Screen.height - s.y - 15 * u, 100 * u, 30 * u), Mathf.RoundToInt((float)n.Amount).ToString(), label);
            }
            GUI.color = Color.white;

            DrawControls(u, label);
            DrawTopBar(u, small);
            if (_showDebug) DrawDebug(u, small);
        }

        private void DrawUnitBars(UnitView v, float u, GUIStyle label)
        {
            if (!v.Alive)
            {
                if (v.Id != _game.Dummy && v.RespawnSeconds > 0)
                {
                    Vector3 r = _camera.WorldToScreenPoint(ToWorld(v.X, v.Z));
                    if (r.z > 0) GUI.Label(new Rect(r.x - 80 * u, Screen.height - r.y - 20 * u, 160 * u, 40 * u), $"respawn {v.RespawnSeconds:F1}s", label);
                }
                return;
            }
            Vector3 s = _camera.WorldToScreenPoint(ToWorld(_view.Position(v.Id, _host.Alpha).X, _view.Position(v.Id, _host.Alpha).Z) + Vector3.up * 2.1f);
            if (s.z <= 0) return;
            float w = 90 * u, h = 9 * u, x = s.x - w / 2, y = Screen.height - s.y;
            Fill(new Rect(x - 1, y - 1, w + 2, h + 2), Panel);
            Color hp = v.Id == _game.Player ? new Color(0.3f, 0.85f, 0.4f) : v.Team == Team.Red ? new Color(0.9f, 0.3f, 0.25f) : Color.gray;
            Fill(new Rect(x, y, w * (float)(v.Health / v.MaxHealth), h), hp);
            if (v.MaxMana > 0) Fill(new Rect(x, y + h + 1, w * (float)(v.Mana / v.MaxMana), 4 * u), new Color(0.35f, 0.55f, 1f));
            for (int i = 0; i < v.Style; i++) Fill(new Rect(x + i * 15 * u, y - 8 * u, 12 * u, 5 * u), new Color(1f, 0.75f, 0.2f));
        }

        private void DrawControls(float u, GUIStyle label)
        {
            // joystick
            Vector2 baseCenter = _joystickFinger != int.MinValue ? _joystickOrigin : new Vector2(180 * u, 180 * u);
            Vector2 knob = _joystickFinger != int.MinValue ? _joystickKnob : baseCenter;
            Vector2 offset = Vector2.ClampMagnitude(knob - baseCenter, 110 * u);
            Circle(baseCenter, 110 * u, new Color(1f, 1f, 1f, 0.12f));
            Circle(baseCenter + offset, 45 * u, new Color(1f, 1f, 1f, 0.35f));

            // attack + skills
            Circle(AttackButtonCenter(), 80 * u, new Color(0.9f, 0.4f, 0.3f, 0.5f));
            GUI.Label(ToGui(AttackButtonCenter(), 160 * u, 40 * u), "ATTACK", label);
            UnitView me = _view.View(_game.Player);
            for (int i = 0; i < 4; i++)
            {
                double cd = me.Cooldown(Slots[i]);
                bool ready = cd <= 0 && me.Alive;
                Circle(SkillButtonCenter(i), 55 * u, ready ? new Color(0.3f, 0.5f, 0.9f, 0.6f) : new Color(0.25f, 0.25f, 0.3f, 0.6f));
                string text = Slots[i] + (cd > 0 ? $"\n{cd:F1}" : "");
                if (Slots[i] == AbilitySlot.R && me.Style < 6) text += $"\n{me.Style}/6";
                GUI.Label(ToGui(SkillButtonCenter(i), 110 * u, 70 * u), text, label);
            }

            if (_aimFinger != int.MinValue)
            {
                Fill(ToGui(new Vector2(Screen.width * 0.5f, Screen.height - 70 * u), Screen.width * 0.2f, 140 * u), new Color(0.8f, 0.1f, 0.1f, 0.25f));
                GUI.Label(ToGui(new Vector2(Screen.width * 0.5f, Screen.height - 70 * u), 200 * u, 40 * u), "release here to cancel", label);
                Vector2 drag = _aimCurrent - _aimOrigin;
                if (drag.magnitude >= DragThresholdPx * u && (_aimSlot == AbilitySlot.Q || _aimSlot == AbilitySlot.E))
                {
                    drag.Normalize();
                    (double dx, double dz) = _cameraRig.ScreenToWorldDirection(drag.x, drag.y);
                    (double px, double pz) = _view.Position(_game.Player, _host.Alpha);
                    double reach = _aimSlot == AbilitySlot.Q ? QAimDistance : EAimDistance;
                    Vector3 a = _camera.WorldToScreenPoint(ToWorld(px, pz));
                    Vector3 b = _camera.WorldToScreenPoint(ToWorld(px + dx * reach, pz + dz * reach));
                    Line(new Vector2(a.x, Screen.height - a.y), new Vector2(b.x, Screen.height - b.y), 6 * u, new Color(1f, 0.9f, 0.3f, 0.7f));
                }
            }
        }

        private void DrawTopBar(float u, GUIStyle small)
        {
            var button = new GUIStyle(GUI.skin.button) { fontSize = Mathf.RoundToInt(15 * u) };
            float x = 10 * u, y = 10 * u, bw = 105 * u, bh = 36 * u;
            foreach (string d in Difficulties)
            {
                GUI.color = d == _difficulty ? new Color(1f, 0.85f, 0.4f) : Color.white;
                if (GUI.Button(new Rect(x, y, bw, bh), d, button)) { _difficulty = d; NewGame(); }
                x += bw + 6 * u;
            }
            GUI.color = Color.white;
            if (GUI.Button(new Rect(x, y, bw, bh), "reset", button)) NewGame();
            x += bw + 6 * u;
            if (GUI.Button(new Rect(x, y, bw, bh), _showDebug ? "debug ▲" : "debug ▼", button)) _showDebug = !_showDebug;
            GUI.Label(new Rect(10 * u, y + bh + 4 * u, 900 * u, 24 * u),
                "Desktop: right-click move/attack · Q W E R cast at cursor · A attack nearest · S stop · F1 debug   (personal build)", small);
        }

        private void DrawDebug(float u, GUIStyle small)
        {
            var lines = new List<string>
            {
                $"tick {_view.Tick}   hash {_view.StateHash:X16}   bot {_difficulty}",
            };
            foreach (string m in _view.Messages) lines.Add(m);
            lines.Add("Unsupported / provisional:");
            foreach (string s in _game.Champion.Unsupported) lines.Add(" • " + s);
            float h = lines.Count * 18 * u + 12 * u;
            var rect = new Rect(10 * u, 90 * u, 720 * u, h);
            Fill(rect, Panel);
            GUI.Label(new Rect(rect.x + 6 * u, rect.y + 6 * u, rect.width - 12 * u, rect.height), string.Join("\n", lines), small);
        }

        // ---- drawing helpers ----------------------------------------------------------------

        private static Rect ToGui(Vector2 center, float w, float h) => new Rect(center.x - w / 2, Screen.height - center.y - h / 2, w, h);

        private static void Fill(Rect r, Color c)
        {
            Color old = GUI.color;
            GUI.color = c;
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            GUI.color = old;
        }

        /// <summary>Rounded square stand-in for a circle (IMGUI has no circle primitive).</summary>
        private static void Circle(Vector2 center, float radius, Color c)
        {
            Color old = GUI.color;
            GUI.color = c;
            GUI.DrawTexture(ToGui(center, radius * 2, radius * 2), Texture2D.whiteTexture, ScaleMode.StretchToFill, true, 0f, c, 0f, radius);
            GUI.color = old;
        }

        private static void Line(Vector2 a, Vector2 b, float width, Color c)
        {
            Matrix4x4 old = GUI.matrix;
            float angle = Mathf.Atan2(b.y - a.y, b.x - a.x) * Mathf.Rad2Deg;
            GUIUtility.RotateAroundPivot(angle, a);
            Fill(new Rect(a.x, a.y - width / 2, (b - a).magnitude, width), c);
            GUI.matrix = old;
        }
    }
}
