# Marksman implementation queue — 2026-10-03

All 23 champions are connected to Skill Lab. All adapters are provisional: integration completion does not imply verified Wild Rift parity.

Each champion has an executable event timeline, automatic ranks, item callbacks, resource handling and movement. Unknown timings and source conflicts remain explicit in runtime assumptions and the in-game TODO.

| Order | Champion | Catalogue | Fight engine | Missing mana slots |
|---|---|---|---|---|
| 1 | Samira | 5 slots | Provisional | — |
| 2 | Smolder | 5 slots | Provisional | — |
| 3 | Twitch | 5 slots | Provisional | — |
| 4 | Yunara | 5 slots | Provisional | — |
| 5 | Lucian | 5 slots | Provisional | — |
| 6 | Varus | 5 slots | Provisional | W |
| 7 | Ezreal | 5 slots | Provisional | — |
| 8 | Vayne | 5 slots | Provisional | — |
| 9 | Tristana | 5 slots | Provisional | — |
| 10 | Ashe | 5 slots | Provisional | E |
| 11 | Kalista | 5 slots | Provisional | W |
| 12 | Draven | 5 slots | Provisional | — |
| 13 | Caitlyn | 5 slots | Provisional | — |
| 14 | Jinx | 5 slots | Provisional | — |
| 15 | Kai'Sa | 5 slots | Provisional | — |
| 16 | Kog'Maw | 5 slots | Provisional | R |
| 17 | Miss Fortune | 5 slots | Provisional | — |
| 18 | Xayah | 5 slots | Provisional | — |
| 19 | Sivir | 5 slots | Provisional | E |
| 20 | Corki | 5 slots | Provisional | — |
| 21 | Senna | 5 slots | Provisional | — |
| 22 | Zeri | 5 slots | Provisional | — |
| 23 | Jhin | 5 slots | Provisional | — |

## Remaining work by champion

### 1. Samira

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: R AH/static cooldown ve başlangıç anı; W1–E–W2 Style/Conqueror sırası; W2/R sonraki hit'lerde süre yenileme; CC özel AA/retrigger/reset; gerçek WR channel/shot offsetleri
Unresolved mana: none.

### 2. Smolder

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: E bolt sayısı/stack grant; W sneeze/explosion/stack işlem sırası; burn refresh/snapshot/rounding/rün amplification; %50 crit + %230 crit damage çapraz nokta; Q100 patlamalarının ana hedefe overlap'i
Unresolved mana: none.

### 3. Twitch

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Patch/veri çelişkisi; E global metadata ve hedef eligibility; W AS-dependent cast candidate
Unresolved mana: none.

### 4. Yunara

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: 1–15 tüm seviyelerde core stat ve mana regen kaydedildi; MS 335 ve AA range 575 teyitli. HP regen birimi; AD/AS görüntüleri ile eski formüllerin/rün katkılarının uzlaştırılması; W hareketli hedef/contact geometrisi; Q/W/P damage classification açık. Normal W ilk hit + 4 ek tick, 0.25s aralık/1s süre teyit edildi.
Unresolved mana: none.

### 5. Lucian

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: İkinci shot level progression; R bullet rounding/cap; Q level-dependent cast timing
Unresolved mana: none.

### 6. Varus

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: W mana bedeli; Q bonus AD vs total AD kaynak çelişkisi; skill menzilleri; Phantom damage tags
Unresolved mana: W.

### 7. Ezreal

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q Kraken/Phantom/Terminus sayaç kapsamı teyitli; Q Rageblade AS stack kazanımı, Q/W detonation ve diğer item eligibility açık; Q/AA ortak sayaç testi tekrar istenmez
Unresolved mana: none.

### 8. Vayne

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Tumble süresi/endpoint; passive/on-hit classification
Unresolved mana: none.

### 9. Tristana

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: W trajectory; E/R hedef menzili; R damage tag
Unresolved mana: none.

### 10. Ashe

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q oklarında on-hit/Hexoptics split; Frost ilk hit farkı; Volley mana kaynağıyla kullanıcı referansı çelişiyor (kullanıcı değerleri korundu)
Unresolved mana: E.

### 11. Kalista

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Hop speed/distance/boots ve kite geometrisi; Q/E range
Unresolved mana: W.

### 12. Draven

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Axe catch gerçek timing; axe crit scope
Unresolved mana: none.

### 13. Caitlyn

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Headshot level/crit progression; R crit etkisi; trap ammo/recharge/arming
Unresolved mana: none.

### 14. Jinx

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Rocket mana ve silah geçişi; E delivery/arming; R mesafe hasar eğrisi
Unresolved mana: none.

### 15. Kai'Sa

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Passive level progression; E WR charge/AS formülü; Phantom on-hit kapsamı
Unresolved mana: none.

### 16. Kog'Maw

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: R mana ramp kaynak çelişkisi; R missing-health interpolation; 5 değerli range kaydının WR 3 rank eşlemesi
Unresolved mana: R.

### 17. Miss Fortune

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Love Tap level/crit progression; eligible on-hit
Unresolved mana: none.

### 18. Xayah

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q efektif hız ve yukarıdaki I03; R WR lock süresi
Unresolved mana: none.

### 19. Sivir

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q 1450/1200 gidiş/dönüş WR doğrulaması; Morale cap/expiry
Unresolved mana: E.

### 20. Corki

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: R recharge kaynak çelişkisi ve package kapsamı; AA refund; E/W tick cadence; pasif–Spellblade/crit sırası
Unresolved mana: none.

### 21. Senna

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Soul generation ve pasif level progression; WR windup level modifier; Q target reach ile beam reach ayrımı
Unresolved mana: none.

### 22. Zeri

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Flat damage progression; Q cast/attack ilişkisi; E endpoint ve W normal/wall varyant menzili
Unresolved mana: none.

### 23. Jhin

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: AD dönüşümü temporary AS dahil oyun içi çapraz kontrol; 4. AA launch/ammo/reload; W beam timing; W/R WR damage tag'leri
Unresolved mana: none.

## Important source limits

Blank cost fields were not interpreted as zero. Explicit `none` was interpreted as zero with its source retained.
Kog’Maw R template has five ranks and a 40–400 conditional cost; the user WR record has three ranks and a different mana ramp. This conflict is retained and not applied.
All 23 champions use user-authorized PC timing proxies with WR stats. Proxy data is present; WR parity remains unverified.
See docs/all-marksman-fight-engine.md for executable mechanics, conservative exclusions and outstanding parity checks.
