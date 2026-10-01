# Item tetikleme taraması — V5.60.1

Taranan kapsam: 36 completed item, 14 boot ve 23 component. Bu rapor mevcut kod davranışını anlatır; oyundaki doğrulanmamış koşulları doğru kabul etmez.

## Düzeltilen Spellblade davranışı

Essence Reaver, Trinity Force, Iceborn Gauntlet ve Sheen artık cooldown bitince kendiliğinden yeniden hazırlanmaz. Gerçek başarılı skill cast zamanları item kerneline taşınır. Bir cast bir sonraki uygun on-hit’i hazırlayabilir; skillin kendisi damage proc’u değildir. 1.5s internal cooldown korunur. Cooldown içindeki cast daha sonra cooldown bitince sıraya alınmaz. Legacy Spellblade ready seçeneği yalnızca tek başlangıç cast’i temsil eder. Proc buff süresi ve çoklu Spellblade unique kuralı doğrulanmamış kaldı.

## Birlikte incelenecek bulgular

| Item | Kodda gözlenen davranış / eksik koşul |
|---|---|
| Rapid Firecannon | AA hesabında 7-hit cadence varsayımı; fight engine gerçek hareketten Energized doldurmuyor, başlangıç proc’u dışında recharge yok. Ek menzil hareket planına dahil değil. |
| Stormrazor | AA hesabında 7-hit cadence varsayımı; fight içinde Energized recharge ve proc sonrası hareket hızı modellenmiyor. |
| Statikk Shiv | AA hesabında 5-hit cadence varsayımı; fight içinde Energized recharge yok; tek hedefte bounce değeri hariç. |
| Duskblade of Draktharr | Koşul kontrolü yerine ilk kernel hitinde otomatik hasar. Görünürlük/combat eligibility doğrulanmıyor; kayıttaki 10s cooldown ve reset tekrar uygulanmıyor. |
| Galeforce | Aktif skill komutu yok: tier aramasında baştan hazır, sonraki uygun AA ile otomatik çalışır; 50s sonra yine AA ile kullanılır. Dash ve ayrı cast zamanı yok. |
| Yun Tal Wildarrows | Başlangıç kalıcı stack’i hero leveldan otomatik 0–125 atanıyor, gerçek maç geçmişi yok. Flurry ilk uygun AA ve cooldown ile hazırlanır; tetik şartı referansla yeniden incelenmeli. |
| Fiendhunter Bolts | Fight engine gerçek R cast’ine bağlı. Eski AA/Item Value hesabında Ultimate pre-cast seçeneği R atmadan buff verebilir. |
| Immortal Treads | Kerneldaki +5% damage her zaman uygulanır. Build Lab kendi HP seçeneğiyle düzeltir; tier benchmark kendi HP >50% varsayar. |
| Essence Reaver | Düzeltildi: skill cast geçmişiyle hazırlanır, sonraki eligible on-hit tüketir, 1.5s iç cooldown. Spellblade itemları aynı buildde hâlâ birlikte hasar ekleyebilir; unique proc seçimi ve buff süresi doğrulanmalı. |
| Trinity Force | Düzeltildi: skill cast geçmişiyle hazırlanır; shared cooldown. Başka Spellblade ile birlikte stacklenme ve buff süresi açık. |
| Iceborn Gauntlet | Düzeltildi: skill cast geçmişiyle hazırlanır; başka Spellblade ile birlikte stacklenme ve buff süresi açık. Slow yok. |
| Muramana | Mana statik max mana hesabından geliyor; on-hit/mana-consumption/skill eligibility sırası ve anlık mana scaling referansı ayrıca doğrulanmalı. |
| Guinsoo's Rageblade | Stack doğal eligible hitlerle artıyor; skill-on-hit callback’lerinin stack ve Phantom Hit sayımına uygunluğu tüm şampiyonlar için doğrulanmamış. |
| Terminus | Light/Dark alternasyonu kernel çağrı sayısına bağlı; eligible skill hitleri de sayacı etkiliyor. Skill eligibility/alternasyon sırası doğrulanmalı. |
| Kraken Slayer | Sayaç eligible kernel hitleriyle artıyor; skill-on-hit/Phantom Hit eligibility doğrulanmalı. |
| Phantom Dancer | Doğal AA stack’i; stack expiry/refresh buff süresi kernelde yok, fight boyunca stack kalır. |
| Hexoptics C44 | Fight içinde gerçek mesafe kullanılır; eski AA hesaplayıcısında sabit distance varsayımı vardır. Kernel AA physical/true arttırır; ability ve diğer damage kapsamı doğrulanmalı. |
| Lord Dominik's Regards | Hedef bonus HP manuel/profil farkından hesaplanır; anlık buff yok. Tek hedef profili dışındaki health growth belirsizlikleri sonucu etkiler. |
| The Collector | Önceki execute sayısı kullanıcı/progression state’i; hedef ölümü sırasında eşik kontrolü gerçek HP’ye bağlı. Maç geçmişi otomatik simüle edilmez. |
| Manamune | Seçilmiş itemin flat mana ve Awe’su doğrudan uygulanır; Tear yüklenme geçmişi ayrı hesaplanmıyor. |
| Youmuu's Ghostblade | Statik MS ve statlar var; hareket stack’i/aktif ve combat durumuyla buff değişimi yok. |

## Bütün kayıtların kapsamı

| Tür | Item | Bulgu |
|---|---|---|
| completed | Fiendhunter Bolts | Fight engine gerçek R cast’ine bağlı. Eski AA/Item Value hesabında Ultimate pre-cast seçeneği R atmadan buff verebilir. |
| completed | Rapid Firecannon | AA hesabında 7-hit cadence varsayımı; fight engine gerçek hareketten Energized doldurmuyor, başlangıç proc’u dışında recharge yok. Ek menzil hareket planına dahil değil. |
| completed | Runaan's Hurricane | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Extra bolts excluded in single-target ranking. |
| completed | Phantom Dancer | Doğal AA stack’i; stack expiry/refresh buff süresi kernelde yok, fight boyunca stack kalır. |
| completed | Navori Quickblades | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Deft Strikes: each AA reduces remaining basic-ability cooldowns by 15%; effect activates when ability timeline is added. |
| completed | Wit's End | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Magic on-hit each attack. |
| completed | Hexoptics C44 | Fight içinde gerçek mesafe kullanılır; eski AA hesaplayıcısında sabit distance varsayımı vardır. Kernel AA physical/true arttırır; ability ve diğer damage kapsamı doğrulanmalı. |
| completed | Kraken Slayer | Sayaç eligible kernel hitleriyle artıyor; skill-on-hit/Phantom Hit eligibility doğrulanmalı. |
| completed | Nashor's Tooth | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Magic on-hit. |
| completed | Manamune | Seçilmiş itemin flat mana ve Awe’su doğrudan uygulanır; Tear yüklenme geçmişi ayrı hesaplanmıyor. |
| completed | Muramana | Mana statik max mana hesabından geliyor; on-hit/mana-consumption/skill eligibility sırası ve anlık mana scaling referansı ayrıca doğrulanmalı. |
| completed | Statikk Shiv | AA hesabında 5-hit cadence varsayımı; fight içinde Energized recharge yok; tek hedefte bounce değeri hariç. |
| completed | Guinsoo's Rageblade | Stack doğal eligible hitlerle artıyor; skill-on-hit callback’lerinin stack ve Phantom Hit sayımına uygunluğu tüm şampiyonlar için doğrulanmamış. |
| completed | Mortal Reminder | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Percent armor penetration. |
| completed | Maw of Malmortius | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Shield/survival excluded. |
| completed | Essence Reaver | Düzeltildi: skill cast geçmişiyle hazırlanır, sonraki eligible on-hit tüketir, 1.5s iç cooldown. Spellblade itemları aynı buildde hâlâ birlikte hasar ekleyebilir; unique proc seçimi ve buff süresi doğrulanmalı. |
| completed | Immortal Shieldbow | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Shield/survival excluded. |
| completed | The Collector | Önceki execute sayısı kullanıcı/progression state’i; hedef ölümü sırasında eşik kontrolü gerçek HP’ye bağlı. Maç geçmişi otomatik simüle edilmez. |
| completed | Terminus | Light/Dark alternasyonu kernel çağrı sayısına bağlı; eligible skill hitleri de sayacı etkiliyor. Skill eligibility/alternasyon sırası doğrulanmalı. |
| completed | Stormrazor | AA hesabında 7-hit cadence varsayımı; fight içinde Energized recharge ve proc sonrası hareket hızı modellenmiyor. |
| completed | Yun Tal Wildarrows | Başlangıç kalıcı stack’i hero leveldan otomatik 0–125 atanıyor, gerçek maç geçmişi yok. Flurry ilk uygun AA ve cooldown ile hazırlanır; tetik şartı referansla yeniden incelenmeli. |
| completed | Galeforce | Aktif skill komutu yok: tier aramasında baştan hazır, sonraki uygun AA ile otomatik çalışır; 50s sonra yine AA ile kullanılır. Dash ve ayrı cast zamanı yok. |
| completed | Mercurial Scimitar | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Cleanse/active excluded. |
| completed | Blade of the Ruined King | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Current-HP on-hit recalculated each attack. |
| completed | Guardian Angel | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Revive excluded. |
| completed | Bloodthirster | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Sustain is not scored as DPS. |
| completed | Lord Dominik's Regards | Hedef bonus HP manuel/profil farkından hesaplanır; anlık buff yok. Tek hedef profili dışındaki health growth belirsizlikleri sonucu etkiler. |
| completed | Trinity Force | Düzeltildi: skill cast geçmişiyle hazırlanır; shared cooldown. Başka Spellblade ile birlikte stacklenme ve buff süresi açık. |
| completed | Infinity Edge | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Critical damage modifier. |
| completed | Serylda's Grudge | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Penetration modeled; slow excluded. |
| completed | Serpent's Fang | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Needs target shield state. |
| completed | Youmuu's Ghostblade | Statik MS ve statlar var; hareket stack’i/aktif ve combat durumuyla buff değişimi yok. |
| completed | Duskblade of Draktharr | Koşul kontrolü yerine ilk kernel hitinde otomatik hasar. Görünürlük/combat eligibility doğrulanmıyor; kayıttaki 10s cooldown ve reset tekrar uygulanmıyor. |
| completed | Edge of Night | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Spell shield excluded. |
| completed | Iceborn Gauntlet | Düzeltildi: skill cast geçmişiyle hazırlanır; başka Spellblade ile birlikte stacklenme ve buff süresi açık. Slow yok. |
| completed | Death's Dance | Statik stat veya doğal on-hit/crit/defense-only kapsamı; yeni bir zorunlu-proc default’u tespit edilmedi. Mevcut kapsam: Damage delay/survival excluded. |
| boot | Gluttonous Greaves | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Immortal Treads | Kerneldaki +5% damage her zaman uygulanır. Build Lab kendi HP seçeneğiyle düzeltir; tier benchmark kendi HP >50% varsayar. |
| boot | Ionian Boots of Lucidity | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Crimson Lucidity | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Berserker's Greaves | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Gunmetal Greaves | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Mercury's Treads | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Chainlaced Crushers | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Plated Steelcaps | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Armored Advance | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Boots of Mana | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Spellslinger's Shoes | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Boots of Dynamism | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| boot | Armorcrusher Boots | Statik boot stats/MS; shield/defense/utility gelen hasar olmadığı için DPSye eklenmez. |
| component | Pickaxe | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Sheen | Tek initial pre-cast ya da gerçek cast; cooldown otomatik rearm kaldırıldı. |
| component | Kircheis Shard | Başlangıç Energized checkbox’ı; gerçek hareket recharge yok. |
| component | Executioner's Calling | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Recurve Bow | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Quicksilver Sash | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Hearthbound Axe | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Vampiric Scepter | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Last Whisper | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Caulfield's Warhammer | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Noonquiver | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Zeal | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | B.F. Sword | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Tear of the Goddess | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Dagger | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Long Sword | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Brawler's Gloves | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Cloth Armor | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Null-Magic Mantle | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Ruby Crystal | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Amplifying Tome | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Ring of Revelation | Statik stats; Recurve Bow doğal eligible on-hit. |
| component | Boots of Speed | Statik stats; Recurve Bow doğal eligible on-hit. |

Öncelik önerisi: Energized hareket/AA recharge → Duskblade eligibility → Galeforce gerçek action → Yun Tal başlangıç/tetik koşulları → çoklu Spellblade unique davranışı → skill-on-hit item stack eligibility. Bunlar bu güncellemede değiştirilmedi; sadece Spellblade otomatik rearm hatası düzeltildi.

Doğrulama: 131/131 otomatik test geçti (86.490 saniye). Yeni testler initial pre-cast tek proc, gerçek cast ile rearm, cooldown içindeki cast’in sıraya alınmaması ve geciken AA için gerçek cast timestamp kontrolünü kapsıyor.

## V5.60.2 corrections and user locks

- RFC, Stormrazor and Statikk current measured values are user-locked and removed from the proposed replacement queue.
- Duskblade first AA and next AA after 10s proc. Visibility is not required; earlier audit wording was incorrect. Skill-on-hit callbacks do not consume the AA trigger.
- Galeforce is a separate fight event with its own 50s cooldown. It waits until current AA windup, cast or channel finishes; does not alter the AA clock or grant ability/AA stacks. Dash path/range and cast restrictions remain unverified. The AA-only legacy simulator has no active action timeline and retains its explicit scenario active flag.
- Yun Tal unchanged: level-derived initial permanent stacks, first eligible AA Flurry, 6s AS buff, 25s cooldown and AA/expected-crit cooldown reductions remain the two review subjects (initial progression and Flurry trigger rules).

## User confirmation — Yun Tal

Yun Tal existing starting crit/stack approximation is based on user in-game AA measurements and approved. Preserve current behavior; remove Yun Tal from the review queue. RFC, Stormrazor and Statikk remain approved as well.

## V5.60.3 user rules

PD/Youmuu closed as approved scope. Spellblade highest percentage coefficient only. Fiendhunter actual R only. Galeforce 325 max dash and 600 target radius implemented. I01 Rageblade/Kraken/Terminus and I02 Hexoptics are in-game TODO. Muramana uses recorded champion mana/growth/regen and skill spending/refund; 7.3 removed Shock drain, so max-mana damage remains correct.
