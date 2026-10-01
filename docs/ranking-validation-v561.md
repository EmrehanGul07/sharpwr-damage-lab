# V5.61.0 — Build araması ve formül doğrulama raporu

İşlem sırası: aday aramasını genişletme → finalistlerin rotasyon/hareket doğrulaması → eksik formüllerin kaynaklı uygulaması. Son benchmarklar tamamlanmış formüllerle tekrar çalıştırıldı.

- 3–5 item aşamalarında 40 yerine 80 aday tutuluyor; AP, crit, on-hit, penetration, saf ve hibrit profiller için yer ayrılıyor.
- Bütün legal tekli/ikili kombinasyonlar taranıyor; erken aşama adaylarına altı temel skill sırası deneniyor.
- Tam build aşamasında bütün 7 Tier 3 bot deneniyor; 20 yerine 40 finalist daha derin hesaplanıyor.
- Final kontrol: altı skill önceliği, E açık/kapalı, AA weaving/skill-first, ulti önce/sonra, hazır skill menzili/AA menzili/yakın menzil. Hareket seçenekleri varsayılan skill sırasıyla; tüm altı sıra varsayılan hareketle karşılaştırılıyor. Samira melee yaklaşımını koruyor; Xayah ayrıca 1/3/5 tüyde E kullanmayı karşılaştırıyor.
- İlk bölümde full-build Top3, aşağıda 1–4 item Top10 kalıyor; kazanan skill ve hareket tercihleri tabloda gösteriliyor.

## Tam havuz benchmarkı

Level15; Ornn hedefi: 5698 HP, 415 armor, 184 MR, %10 AA azaltma. Hedef hasar vermiyor; beklenen crit hasarı kullanılıyor. Bu iki benchmark belirli bir test senaryosudur, tüm hedefler için aynı build önerisi değildir.

| Şampiyon | Fight sayısı | Item havuzu | Full build + bot adayı | Derin finalist | Süre |
|---|---:|---:|---:|---:|---:|
| Jhin | 19,260 | 36 | 560 | 40 | 155.21 s |
| Xayah | 25,516 | 36 | 560 | 40 | 270.37 s |

### Jhin — doğrulanan Top3

| Sıra | Build + bot | TTK | İlk tarama TTK | Hareket / rotasyon |
|---|---|---:|---:|---|
| 1 | Hexoptics C44 + Infinity Edge + Lord Dominik's Regards + Muramana + The Collector + Armorcrusher Boots | 5.406 s | 6.598 s | E → Q → W; skill_envelope; after_basics; aa_weave |
| 2 | Blade of the Ruined King + Hexoptics C44 + Infinity Edge + Lord Dominik's Regards + The Collector + Armorcrusher Boots | 5.406 s | 6.483 s | E → Q → W; skill_envelope; after_basics; aa_weave |
| 3 | Blade of the Ruined King + Galeforce + Infinity Edge + Lord Dominik's Regards + The Collector + Armorcrusher Boots | 5.406 s | 6.483 s | E → Q → W; skill_envelope; after_basics; aa_weave |

### Xayah — doğrulanan Top3

| Sıra | Build + bot | TTK | İlk tarama TTK | Hareket / rotasyon |
|---|---|---:|---:|---|
| 1 | Hexoptics C44 + Infinity Edge + Lord Dominik's Regards + Navori Quickblades + Yun Tal Wildarrows + Armorcrusher Boots | 7.157 s | 8.335 s | W → Q → E; skill_envelope; immediate; aa_weave; E≥1 tüy |
| 2 | Infinity Edge + Lord Dominik's Regards + Navori Quickblades + The Collector + Yun Tal Wildarrows + Armorcrusher Boots | 7.157 s | 8.335 s | W → Q → E; skill_envelope; immediate; aa_weave; E≥1 tüy |
| 3 | Essence Reaver + Infinity Edge + Lord Dominik's Regards + Navori Quickblades + Yun Tal Wildarrows + Armorcrusher Boots | 7.593 s | 8.262 s | W → Q → E; skill_envelope; immediate; aa_weave; E≥1 tüy |

## Kapatılan formüller

- Jhin: WR7.3 AD dönüşümü, dinamik item AS/crit ve AD ile bir kez uygulanıyor. AS itemi saldırı hızını yükseltmiyor; sabit AA hızı ve reload korunuyor. Dördüncü AA eksik can oranı WR template dizisindeki level1 %11 → level15 %25 olarak tamamlandı.
- Xayah: E çoklu tüy hasarı %100, %90, %80… ve en az %10 şeklinde toplanıyor. Kullanıcının tüy başına hasar/bonus AD/crit oranları korundu. Q iki tüy ve iki hasar sayıyor; pasif saldırı yükleri 7.5s sonunda siliniyor; yerdeki tüyler 6s kalıyor; manuel E tek tüy ile kullanılabiliyor.
- Varus: raw component Q rank2–4 oranları mevcut fight engine ile eşlendi. Rank1 oyun içi bonus-AD referansı korundu; wiki total-AD ifadesiyle çatışma kapatılmış sayılmadı.
- Kaynak ve formül kayıtları: [verified-ranking-formulas.json](../data/verified-ranking-formulas.json).

## Kontroller ve gerçek sınırlar

- Tam suite: 149 test geçti. Son Varus component güncellemesi sonrası 14 catalogue ve 7 refinement kontrolü tekrar geçti; son UI düzenlemesi sonrası Top3/Top10 sıralaması ve cache testleri geçti.
- Jhin ve Xayah Top3 sonuçları ilk taramadan daha kötü TTK vermiyor; tam havuz çıktıları [ranking-validation-v561.json](../data/ranking-validation-v561.json) dosyasında.
- Sonuçlar denenen adayların en iyisidir; beam araması ve sınırlı politika grid’i global optimum kanıtı değildir.
- Xayah benchmarkı sabit hedef ve aynı hat üzerindeki radial hareket kullanıyor. Sağ-sol hareketin gerçek tüy çarpışma geometrisi, R fanı/dash uçları ve bilinmeyen AA windup/projectile ayrıntıları hâlâ oyun içi doğrulama gerektiriyor.
- Varus Q bonus/total AD kapsamı, Yunara eksik core statları, Senna mist kazanımı ve kalan şampiyon mekanikleri [TODO](ingame-test-todo.md) / [şampiyon kuyruğu](marksman-task-queue.md) içinde duruyor.
- Rageblade/Kraken/Terminus ve Hexoptics oyun içi testleri TODO olarak korundu. RFC/Stormrazor/Statikk ve YunTal için kullanıcı onaylı yaklaşık değerler değiştirilmedi. Dolayısıyla bu itemleri içeren Top3, ilgili doğrulanmamış item mekaniklerinin sınırlarını taşır.
