# Offline tamamlanan işler — V5.87.1 / 3 Ekim 2026

Bu çalışma yalnız dosyadaki `TODO` kelimelerini saymadı: canlı UI → stat → item kernel → 23 fight adapter → build search → kayıtlı sonuç → catalogue üretimi → test ve dokümantasyon bağlantılarını taradı. Mevcut kaynaklarla uygulanabilen yazılım işlerini kapattı. Yeni WR katsayısı, damage tag veya timing uydurulmadı. Proje hâlâ WR araştırma modelidir; birebir WR motoru değildir.

## Kapatılan işler

| ID | İş | Sonuç / doğrulama |
|---|---|---|
| O01 | Skill Lab persistent rune statları | Zombie Ward, Eyeball, Hubris, Absolute Focus ve Gathering Storm AD; Alacrity AS; Haste/Transcendence AH aynı ayarlardan replay'e aktarılır. |
| O02 | Manaflow ve mana override | +300 mana Skill Lab/AA hesap/Awe/Shock'a gider. Sıfır input kayıtlı champion mana kullanır; pozitif manual override iki hesapta da geçerlidir. |
| O03 | Full own stats | Overgrowth tüm champion HP'ye; Unshakeable champion + item armor/MR'a uygulanır. Bilinmeyen base stat sıfıra çevrilmez. |
| O04 | Grasp own HP | Legacy AA hesabı hedef HP veya yalnız item HP yerine kendi tam max HP'sini kullanır; ranged +4 kalıcı HP kaydı. Incoming damage/healing fight'i kapsam dışı. |
| O05 | Başlangıç Yun Tal | Kullanıcının başlangıç crit ve Flurry seçimi item kernel/fight/display'e aktarılır; yanlış başlangıç sıfırlaması kaldırıldı. |
| O06 | Başlangıç Spellblade | “Hazır” seçimi event-driven replay ilk attack'ına kadar korunur. Live armed-window/expiry kuralı bu yazılım düzeltmesiyle doğrulanmış sayılmaz. |
| O07 | Energized launch | Replay'e item eligibility flag'i aktarılır; launch rezervasyonu ve impact hasarı ayrılır. Launch callback'i olmayan bonus stat/damage alanlarına erişmez. |
| O08 | First Strike | İlk gerçek damaging impact'ten başlayan hazır 3s pencere, %7 ayrı true damage component. Gold ve cooldown rearming açık. |
| O09 | Last Stand ve adaptive proclar | Mevcut AA Last Stand modeli ile Dark Harvest/Tyrant/Empowered Attack formül, threshold/CD kuralları fight yollarına bağlandı. ADC physical varsayımı açık yazılır; WR adaptive seçim/aynı-hit sırası kanıtı değildir. |
| O10 | Girdi ve build doğrulaması | NaN/inf, geçersiz HP/mana/level/rank, boolean level, illegal/duplicate item, bilinmeyen boots, negatif beam/refine, geri event zamanı reddedilir. Negatif resistance mevcut geçerli model olarak korunur. |
| O11 | Widget state | Rune/event ayarları, Yun Tal ve Immortal Treads seçimleri item/rune erken rerun'larında korunur. |
| O12 | Catalogue rebuild | Eski screenshot rebuild'i daha yeni kullanıcı teyitlerini, CD/mana, classification/provenance ve ek metadata alanlarını silmez. İzole rebuild testi eklendi. |
| O13 | Yunara CD metadata | Runtime'da zaten kullanılan Q resource gate/W/E/R cooldownları catalogue'a işlendi; yeni formül çıkarılmadı. |
| O14 | Yayınlı tier koruması | Public search/compare sentetik disabled-button click'inde bile çalışmaz. Yayınlı 36-item tier JSON ve HTML değiştirilmedi. |
| O15 | Güncel kuyruk ve assumptions | 23 champion remaining kaydı aktif kanıt TODO'sundan üretilir; eski “Yunara mana yok / timing yok” raporları güncel dosyalardan kaldırıldı. README güncellendi. |
| O17 | Canlı sürüm module cache | Core-item/consensus modülleri sürüm değişiminde yenilenir; stale module regression testi. |
| O16 | Yeniden üretilebilir audit/cache | Matrix yeni current dosyalarına yazılır ve failure'da nonzero exit verir. 414 core cell/1.242 retained finalist eski-yeni exact-policy replay ile doğrulandı; bounded search tekrar yapılmış gibi gösterilmedi. |

## Doğrulama

- Python suite: **252 test, 0 failure/error (82.559s)**; Streamlit state/starting-stat/public-freeze regresyonları dahil. Yapılandırılmış sonuç `data/offline-task-inventory.json` içinde.
- Combat integrity matrix: **3.312 senaryo, 6.912 fight, 0 failure**. Champion seviyeleri 1 ve 15; üç hedef; item başına ve altı build profili.
- Cache migration: **1.242 finalist** için baseline `6f31574` ve yeni motorun time/action/damage hit ledger, total damage, remaining HP ve TTK sonuçları birebir eşit. Her finalist mevcut kayıtla da karşılaştırıldı. 414 cell ve ranking değişmedi.
- JS replay state regresyonu ve Python compile/diff kontrolleri geçti.
- Public tier board asset/data byte-for-byte korundu; arama hâlâ kapalı.
- Canlı V5.87.1: core-item görünümü düzeldi; Kalista9 / 1.475 HP Squishy hedef replay 3.900s, 1.475 damage, 0 remaining HP; hata yok.

Komutlar README'de; baseline karşılaştırması `scripts/verify_core_rows.py BASELINE_REPO baseline.json` ve `scripts/verify_core_rows.py CANDIDATE_REPO candidate.json` ile yeniden üretilebilir. Sayısal `rows` alanları karşılaştırılır; `warnings` alanındaki metin değişiklikleri sayısal eşitlik değildir.

## Açık kalan işler ve nedenleri

Tam liste [ingame-test-todo.md](ingame-test-todo.md): **8 item/eligibility başlığı, 23 şampiyonun ayrı mekanik açıkları ve 7 ortak kaynak/parity başlığı**. Bunlar birer tek işlem değildir; alt konular ayrı tutulur. Şampiyon queue'su integration tamamlandı diye parity tamamlandı saymaz.

- WR AA/skill timing, collision/center-edge geometry, snapshot ve aynı timestamp işlem sırası: mevcut PC proxy veya yazılım testi WR kanıtı değildir.
- Item/passive/indirect ability eligibility ve unknown WR damage tags: kayıtlı ölçümler yalnız teyit ettikleri şampiyon/hit kapsamını kapatır.
- Rune catalogue tooltip'i tek başına tam event motoru değildir. Desteklenmeyen offensive loadout'lar bloklanır; proc arrival/return, trigger scope, cooldown reset ve state kuralları eksik olduğunda tahminle açılmaz. First Strike rearming/gold bu kapsamda açık kalır.
- Çelişkili progression, range, recharge ve mana kaynakları: kullanıcı kilitleri korunur; güvenilir yeni WR kaydı olmadan katsayı değiştirilmez.
- Incoming enemy attacks, own death/lifesteal survival, ally/turret/heal simülasyonu mevcut hedef kapsamı dışındadır.

Bu kalanlar için kullanıcıdan bugün yeni oyun içi test istenmedi. Sonradan güvenilir WR kaynak kaydı bulunursa ilgili açık yine offline kapatılabilir; mevcut dosyalarda bu kanıt yoktur.
