# Rageblade startup cadence correction — V5.74.0

User test on 2026-10-02: Smolder level15, Rageblade only, AD138/AP30/AS1.27. Ordered ten AA results: physical74 each, magic16 each, with two separate16 magic indicators at AA6 and AA9. The requested setup was zero item/combat stacks, no skills. This confirms the observed startup cadence; AS stack values and expiry were not measured.

Old kernel began the three-hit Phantom counter only when four stacks existed before the attack, producing AA7/10. The attack granting stack4 now starts the eligible three-hit cycle, producing AA6/9/12. Four-stack AS cap and existing on-hit damage values remain unchanged. The UI counter follows the corrected cycle. Skill on-hit eligibility and Phantom interaction with Kraken/Terminus remain TODO.

Kraken only: Smolder15 AD148/AP0/AS1.30/crit0; physical sequence79,79,170,79,79,172,79,79,174. Rune page Fleet Footwork/Battle Zeal/Cut Down/Legend Bloodline/Bone Plating. Item tooltip confirms ranged level15 raw168, +0.75% per1% missing HP, max+75%. The existing kernel with Cut Down and sequential health loss reproduces the integer sequence using upward displayed rounding. Exact per-hit game HP and display-rounding implementation were not independently measured. No Kraken damage coefficient changed.

Regression covers Phantom startup and preserved stack cap, and the observed Kraken nine-hit sequence. Measurements are in [smolder-item-aa-tests-20261002.json](../data/smolder-item-aa-tests-20261002.json). All414 item-adoption cells across23 champions are regenerated because this is a shared item mechanic.
