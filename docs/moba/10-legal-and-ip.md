# 10 · Intellectual property boundary

Not legal advice. This records the engineering constraints the project follows; the owner
should confirm the position with a qualified adviser before distributing anything.

## The constraint

Riot's fan-content policy states that Riot prohibits use of its IP in games and apps, and names
character appearance and abilities, maps, icons and items as parts of the IP
([riotgames.com/en/legal](https://www.riotgames.com/en/legal)). Exceptions require a written
license or Riot API-based projects under the API terms. A playable MOBA is a game; a champion's
kit is a protected element. The brief already says not to assume permission to redistribute
Riot IP — this goes further: the **shipped game must be original**.

## Engineering rules

| Rule | Enforcement |
|---|---|
| Riot reference data lives only in `game/content/reference-riot/` with `ip: "riot-reference"`, `shippable: false` | `tools/content/validate_content.py` R4 |
| Shippable content uses only original/placeholder/unresolved statuses (no `wr_*`, `damage_lab_*`, `pc_*`) | validator R4 |
| Rosters may list only shippable champions | validator R5 |
| Riot art (icons, portraits, the 23 champion GLBs) never enters `game/` | `.claude/hooks/guard_paths.py` |
| Reference content is never placed under `game/unity/Assets/` or Addressables; a reference build needs the `SHARPWR_RIOT_REFERENCE` define and is never distributed | build script check (M1, qa) |
| Original champions are not thin re-skins of a Riot kit: design review checks names, silhouettes, ability combinations and numbers | manual design review per champion |
| Map is original (lane count/shape of a generic 3-lane MOBA is a genre convention; Rift-specific layout, art and objective identities are not used) | manual design review |
| Third-party assets: license recorded in `game/unity/Assets/SharpWR/Art/LICENSES.md` per file | qa checklist |

## What remains allowed

Using the Damage Lab and its Riot-derived data privately to validate that the engine computes
MOBA combat correctly (the same numbers the existing fan tool already uses), and the existing
non-game Damage Lab itself, which carries Riot's required notice. The owner should separately
review whether the existing Android app's Practice/1v1 features fit the policy.
