# ADR-0004 · Riot data for validation only; shipped content is original

Status: proposed — needs owner confirmation · Date: 2026-10-15

**Context.** Riot's policy prohibits its IP in games/apps (see `../10-legal-and-ip.md`).

**Decision.** Reference data (`ip: riot-reference`) is used only in tests and an optional,
never-distributed reference build. Playable/shareable builds use original champions, items,
runes, map and art. Enforced by content validator R4/R5 and the art guard hook.

**Open.** Owner decision on (a) whether a private reference build is acceptable at all,
(b) the first original champion's identity and design values.
