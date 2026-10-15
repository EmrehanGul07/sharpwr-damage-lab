---
name: milestone-report
description: Write the acceptance report for a SharpWR milestone with evidence — work completed, test and build results, unverified assumptions, blockers, next milestone. Use at the end of every milestone and whenever completion is being claimed (qa agent or lead).
---
# Milestone report

File: `docs/moba/milestones/<MN>-<slug>.md`. Fill every section; "none" is a valid answer,
silence is not.

```md
# <MN> · <name> — <Accepted | Not accepted>
Date · commit · Damage Lab VERSION · Unity version · .NET SDK version · devices

## Work completed
- bullet per deliverable with paths

## Evidence
| Check | Command | Platform | Result |
(every acceptance item from the roadmap/slice doc; paste counts, max errors, hashes, build
artifact names; "not run" + reason where applicable)

## Acceptance criteria
| # | Criterion | Automated? | Status | Evidence |

## Unverified assumptions
- data labelled pc_reference_provisional / damage_lab_user_sourced that the milestone relies on
- engine defaults standing in for unknown data

## Manual verification still required
- steps a human must perform, with expected result

## Remaining blockers
## Next recommended milestone
```

Rules: a milestone is "Accepted" only if every automated acceptance test ran and passed.
Suites blocked by environment are "Not run", never "Passed". Link the parity report.
