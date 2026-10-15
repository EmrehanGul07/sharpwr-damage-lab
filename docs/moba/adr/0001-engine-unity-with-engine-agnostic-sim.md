# ADR-0001 · Unity 6.3 LTS client, engine-agnostic C# simulation

Status: proposed (validate in M0) · Date: 2026-10-15

**Context.** Requested stack is Unity 6 + C#. The repository already has a three.js arena
(120 Hz, bots, lanes) and a Python reference engine. Target: mobile-first 3D MOBA, later
server-authoritative 5v5.

**Decision.** Unity 6.3 LTS (URP, IL2CPP) for the client. All gameplay rules live in
`com.sharpwr.sim`, a local UPM package with `noEngineReferences: true`, also compiled by
`game/sim/SharpWR.Sim.csproj` (netstandard2.1) for `dotnet test` and a headless .NET server.

**Consequences.** + fast, cross-platform sim tests without Unity; + same sim offline and on the
server; + rendering can evolve independently. − the three.js arena is not reused as code (kept
as behaviour reference); − Unity license secrets needed for CI builds.
