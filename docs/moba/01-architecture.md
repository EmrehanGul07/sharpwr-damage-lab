# 01 · Technical architecture, dependency map, Unity project structure

Status: proposed for validation (M0). Decisions are recorded as ADRs in `adr/`.

## 1. Engine choice, evaluated against this repository

| Option | For | Against | Verdict |
|---|---|---|---|
| **Unity 6.3 LTS + C#** (requested) | Mature mobile renderer (URP), IL2CPP Android/iOS, profiler, Input System, Addressables, test runner; C# sim core can also run on a plain .NET headless server; large hiring/tooling pool. | Full rendering rewrite; existing three.js arena and GLB pipeline not reused directly; Unity licensing terms to track. | **Chosen** (ADR-0001) |
| Evolve the existing three.js/TypeScript arena | 120 Hz arena, bots, lanes, HUD already exist; same TS sim could run in Node for the server. | WebView rendering budget on mid-range Android for 10 champions + ~150 minions + fog; dense untyped JS; no asset pipeline/LOD/streaming. | Kept as **behaviour reference** and for the Damage Lab app; not the game client. |
| Godot 4 + C# | Free/open, light. | Weaker console/mobile tooling, C# on mobile less mature, smaller ecosystem for netcode/profiling. | Not chosen. |

Unity 6.3 is the current LTS, supported until December 2027
([Unity releases](https://unity.com/releases/lts-vs-tech-stream)). Pin the exact `6000.3.x`
patch in `game/unity/ProjectSettings/ProjectVersion.txt` when the project is created (M0).

**Key structural decision:** the simulation is **engine-agnostic C#** (no `UnityEngine`
reference, `noEngineReferences: true`) in a local UPM package that is *also* compiled by a
plain `netstandard2.1` project. This gives fast `dotnet test` in CI, cross-platform
determinism tests on ARM and x64, and a headless server without Unity.

## 2. Layered architecture

```
                 ┌──────────────────────────────────────────────────────────┐
  Reference      │ Python Damage Lab (sharpwr/, data/)  — unchanged, protected │
  (validation)   └───────────────┬──────────────────────────────────────────┘
                                 │ tools/parity  tools/data_import  (read-only exporters)
                                 ▼
  Content        game/content/   champions · items · runes · ai · rosters (JSON, provenance)
                 game/parity/    golden fixtures (expected values from Python)
                                 │ importer (decimal text → Fix64)
                                 ▼
  Simulation     com.sharpwr.sim  (pure C#, deterministic, fixed step, Fix64, µs event queue)
                 Numerics · Core · Combat · Stats · Status · Abilities · Champions ·
                 Items · Runes · World · AI · Net(protocol, state hashing)
                    ▲ commands                         │ snapshots / event log
                    │                                  ▼
  Host           ┌───────────────┐            ┌──────────────────────────┐
                 │ Offline host   │            │ Headless server (.NET 8)  │
                 │ (in Unity)     │            │ game/server, authoritative│
                 └──────┬────────┘            └──────────┬───────────────┘
                        │ same sim, same content         │ UDP (M5+)
                        ▼                                ▼
  Presentation   Unity client: input → commands; snapshots → interpolated views;
                 camera, HUD, VFX, audio, joystick/skillshot UI. Never decides outcomes.
```

Rules (enforced by asmdef references, `tools/sim_lint`, and `.claude/rules/`):

1. **Dependencies point down only.** Presentation → Sim; Sim → nothing but `System`.
2. **The sim is a pure function of (content, seed, ordered commands).** No wall clock, no
   `UnityEngine`, no floats, no unordered iteration, no threads inside a tick.
3. **Clients never decide outcomes.** Offline mode runs the same authoritative sim locally;
   online, the server's sim is authoritative and clients predict only their own movement and
   cast *presentation* (`04-networking.md`).
4. **Content is data.** Champions/items/runes are JSON definitions + a small number of named,
   tested script hooks for genuinely unique mechanics (`05-ability-framework.md`).
5. **The Damage Lab is the oracle**, never a dependency at runtime.

## 3. Simulation core design summary

| Concern | Design |
|---|---|
| Numbers | `Fix64` Q32.32, exact 128-bit multiply, round-half-up / half-away rules, throw on overflow (ADR-0002). Validated: max error vs Python 2.7e-7 HP over 270 ability cases, 1.3e-8 on stats. |
| Time | `SimTime` = int64 microseconds. Fixed step 30 Hz (`SimClock.TicksPerSecond`). Combat events are scheduled at exact µs inside a tick, so windups like 0.2279635 s are not quantized to 33 ms. Validated: AA impact times within 1.1 µs of Python. |
| Ordering | Single binary heap ordered by (µs, phase, sequence); phases Input → CastStart → Movement → Impact → Damage → Death → StatusExpiry (`03-combat-event-model.md`). |
| Randomness | PCG32 streams per purpose (crit per entity, AI per bot) seeded from match seed. |
| State | Struct-of-arrays entity store with stable integer ids, no references across entities; snapshot = memcpy-able blocks (rollback/reconciliation ready). |
| Audit | `EventLog` with FNV-1a 64 running hash; per-tick hash exchanged online to detect desync. |
| Geometry | Fixed-point 2-D (x, z) on the ground plane, circles for units, swept capsule for skillshots; height is presentation only. |

## 4. Dependency map

Module-level dependencies inside `com.sharpwr.sim` (arrows = "may reference"):

```
Numerics ◄─ Core ◄─ Combat ◄─ Stats ◄─ Status ◄─ Abilities ◄─ Champions
   ▲          ▲        ▲        ▲        ▲          ▲            │
   │          │        │        │        └── Items ◄┤            │
   │          │        │        └────────── Runes ◄─┘            │
   │          │        └────────── World (map, lanes, minions, towers, fog) ◄── AI
   │          └─────────────────────────────────────────────────────── Net (protocol, hashing)
Contracts (ids, command & event structs) ◄── everything
```

* `Champions` contains only per-champion hook classes registered by id; it may not be
  referenced by any other module (content wiring happens through the registry).
* `AI` reads the same observation API the client sees (fog applied) and emits commands; it
  never mutates state directly.
* `Net` depends on `Contracts`/`Core` only; it serializes commands/snapshots and never runs
  gameplay rules.

Repository-level dependencies:

```
sharpwr/, data/ ──(read by)──► tools/parity, tools/data_import ──(write)──► game/parity, game/content/reference-riot
game/content/{champions,items,runes,ai,rosters} ◄── authored by design (original IP)
game/packages/com.sharpwr.sim ◄── game/sim (dotnet build/test), game/server, game/unity
game/unity ──► com.sharpwr.sim (+ com.sharpwr.acceptance for QA PlayMode tests)
```

## 5. Unity project structure

```
game/
  README.md
  content/                         # JSON, provenance-checked (tools/content)
    champions/  items/  runes/  ai/  rosters/  schema/
    reference-riot/                # private validation data, never in player builds
  parity/fixtures/                 # generated by tools/parity (Python reference)
  packages/
    com.sharpwr.sim/               # engine-agnostic simulation (local UPM package)
      Runtime/{Numerics,Core,Contracts,Combat,Stats,Status,Abilities,Champions,
               Items,Runes,World,AI,Net}/  SharpWR.Sim.asmdef (noEngineReferences)
    com.sharpwr.acceptance/        # QA PlayMode acceptance tests (owned by qa)
  sim/                             # SharpWR.Sim.csproj + tests/ (NUnit, dotnet test)
  server/                          # headless authoritative server (.NET 8), M5+
  unity/                           # Unity 6.3 LTS project (created in M0 with URP)
    Packages/manifest.json         # adds "com.sharpwr.sim": "file:../../packages/com.sharpwr.sim"
    Assets/SharpWR/
      Bootstrap/      # scene entry, content loading, offline host loop
      Presentation/   # entity views, interpolation, animation, VFX/audio hooks
      Input/          # touch joystick, skill buttons with drag-aim, desktop mouse/keys → commands
      Camera/         # isometric camera rig, follow/lock, edge panning (desktop)
      UI/             # HUD, health bars, cooldowns, damage numbers, debug overlay
      Scenes/         # Practice.unity, Arena.unity
      Art/            # original or licensed assets only
      Tests/EditMode/ Tests/PlayMode/   # presentation tests (unity-gameplay)
```

Assembly definitions: `SharpWR.Sim` (package) ← `SharpWR.Presentation` ← `SharpWR.Bootstrap`;
test asmdefs reference the assembly under test only. Player builds exclude
`content/reference-riot` (it is never placed under `Assets/` or Addressables).

## 6. Target hardware (initial)

| Tier | Example class | Target |
|---|---|---|
| Minimum Android | 4 GB RAM, Mali-G57/Adreno 610 class, Android 10+ | 30 fps stable, 720p render scale |
| Recommended Android | 6–8 GB RAM, Adreno 650+ | 60 fps |
| iOS (later) | A13+ | 60 fps |
| Desktop dev/test | any x64/ARM64 with Unity editor | 60+ fps, used for desktop input |

Budgets are in `07-performance.md`; they are targets to be measured on real devices in M1,
not claims.
