# Energized launch/hit rules — V5.81.0

User-confirmed on 2026-10-02: RFC/Stormrazor/Statikk share movement charge (26 per 700 units). AA grants nine on hit; Statikk adds five, yielding 14. Ezreal Q grants no charge, adds a PD stack only on hit, never stacks Yun Tal crit or activates Flurry, and consumes a ready Energized proc on hit.

An AA reaching 100 does not proc. A subsequent attack consumes 100 at projectile launch; its reserved proc damages only at impact. That proc attack does not gain nine/fourteen charge. Reservations are keyed by attack ID to prevent overlapping AA/Q or secondary projectiles from duplicating/stealing one proc. Walking between launch and impact can still add new charge. Guinsoo Phantom does not grant attack charge or duplicate Energized.

The optimizer enables launch events for every Energized build. Impact-only legacy callers resolve readiness before granting attack charge. Shared-pool behavior when buying multiple Energized items is a model choice; user confirmed individual item rules, not multi-item combined behavior. Generic movement-skill exact distances and travel timing remain provisional as documented in TODO.

V5.80 seven-hit RFC/five-hit Shiv and threshold-crossing Storm assumptions are superseded. Archived paired-comparison results used earlier rules and must not be interpreted as current rankings.
