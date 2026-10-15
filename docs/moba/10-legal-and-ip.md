# 10 · Intellectual property boundary

Not legal advice. This records the engineering constraints the project follows.

## The constraint

Riot's fan-content policy states that Riot prohibits use of its IP in games and apps, and names
character appearance and abilities, maps, icons and items as parts of the IP
([riotgames.com/en/legal](https://www.riotgames.com/en/legal)).

## Owner decision (2026-10-15, ADR-0004 rev 2)

The game is **for the owner's personal use only**. It is not published, uploaded to a store,
or shared. Under that decision the personal build plays Riot reference content (Samira first).

## Engineering rules

| Rule | Enforcement |
|---|---|
| Never publish, upload or share a build (stores, public links, release assets) | owner + `CLAUDE.md` |
| Riot data lives only in `game/content/reference-riot/` (`ip: "riot-reference"`) | validator R4 |
| Rosters declare `distribution`; `personal` may list reference champions, `public` only `ip: "original"` | validator R5 |
| Riot-derived art (fan models, icons) only in `game/unity/Assets/SharpWR/Reference/` | `.claude/hooks/guard_paths.py` |
| CI artifacts of game builds are private and short-lived; no release uploads for game builds | `game-ci.yml` review (qa) |

These keep Riot content separable. If the owner ever wanted to share a version, it would need
original champions/art and a `public` roster; the checks above make that a content swap, not a
rewrite.
