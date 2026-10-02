# Aktif TODO — V5.75.0 / 2 Ekim 2026

Bu dosya yalnız açık işleri içerir. Eski “adapter bağlı değil”, “AA windup yok” ve “Smolder skilleri anlık” kayıtları kaldırıldı: 23 adapter bağlı, PC timing proxy verileri girilmiş ve impact zamanlaması çalışıyor. Bunların WR doğrulaması ayrı bir iştir.

Kapsam: sabit, bize saldırmayan hedef; expected crit; kullanıcı tarafından doğrulanmış WR katsayıları korunur. Rünler değiştirilemediğinde mevcut rünlerle ölçülür. Video istenmez. Her ölçümde level/rank, AD/AP/AS, crit, mana, hedef HP/armor/MR ve aktif buff'lar kaydedilir. İlk impact ve sonraki tick'ler ayrı yazılır.

## Öncelikli oyun içi ölçümler

| ID | İş | Gereken bilgi |
|---|---|---|
| I01 | Rageblade + Kraken + Terminus | Kraken tek başına AA3/6/9 ve Rageblade tek başına AA6/9 phantom teyitli. Terminus tekli, ikili/üçlü sayaçlar; Phantom on-hit tekrarı; penetration sırası; skill on-hit eligibility |
| I02 | Hexoptics | Ezreal AA/Q fiziksel kapsamı ve taşınan Wits End büyü on-hitinin mesafeden etkilenmemesi teyitli (2026-10-02). Tooltip ile %0–10 bonus ve 550 mesafede maksimum teyitli. 100 mesafede %1, her50 birimde +%1, 550 mesafede %10 basamakları kullanıcı tarafından yeniden teyit edildi. Center-edge mesafe tanımı, diğer şampiyon basic/proc bileşenleri ve MF/Senna Q farkı açık. |
| I03 | Xayah | 1/3/5/10 tüy E; tüy expiry ve lateral recall collision; R fanı/10+ tüy floor |
| I04 | Muramana | Samira R/W kullanım başına tek Shock ve Ezreal Q skill Shock teyit edildi (2026-10-01). Diğer şampiyonların çoklu-hit/on-hit etkileşimleri ve melee animasyonunun ranged item sınıfına etkisi açık. |
| I05 | Fiendhunter | R sonrası üç AA/8s penceresi; Lucian ikinci shot tüketimi ve AS buff bitişi |
| I06 | Spellblade | Armed-window expiry; eligible skill on-hit proc; cooldown sırasında cast edilen skill'in sonraki AA'yı arm edip etmemesi |
| I07 | Damage classification | Item BasicAttack/Proc kapsamı; AA damage reduction'ın item/pasif eklerine uygulanması; aşağıdaki bilinmeyen WR ability tag'leri |

Ölçüm protokolü: [priority-ingame-test-protocol.md](priority-ingame-test-protocol.md). İlk pratik sıra: Hexoptics → item üçlüsü → Muramana → Xayah. Sıralama duyarlılığı sonucu ayrıca [offline-engine-review-v565.md](offline-engine-review-v565.md) içindedir.

## Şampiyon bazında açıklar

| Şampiyon | Kalan bilgi / test |
|---|---|
| Yunara | 1–15 tüm seviyelerde core stat ve mana regen kaydedildi; MS 335 ve AA range 575 teyitli. HP regen birimi; AD/AS görüntüleri ile eski formüllerin/rün katkılarının uzlaştırılması; W hareketli hedef/contact geometrisi; Q/W/P damage classification açık. Normal W ilk hit + 4 ek tick, 0.25s aralık/1s süre teyit edildi. |
| Samira | R AH/static cooldown ve başlangıç anı; W1–E–W2 Style/Conqueror sırası; W2/R sonraki hit'lerde süre yenileme; CC özel AA/retrigger/reset; gerçek WR channel/shot offsetleri |
| Smolder | E bolt sayısı/stack grant; W sneeze/explosion/stack işlem sırası; burn refresh/snapshot/rounding/rün amplification; %50 crit + %230 crit damage çapraz nokta; Q100 patlamalarının ana hedefe overlap'i |
| Jhin | AD dönüşümü temporary AS dahil oyun içi çapraz kontrol; 4. AA launch/ammo/reload; W beam timing; W/R WR damage tag'leri |
| Jinx | Rocket mana ve silah geçişi; E delivery/arming; R mesafe hasar eğrisi |
| Xayah | Q efektif hız ve yukarıdaki I03; R WR lock süresi |
| Caitlyn | Headshot level/crit progression; R crit etkisi; trap ammo/recharge/arming |
| Kai'Sa | Passive level progression; E WR charge/AS formülü; Phantom on-hit kapsamı |
| Lucian | İkinci shot level progression; R bullet rounding/cap; Q level-dependent cast timing |
| Senna | Soul generation ve pasif level progression; WR windup level modifier; Q target reach ile beam reach ayrımı |
| Zeri | Flat damage progression; Q cast/attack ilişkisi; E endpoint ve W normal/wall varyant menzili |
| Varus | W mana bedeli; Q bonus AD vs total AD kaynak çelişkisi; skill menzilleri; Phantom damage tags |
| Kog'Maw | R mana ramp kaynak çelişkisi; R missing-health interpolation; 5 değerli range kaydının WR 3 rank eşlemesi |
| Corki | R recharge kaynak çelişkisi ve package kapsamı; AA refund; E/W tick cadence; pasif–Spellblade/crit sırası |
| Twitch | Patch/veri çelişkisi; E global metadata ve hedef eligibility; W AS-dependent cast candidate |
| Ashe | Q oklarında on-hit/Hexoptics split; Frost ilk hit farkı; Volley mana kaynağıyla kullanıcı referansı çelişiyor (kullanıcı değerleri korundu) |
| Miss Fortune | Love Tap level/crit progression; eligible on-hit |
| Kalista | Hop speed/distance/boots ve kite geometrisi; Q/E range |
| Vayne | Tumble süresi/endpoint; passive/on-hit classification |
| Draven | Axe catch gerçek timing; axe crit scope |
| Tristana | W trajectory; E/R hedef menzili; R damage tag |
| Ezreal | Skill on-hit Phantom/stack kapsamı; Q/W detonation ve item eligibility |
| Sivir | Q 1450/1200 gidiş/dönüş WR doğrulaması; Morale cap/expiry |

## Ortak kaynak / oyun doğrulaması

- [ ] PC'den yetkilendirilmiş 23 AA base windup/projectile ve skill timing proxy'lerinin WR karşılığı. Veriler eksik değil; parity doğrulaması eksik.
- [ ] Hitbox, edge/center distance, MS soft cap ve dash bitiş geometrisi.
- [ ] AD/crit buff snapshot'ı launch'ta mı impact'te mi? Item/rün stack grant ve expiry'nin aynı timestamp sırası.
- [ ] Level growth eğrisi: Samira itemsiz level1/5/9/15 AD/AS/mana/HP/armor/MR; mevcut referansları değiştirmeden kontrol.
- [ ] Manamune/Muramana %15 mana iadesi: skill tüketimi ile regen'i ayırarak kontrol.
- [ ] Desteklenmeyen offensive keystone/rünler için kaynaklı proc/cooldown kuralları (First Strike vb.).
- [ ] Bilinmeyen WR ability/property/item tag'leri: PC sözlüğü kaynak sınıflandırmasının yerine geçmez. Registry'deki unknown alanlar açık kalır.

## Ölçüm istemediğimiz kullanıcı kilitleri

- RFC/Stormrazor/Statikk periyodik ve Yun Tal crit varsayımları korunur. Energized dolum katsayısı veya Yun Tal varsayımını yeniden ölçme zorunluluğu yoktur; daha kesin charge modeli kullanıcı ileride isterse ayrı kapsam olur.
- PD stack süresi 6s; sürekli vuruşta yeniden test istenmez.
- Youmuu combat dışı momentum model dışıdır.
- Tek Spellblade satın alma; Galeforce 325 dash / 600 hit range / 50s; Duskblade ilk AA / 10s kullanıcı kuralları uygulanır.
- Samira R manasız ve S Style gerektirir; R melee pasif almaz. Mana bedelleri tekrar sorulmaz.
- Rakibin saldırması, kendi ölümümüz ve lifesteal ile hayatta kalma model kapsamı değildir.

## Offline kapanan işler

- [x] 23 adapter ve timing bağlantısı; mana/cast/AA lock akışı.
- [x] Jhin/Jinx launch resource ve in-flight kimlik düzeltmeleri.
- [x] Kaynaklı WR skill range'lerinin runtime kullanımı; scalar range AA fallback'e düşmez.
- [x] Sivir Q endpoint/return travel; sabit .25s tahmin kaldırıldı.
- [x] Muramana hedef/rün çarpanı ve ayrı Item damage component kaydı.
- [x] Finalist policy taraması tam Cartesian product: rotation × movement × ultimate timing × AA weaving; E/weapon/feather varyantları.
- [x] Kaynak araştırması, etiket/integrity denetimi, sınır testleri, bounded optimizer ve sıralama duyarlılığı analizi. Sonuç raporu birebir WR kanıtı değildir.

## Oyun içi teyitler — 2026-10-01

- Kullanıcının oyun içi item açıklaması: AA Shock %1,5 maksimum mana; ability Shock melee/ranged %3,5/%3 maksimum mana. Aynı şampiyona saldırı veya ability cast başına yalnızca bir kez.
- Samira R: kullanıcı ilk tick'te Shock, sonraki tick'lerde Shock olmadığını test etti.
- Samira W: kullanıcı iki vuruşta toplam yalnızca bir Shock tetiklendiğini test etti.
- Ezreal: level 15, Q rank 4, full Conqueror dahil 239 AD, 0 AP, 2276 maksimum mana, yalnızca Muramana. Kukla 10.000 HP, 100 armor, 100 MR. Q ölçümü 259 fiziksel hasar. Kullanıcının bağımsız teyidi: Brutal her vuruşta 6 net hasar.
- Ezreal hesap: (115 + 1,35 × 239 + 0,03 × 2276) / 2 + 6 = 258,965. Skill Shock tek başına ölçümle uyumlu; ayrıca AA Shock eklenmesi ölçümle uyuşmuyor.
- Sınır: bu ölçüm Brutal'ın genel AD scaling formülünü teyit etmez. Cut Down'ın bu denemedeki aktifliği/hedefin vuruş öncesi canı kaydedilmedi; bu yüzden genel rün etkileşimi doğrulanmış sayılmıyor. Başka champion/cast etkileşimleri bu üç testten otomatik teyit almıyor.

## Hexoptics oyun içi teyidi — 2026-10-02

Ezreal15, AD178/AP0, crit25%/crit damage200%. Conqueror/Brutal/Cut Down/Legend Bloodline/Bone Plating. Tek Hexoptics ile yakın/uzak AA102/109 fiziksel, Q1 148/159 fiziksel. Wits End eklenince aynı fiziksel sayılar korunuyor; AA ve Q'da iki mesafede de22 büyü hasarı ekleniyor. AS0.99→1.30. Farklı aktif rune/buff olmadığı kullanıcı tarafından bildirildi. Numeric mesafeler ve başlangıç Conqueror stack sayısı kaydedilmedi. Katsayılar bu ölçümden değiştirilmez; kaynak veri [hexoptics-ezreal-user-test-20261002.json](../data/hexoptics-ezreal-user-test-20261002.json).

- 2026-10-02: Terminus standalone and all three Rageblade/Kraken/Terminus AA combinations recorded. Phantom counter advancement confirmed. Exact Kraken within-hit missing-health snapshot / split indicator rounding remains open (triple AA6 249 calculated vs250 displayed).
