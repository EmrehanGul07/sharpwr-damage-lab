# Oyun içi doğrulama TODO — 1 Ekim 2026

Bu liste kalıcıdır. Akşam test sonuçları geldikçe maddeler kapanacak; bilinmeyenler sıfır veya kesin değer olarak kaydedilmeyecek. Hedef sabit kukla, bize saldırmıyor. Her ölçümde champion level, skill rank, toplam AD/AP/AS, crit chance/damage, mana ve rünler yazılmalı. Aynı kukla, aynı HP/armor/MR; farklı denemelerde kukla/stack resetlenmeli. Rünlerin tetiklenmesi hasarı değiştirebileceği için hangi buff aktif olduğuna dikkat edilmeli.

## Öncelikli ve sayı/metin ile yapılabilecekler

- [ ] **T01 — Muramana Q/W/E/R Shock tekrarları.** Her skill için Muramana ile/olmadan karşılaştır. Itemlerden gelen AD/crit farkını kaydet. W'nin iki vuruşunda ayrı fark var mı? R'nin her atışında mı, ilkinde mi, aralıklarla mı? V5.57 yalnızca cast'in ilk başarılı vuruşuna %3 max mana ekliyor; çoklu-vuruş tekrar kuralı henüz doğrulanmadı. Samira ranged şampiyon olduğu için melee animasyonunun item sınıflandırmasını değiştirip değiştirmediği de ayrıca kontrol edilmeli.
- [ ] **T02 — Mana iadesi.** Manamune/Muramana ile Q: 30 harcama ve 4.5 iade; W:60/9; E:40/6. Regen nedeniyle anlık değişim okunamıyorsa tooltip açıklaması yeterli. Kısa süre sonra görülen mana ile anlık tüketimi karıştırma.
- [ ] **T03 — R cooldown ve ability haste.** R tooltip/cooldown'u 0 AH ve bilinen AH ile karşılaştır. 6 saniye static mi, AH ile azalıyor mu? Sayaç cast başlangıcında mı, channel sonunda mı başlıyor?
- [ ] **T04 — Level büyümesi.** Samira itemsiz level1/5/9/15 AD, AS, max mana, HP, armor/MR. Var olan AD/AS kullanıcı referansları korunuyor; engine'in eski büyüme eğrisi WR ile ayrıca doğrulanmalı. Sadece ekran statlarını yazmak yeterli.
- [ ] **T05 — Skill on-hit/Spellblade.** Tek itemle Q/W/E/R kullan; BORK, Wit's End, Nashor, Terminus, Kraken ve Rageblade stack/proc üretiyor mu? Essence Reaver/Trinity/Iceborn için skill'in kendisi proc hasarı veriyor mu, yoksa sonraki AA mı? Aynı cast içinde kaç kez? İtemler tek tek test edilmeli.
- [ ] **T06 — Energized dolumu.** Başlangıç charge, tek AA sonrası charge, skill sonrası charge, yürürken/dash sonrası charge. RFC/Stormrazor/Shiv için ortak charge olup olmadığı, reset ve dolum katsayıları. Engine hareketi artık hesaplıyor, fakat doğrulanmış dolum katsayısı olmadığından tekrar charge üretmiyor.
- [ ] **T07 — AS item buff süreleri.** Rageblade stack süreleri ve reset şartları (PD 6s kullanıcı teyitli; yeniden ölçüm istenmez); Yun Tal Flurry süresi/CD/AA ile cooldown azaltımı; Fiendhunter R sonrasında AA sayısı ve AS buff sona ermesi. Metin tooltip yeterli olan alanlar önce kapatılmalı.
- [ ] **T08 — WR skill timing/range metinleri.** W aktif süresi, R süresi, E dash mesafesi/hızı, Q ve AA projectile hızları varsa kaynak/tooltip. Şu anda kullanıcı onaylı PC timing fallback'ları ayrı kayıtlı.
- [ ] **T09 — Style/Conqueror çoklu-hit davranışı.** W1→E→W2 hangi Style artışını veriyor? W2/R'nin sonraki atışları Conqueror süresini yeniliyor mu? Yeni stack mi yoksa yalnızca süre yenileme mi?
- [x] **T10 — Spellblade satın alma kısıtı.** Kullanıcı teyidi: yalnızca bir Spellblade alınabilir. Picker ve optimizer bu kuralı uygular; tekrar oyun içi test istenmez.

## Sonraya bırakılabilen, daha zor doğrulamalar

- [ ] **T11 — Gerçek WR AA base windup / melee-ranged ayrımı.** Şimdilik PC base0.2279635s ve WR bonusAS×0.5 formülü kullanılıyor; kullanıcı ekran kaydı yapmak zorunda değil, uygun kaynak bulunursa kapatılabilir.
- [ ] **T12 — R'nin kesin tek tek shot offsetleri.** Şimdilik PC reference2.013s içine eşit aralıklı10hit, channel2.277s. Kesin WR atış planı farklı olabilir.
- [ ] **T13 — Hitbox / edge-center mesafe / MS soft cap.** Nokta-hedef yaklaşımı ve build MS toplaması geçici. Kaynak bulunursa manuel ölçüm gerekmeyebilir.
- [ ] **T14 — Immobilize hedefe pasif özel AA.** Ranged/melee özel hit sayısı, toplam hasar, retrigger10s, on-hit bir kere mi, AA reset/dash davranışı. Kukla CC olmadığı standart testlerde devrede değil.
- [ ] **T15 — AA atış anı ile hasar anı snapshot.** AD/crit buff'ları, AS ve item stack'leri AA launch'ta mı impact'te mi değerlendiriliyor? Mevcut kernel on-hit durumunu impact'te ilerletir; hasar stat snapshot ayrımı doğrulanmalı.

- [ ] **T16 — Diğer offensive keystone/rünler.** Samira replay şu anda Conqueror/Lethal Tempo ve desteklenen damage rünleriyle sınırlı. First Strike vb. desteklenmeyen loadout çalıştırılmıyor; bunların ayrı proc/cooldown koşulları kaynak/test ile tamamlanmalı.

## Smolder ve kite modeline eklenen açıklar

- [ ] **T17 — Smolder timing/menziller.** Q/W/R cast ve projectile süreleri, E sırasında AA/diğer skill kilitleri ve E bolt gerçek offsetleri. Mevcut yeni adapter Q/W/R impactlerini anlık, E'yi1.25s içinde dağıtır; gerçek WR timing diye doğrulanmadı. Smolder AA windup bilinmiyor; PC Samira base'i ona aktarılmadı. Q550/W1000/E700/R2000 provisional range kapıları.
- [ ] **T18 — E bolt/stack.** 10stack5 ve100stack7 tooltip ölçümleri nearest(5+0.0154S) adayını destekliyor. Gerçek bolt sayısı ve her boltun stack verip vermediği hâlâ açık. Adapter şimdilik cast/target başına+1stack kullanır; fazla stack uydurmaz.
- [ ] **T19 — W işlem sırası.** Sneeze hit stack grant, explosion stack magic damage ve doğrudan hedefin bu iki hasarı alma sırası. Çoklu hedefte subsequent explosions birinci100%,diğerleri75% ölçümleri saklı; tek hedef modelinde ikincil kukla yok.
- [ ] **T20 — Burn refresh/snapshot/tick.** İlk tick Q ile aynı anda ve6sonraki tick doğrulandı. Eşit0.5s aralık,D/7 ve yeniden Q'da eski burn iptali adaydır. Gerçek yenileme/tick offsetleri, rune true damage amplifikasyonu ve rounding açık.
- [ ] **T21 — Q crit çapraz kombinasyon.** Resmî7.1e additive (critRate+bonusCritDamage)×45% yazıyor. Kullanıcı0/100crit ve200/230critdamage ölçümleriyle uyumlu. %50crit/%230critdamage gibi çapraz noktayı doğrula; critDamage200% üzerine gelen bonus ayrı tutulur.58.5 maksimum ifadesinin evrensel cap olup olmadığı açık.
- [ ] **T22 — Q100stack ekstra patlamaların ana hedefe yeniden vurması.** Model tek champion'a Q direct damage ekler;25stack AoE/100stack arkaya giden patlamalar ikinci hedef olmadan hasarı çoğaltmaz. Gerçek overlap/geri isabet varsa koşul test edilmeli.
- [ ] **T23 — Kite hareket/proc.** Hareket menzil çemberinde sağ-sol yay hareketi olarak modellenir. Hedef collision radius, MS cap'leri, Energized'ın bu hareket ve E flight ile dolumu ve RFC bonus AA range'i doğrulanmalı. Katsayı bulunmadan hareketten ek Energized proc uydurulmaz.

## Bilerek test istenmeyen kapsam

Rakibin bize hasar vermesi, kendi ölümümüz, kendi regen/lifesteal ile hayatta kalma bu sabit-hedef hasar modelinin kapsamına dahil değil. Başka marksmanların özel ability engine'leri bu Samira denetiminin tamamlanması anlamına gelmez; ayrı aşamalardır.

## All-champion follow-up queue

All 23 champions have an ordered checklist in [marksman-task-queue.md](marksman-task-queue.md). The current list distinguishes collected ability data from pending timeline adapters. Per-champion unresolved mechanics and the five remaining mana slots are recorded there. User-confirmed values must not be re-requested. No unsupported adapter is marked complete.


## All 23 adapters connected — remaining parity checks

See [all-marksman-fight-engine.md](all-marksman-fight-engine.md) for per-champion runtime assumptions. All integration work is complete; the listed in-game measurements remain open.

Priority: Jhin conversion in-game cross-check (WR 7.3 formula implemented); Xayah lateral feather paths (WR falloff implemented); Yunara core stats and W linger; Senna mist generation and level scaling; Twitch patch conflict; Corki recharge and package; Varus W mana and Q bonus-vs-total AD scope; Kog’Maw R mana ramp. General AA windup/projectile timings and exact dash endpoints remain unresolved except explicitly sourced values. Do not repeat previously confirmed mana costs.


## User-requested item tests — V5.60.3

- [ ] I01 — Rageblade + Kraken + Terminus: isolated AA counters, Phantom Hit repeats, damage types, stack/penetration order and eligible skill-on-hit behavior. Keep current values until in-game measurements.
- [ ] I02 — Hexoptics C44: distance breakpoints/cap; applicability to AA, skill, passive, physical, magic and true damage; movement/range interactions.

User locks: Phantom Dancer stack duration is 6 seconds; continuous attacking benchmark does not pause that long. No change requested. Youmuu momentum is out-of-combat and excluded from this always-in-combat benchmark. RFC, Stormrazor, Statikk and Yun Tal measured defaults stay unchanged.

Implemented rules: only one Spellblade purchase; strongest-percentage fallback exists for legacy input only; Galeforce dash up to 325 and hit radius 600; Fiendhunter only after actual R cast. Champion mana/growth/regen comes from recorded WR stats. Yunara missing core mana is still manual, never invented.

Muramana 7.3: Shock has no additional mana consumption and uses maximum mana (AA 1.5%, ranged ability 3%); Awe refunds 15% of skill mana spending. Ability damage can carry ordinary on-hits without also injecting AA Shock a second time. Repeat Shock eligibility for multihit channels remains a separate unresolved WR detail.
Source: https://wildrift.leagueoflegends.com/en-us/news/game-updates/wild-rift-patch-notes-7-3/

### Ranking formula cross-checks (offline formulas completed in V5.61.0)

- Jhin: compare displayed AD at fixed level with crit and AS items; confirm conversion excludes no eligible temporary AS source. Coefficients are sourced, not missing: 30% bonus AS + 40% crit chance + 3% level.
- Xayah: compare E with 1/3/5/10 aligned feathers; sourced multipliers are 1/2.7/4/5.5 times single-feather damage. Check expiry and lateral recall paths separately. No PC coefficient substitution.

## Hazır ölçüm sırası — Hexoptics → item üçlüsü → Xayah

Oyun içi ölçümler bekleniyor. Üçünün offline model kontrolü ve ölçüm kurulumu hazır; bu, oyun kurallarının teyit edildiği anlamına gelmez. [Adım adım ölçüm listesi](priority-ingame-test-protocol.md), [mevcut engine tahminleri](../data/priority-test-predictions.json).

1. **I02 / Hexoptics:** H01 tooltip + yakın/max-range normal AA; H02 yakın/uzak Q; H03 magic on-hit kapsamı. Sayısal menzil ekranı yoksa pixel/breakpoint ölçümü zorunlu değil.
2. **I01 / Rageblade–Kraken–Terminus:** K01–K03 tekli sayaçlar; K04/K05 ikili/üçlü proc ritmi ve stack sırası; K06 Ezreal Q eligible on-hit.
3. **I03 / Xayah:** X01–X02 bir/üç/beş tüy E oranları; X03 sağ-sol hareketle gerçek hit; X04 R fanı sonraki adım.

- [ ] H01–H03 Hexoptics scope/mesafe ölçümleri.
- [ ] K01–K06 item sayaç/phantom/penetration ölçümleri.
- [ ] X01–X03 Xayah E hasar ve lateral yol ölçümleri.
- [ ] X04 R fanı; 10+ tüy/floor kontrolü ve kesin collision geometry daha sonra.

Sabit practice rünleri değiştirilmeyecek, MR ayarı değiştirilemediğinde mevcut100 MR kullanılacak. Video istenmiyor; red/blue ayrı hasar + stat/HP/buff kaydı yeterli. Rün kaynaklı farklar analiz edilmeden item katsayısı değiştirilmeyecek.


## V5.62 · Damage classification checks

- [ ] Hexoptics: Ezreal Q/Miss Fortune Q basic damage vs Senna Q area spell damage. Zero spell-effect events must not create duplicate damage/stack gains.
- [ ] Smolder Q initial hybrid vs default burn; on-hit/Phantom Hit and Kraken stack eligibility.
- [ ] Corki basic true conversion vs separate item/rune additional true damage.
- [ ] Ashe Q first arrow vs remaining four arrows: confirm Magnification split without replacing existing total-damage coefficients.
- [ ] WR Kraken/Spellblade/other item BasicAttack vs Proc membership; PC item examples are not sufficient evidence.
- [ ] Resolve remaining unknown WR ability labels from docs/damage-classification-v562.md, especially Yunara, Jhin W/R and Tristana R.


## PC timing proxy verification (V5.63.0)
- Validate all 23 PC base-AA windups and projectile speeds against WR; Senna WR rule remains preserved.
- Jinx AA weapon speeds sourced from PC game files; verify WR parity. Resolve remaining skill speed gaps listed in docs/pc-combat-timing-v563.md.
- Validate compound projectile trajectories and variant speeds; do not treat stored PC expressions as verified WR timings.


## V5.64.0 combat/item audit sonrası

- [ ] Jhin dördüncü AA launch/ammo/reload sırasını ve Jinx rocket mana/weapon geçişini WR'de kontrol et. Offline regressions geçti.
- [ ] Sivir Q 1450/1200 gidiş/dönüş hızları ve uç nokta dönüşünü WR'de kontrol et; sabit .25s tahmin kaldırıldı.
- [ ] Yunara manuel mana/MS/range; W linger tick kapsamı.
- [ ] Caitlyn headshot/crit, Kai'Sa passive level progression, Lucian ikinci shot progression, Senna soul/bonus-AA ve Zeri flat progression.
- [ ] Kalista hop / Vayne tumble / Draven catch / Xayah lateral feather geometry.
- [ ] Çoklu-hit Muramana eligibility ve Fiendhunter Lucian ikinci shot sayımı; hasar sınıflandırmasına bağlı AA reduction/proc kapsamı.
- [ ] Spellblade armed-window expiry için WR tooltip/kaynak doğrulaması.

Tam offline denetim ve provisional liste: [combat-engine-audit-v564.md](combat-engine-audit-v564.md). Bu test sonucu WR birebir eşitlik onayı değildir.
