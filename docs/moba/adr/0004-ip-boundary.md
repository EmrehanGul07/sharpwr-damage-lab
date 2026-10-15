# ADR-0004 · Personal-only game; Riot reference content kept separable

Status: **accepted (rev 2)** · Date: 2026-10-15

**Context.** Riot's policy prohibits its IP in games/apps (see `../10-legal-and-ip.md`). The
owner decided on 2026-10-15: the game is for personal use only and will not be published or
shared.

**Decision.**
- The personal build may use Riot reference content: Samira and other Damage Lab champions
  (`game/content/reference-riot/`) and the existing SharpWR fan models/icons.
- That content stays **separable**: data in `content/reference-riot/`, art only in
  `game/unity/Assets/SharpWR/Reference/`, rosters declare `distribution: "personal"`.
- A `public` roster may list only `ip: "original"` champions (validator R5), and a public
  build must exclude the Reference folder. Nothing public is planned; the guard keeps the
  option of an original version open without a rewrite.

**Superseded (rev 1).** Required an original first champion for any playable build.

**Consequences.** M1 plays Samira. No original champion design is needed now. Builds are never
uploaded to stores or shared links.
