# ADR-0003 · Monorepo with a protected Python reference

Status: proposed · Date: 2026-10-15

**Decision.** The game lives under `game/` (+ `tools/`, `docs/moba/`, `.claude/`) in the
existing repository. The Damage Lab stays where it is, unchanged, and is write-protected for
agents by a PreToolUse hook; exporters read it and write generated fixtures/content with
`--check` freshness gates. Rationale: parity fixtures and the reference evolve together in one
commit history; no cross-repo version drift.

**Consequences.** Damage Lab CI paths must not trigger on `game/**` (they do not today); repo
size grows with Unity assets → Git LFS for binary art from M1.
