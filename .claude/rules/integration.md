# Integration rules for parallel agents

Applies to every agent in every task.

## Ownership
- `.claude/ownership.json` assigns each governed path to exactly one owner. Write only inside
  your paths. Reading anything is fine.
- Before finishing: `python -I tools/ownership/check_ownership.py diff --owner <you>` must pass.
- Need a change in someone else's path? Stop and hand back to the lead with the exact request
  (file, interface, reason, test that proves it). Do not edit it yourself.
- Parallel agents work in separate git worktrees/branches; the lead merges one owner's branch
  at a time and runs the fast tier after each merge.

## Shared contracts (Numerics, Core, Contracts, CombatEvent.cs)
Owned by combat-engineer. To change one:
1. Write a short ADR in `docs/moba/adr/` (lead approves) describing the change and consumers.
2. Make the change backward compatible if possible; otherwise update all consumers in the same
   merge via their owners.
3. Regenerate fixtures/vectors if numerics changed; all suites green before merge.

## Definition of done (any task)
- Tests written first for behaviour changes; all tiers that apply are green
  (`python -I tools/ci/fast_checks.py` at minimum, `dotnet test` where .NET is available).
- No new "unsupported" behaviour hidden: every gap is listed.
- Report: what changed, evidence (commands + results), unverified assumptions, blockers.
- Never claim completion with failing or unrun acceptance tests; say what could not be run and why.
