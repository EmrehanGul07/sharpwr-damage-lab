# SharpWR MOBA — game workspace

| Path | What |
|---|---|
| `packages/com.sharpwr.sim/` | Engine-agnostic deterministic simulation (C#, local UPM package) |
| `sim/` | `dotnet` build of the same sources + NUnit tests (`dotnet test sim/tests/SharpWR.Sim.Tests.csproj`) |
| `parity/fixtures/` | Generated expected values from the Python Damage Lab (`tools/parity`) |
| `content/` | Champion/item/rune/AI/roster data with provenance (`tools/content/validate_content.py`) |
| `content/reference-riot/` | Riot reference data for private validation — never shipped |
| `unity/` | Unity 6.3 LTS client (created in M0 step S1, see `unity/README.md`) |
| `server/` | Headless authoritative server (M6) |

Start at `docs/moba/README.md`.
