# Guinsoo / Stormrazor paired comparison — engine5.79

23 champions; level5 one item and level15 five items; squishy/bruiser/tank.336 pairs. Each pair changes only the tested item; same other items, boots, runes, starting distance, skill/movement/ultimate policies. Level5 Boots of Dynamism, level15 Armorcrusher Boots; Conqueror/Brutal/Cut Down.

**Locked Stormrazor default unchanged:**120 magic,7 eligible-hit cadence. Uncharged starts model current Item Value; charged starts are an alternative condition. No slow/utility score.

| Condition | Pairs | Guinsoo shorter TTK | Stormrazor shorter TTK | Tie |
|---|---:|---:|---:|---:|
| 5:screen_background:charged=False | 69 | 49 | 17 | 3 |
| 5:screen_background:charged=True | 69 | 32 | 37 | 0 |
| 15:screen_background:charged=False | 69 | 51 | 16 | 2 |
| 15:screen_background:charged=True | 69 | 44 | 23 | 2 |
| 15:avoid_crit_overcap:charged=False | 30 | 9 | 21 | 0 |
| 15:avoid_crit_overcap:charged=True | 30 | 9 | 21 | 0 |

## Findings

- Uncharged Stormrazor deals no Energized damage before eligible hit7; Guinsoo adds magic from hit1. Starting charge matters in short fights.
- Some retained Guinsoo backgrounds already reach100% crit from the other four items. A Stormrazor swap reaches125%, wasting25 points under the cap.
- For those30 backgrounds an additional experiment replaced one25% crit item with a fixed noncrit item in BOTH paired builds. With75% versus100% crit, Stormrazor won21/30 pairs. This is a different background experiment, not a one-variable comparison with the original full-crit background.
- Charged first-item level5/squishy: Stormrazor18/23, Guinsoo5/23. Tank: Guinsoo16/23, Stormrazor7/23.
- TTK and1/2/3-second damage windows are stored separately. Damage after death is HP-capped; dead_by_seconds marks deaths.

## Examples — level15 / Darius

Fixed IE + LDR + Yun Tal + Kraken; Armorcrusher Boots; same runes/policy. Stormrazor starts charged.

| Champion | Guinsoo TTK | Stormrazor TTK | Crit G/S |
|---|---:|---:|---|
| Tristana | 3.092s | 2.881s | 75% / 100% |
| Samira | 3.799s | 3.172s | 75% / 100% |
| Jinx | 5.124s | 4.623s | 75% / 100% |

## Limits

Backgrounds come from retained Guinsoo candidates and are not an unbiased global-optimum search. Each pair holds policy fixed; Stormrazor-specific reoptimization was not done. Rune/boot choices are fixed rather than champion-optimal. Unknown WR mechanics remain model assumptions. Slow, actual movement-driven charge and moving targets are not modeled by this test. Results are simulator outputs, not new ingame validation.

Item Value rankings and item coefficients were not manually changed. Reproduce with `PYTHONPATH=tests:. python scripts/compare_rageblade_stormrazor.py`; full data in `data/rageblade-stormrazor-paired-comparison.json`.
