# Essence Reaver carrier crit fix v5.79.0

On-hit skill callbacks force AA crit probability0 because they carry no AA base damage. That value incorrectly also suppressed ER's crit-dependent Spellblade term. The kernel now snapshots independent Spellblade crit before accepting the AA crit override; Ezreal and Smolder callbacks explicitly forward current build/Yun Tal crit. AA behavior and item coefficients are unchanged.

Regression tests cover both Q adapters, zero AA carrier crit with25% build crit, and explicit50% current crit. At25% this restores20 raw physical ER damage; at50%,40 raw. Armor and rune modifiers apply as before. No ingame confirmation is needed for separation of two unrelated code inputs. Actual item-Q eligibility remains an open WR TODO.
