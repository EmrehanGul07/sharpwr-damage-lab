# Yunara full level snapshots — V5.73.0

User WR practice screenshots supplied 2026-10-02 now cover all 15 levels. Exact displayed HP/mana/armor/MR values replace intermediate-level interpolation. These are rounded UI observations, not claims about hidden decimal growth coefficients.

| Level | AD displayed | HP | Mana | Armor | MR | AS displayed | HP regen displayed | Mana regen / 5s |
|---|---|---|---|---|---|---|---|---|
|1|58|630|345|35|30|0.82|6|9|
|2|61|725|370|39|32|0.83|7|10|
|3|63|825|396|42|33|0.85|7|11|
|4|66|930|423|46|34|0.87|8|11|
|5|68|1040|451|50|35|0.89|8|12|
|6|71|1155|481|54|36|0.90|9|12|
|7|74|1276|512|58|38|0.92|9|13|
|8|77|1401|544|63|39|0.94|10|14|
|9|80|1532|578|67|40|0.97|10|14|
|10|83|1667|613|72|42|0.99|11|15|
|11|86|1808|649|77|43|1.01|12|16|
|12|90|1954|687|82|45|1.03|12|17|
|13|93|2105|726|87|47|1.06|13|18|
|14|97|2261|766|93|48|1.08|14|18|
|15|100|2422|807|98|50|1.11|14|19|

MS 335 and AA range 575 remain verified. Mana regen unit confirmed by user observing approximately 4 mana each second with displayed regen 19. The runtime uses 19/5=3.8/s. HP regen unit is not separately confirmed and is not needed for the current target-never-damages-us simulator. AD/AS observations are retained; original coefficients remain unchanged pending rune/rounding reconciliation.

Regression tests verify every observed mana value, full 15-level coverage, Muramana max-mana propagation and mana clock regeneration (807 mana, W60 ->747, five seconds later766). The affected 18 Yunara item-adoption cells are regenerated; the other 396 unchanged cells are preserved. Growth coefficients remain unknown rather than fitted to rounded observations.
