# SharpWR MOBA — engineering index

Current milestone: **M1 Vertical slice — simulation complete, Unity items pending**
(`milestones/M1-vertical-slice.md`, damage report `milestones/M1-parity.md`).
Next: owner creates the Unity project (`game/UNITY_SETUP.md`), then close M1 and start M2.
M0 (`milestones/M0-foundation.md`): C# now compiled and tested in CI on 4 platforms.

| # | Document | Brief deliverable |
|---|---|---|
| 00 | [Audit](00-audit.md) | Reusable assets, limitations, IP finding, test baseline |
| 01 | [Architecture](01-architecture.md) | 1 technical architecture · 2 dependency map · 5 Unity structure · engine evaluation · target hardware |
| 02 | [Data migration](02-data-migration.md) | 3 data migration strategy, provenance statuses |
| 03 | [Combat event model](03-combat-event-model.md) | 4 tick pipeline, ordering contract, damage pipeline |
| 04 | [Networking](04-networking.md) | 6 server-authoritative design |
| 05 | [Ability framework](05-ability-framework.md) | 7 data + hooks, unsupported gating, Samira mapping |
| 06 | [Testing](06-testing.md) | 8 tiers, parity harness, hooks |
| 07 | [Performance](07-performance.md) | 9 budgets |
| 08 | [Roadmap](08-roadmap.md) | 10 milestones M0–M8 |
| 09 | [Vertical slice](09-vertical-slice.md) | First playable plan + acceptance |
| 10 | [Legal and IP](10-legal-and-ip.md) | Riot IP boundary rules |
| ADR | [adr/](adr/) | 0001 engine · 0002 fixed point · 0003 monorepo · 0004 IP |

Claude Code configuration: `/CLAUDE.md`, `.claude/rules/`, `.claude/agents/`, `.claude/skills/`,
`.claude/settings.json` (hooks), `.claude/ownership.json`.

## Decisions needed from the owner

Decided 2026-10-15: personal-only game, Samira is the first champion (ADR-0004 rev 2).

1. **Unity licensing for CI** (Personal/Pro seat; `UNITY_LICENSE` secret for GameCI).
2. **Repository layout** (ADR-0003): game inside this repo (recommended) vs a separate repo.
3. **Reference devices** for performance acceptance (one minimum-tier, one recommended Android).
