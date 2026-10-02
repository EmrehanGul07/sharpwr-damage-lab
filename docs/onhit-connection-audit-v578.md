# On-hit connection audit v5.78.0

All23 marksmen /115 ability profiles were compared with engine routes. Explicit WR TriggerOnHitEvents profiles route Ezreal Q, Miss Fortune Q, Senna Q and Smolder Q to the shared item kernel. Empowered basic attacks continue through AA. Unspecified classifications remain unknown; no new WR tag or coefficient is invented.

## Changes

- Muramana Shock no longer repeats on a Phantom event from the same attack, following the recorded once-per-attack/cast tooltip rule. Skills still use one skill Shock and do not also receive AA Shock.
- On-hit skill carriers forward primary skill damage and rune health multiplier to BotRK Phantom remaining-HP calculation. Exact skill-versus-on-hit damage order is retained as a modeling assumption pending distinct evidence; the measured AA sequence stays covered.
- Smolder initial Q now uses its own newly granted Terminus penetration for physical damage, consistent with the shared kernel ordering. The legacy untimed Smolder impact also gets a valid stack key.
- Hexoptics carrier callbacks no longer claim basic attack amplification for a zero attack base; the adapter applies the ability's own WR classification. Senna Q stays unamplified while its carried item on-hits retain their own tags.

## Regression coverage

Attack-only guards: Phantom Dancer/Yun Tal AA progression, Fiendhunter charges and Duskblade first-AA proc do not advance/consume on Q. Muramana skill Shock stays one on Phantom Q; attack Shock stays one on Phantom AA. BotRK skill-base damage reduces the following Phantom HP snapshot. Smolder Q uses updated Terminus penetration. Existing Smolder and Ezreal measurements remain covered.

## Closed versus open

No extra mixed Q/AA counter measurement is requested: separate confirmed Q and AA events use the same persistent item counters. Closed AA and Ezreal Q counter tests were removed from active work. Remaining unknowns include Rageblade Q AS stack behavior, modifier/expiry details, other skills' special effects, source-unknown damage tags and exact display rounding. User-locked RFC/Stormrazor/Statikk/Yun Tal defaults are unchanged.

This is a connection audit, not a claim that all115 profiles or all23 champions have been validated in game.
