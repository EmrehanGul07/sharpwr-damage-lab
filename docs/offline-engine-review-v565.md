# Offline engine review — V5.65.0

Altı çalışma paketi: kaynak tamamlama, TODO temizliği, damage classification/işlem sırası denetimi, sınır testleri, sıralama duyarlılığı ve optimizer kapsamı.

## Engine ve kaynak düzeltmeleri

- 88 WR active ability template raw kaydı yeniden alındı; hiçbir kullanıcı damage/mana/cooldown/rank katsayısı değiştirilmedi. Kaynaklar data/offline-source-research-v565.json içinde. Yeni basit numeric alan yok; var olan scalar WR range kayıtlarının runtime'a bağlanmaması düzeltildi.
- Kog'Maw Q/E, Xayah Q/R, Lucian W, Caitlyn Q/E, Jinx W, Zeri Q artık kayıtlı WR damage reach kullanır. Targeted skill range ile beam/dash mesafesi birbirine karıştırılmaz. Global ve attack-range ifadeleri ayrıca ele alınır.
- Self-buff skillerine bağımsız projectile tahmini uygulanmaz; passive on-hit damage AA yolunda kalır.
- Ashe W mana kaynak çelişkisi: kullanıcı 65/60/55/50, yeniden alınan wiki 50/50/50/50. Kullanıcı değeri korundu; conflict manifest ve TODO'da.
- Finalist refinement tam rotation × movement × ultimate timing × attack weaving çapraz çarpımına geçti. Generic 72 policy × E açık/kapalı =144 fight/build; Jinx weapon ile288; Xayah recall threshold ile432; Samira approach-only 24 policy ×2=48. Önce generic varsayılan priority dışındaki sıralar yalnız tek movement ile deneniyordu.
- Aday havuzu duplicate item isimlerini temizler. Üretim search hâlâ bounded diverse beam'dir; global optimum iddiası yok. Mevcut üretim havuzu36 supported itemdir; AP verenler yalnız Nashor, Statikk ve Rageblade'dir. Bütün WR AP itemleri destekleniyor iddiası yok; yeni item için kaynaklı stat/proc adapter gerekir. Bootlar full-build aşamasında karşılaştırılır; 1–4 item tabloları bootsuzdur.
- Muramana skill Shock ayrı physical Item component olarak loglanır; BasicAttack etiketi almaz. İlk cast hit üretim kuralı aynen korunur.
- NaN/Infinity spatial/resource verileri, fractional/bool skill ranks ve geçersiz windup scale reddedilir.

## Etiket ve işlem sırası denetimi

115 ability slot,73 item,51 rün ve stat alanları registry'de mevcut. 77 ability WR classification,25 no-direct-damage,12 unknown-WR ve1 mixed-component kaydı var. Item origin/trigger tags mevcut; 73 item için ayrıntılı WR basic/proc classification hâlâ bilinmeyen olarak saklanır. “On-hit tarafından tetiklenir” olmak “basic damage verir” demek değildir. Eksik property/tag verisi PC'den kesin WR kuralına çevrilmedi.

Başarılı komut önce lock/range/mana kontrolü yapar; mana/ammo/identity tüketilir, cast tetikleyicileri hazırlanır. AA windup sonrası flight ile impact gelir. Hasar/execute ardından stack kazancı uygulanır. Eşit timestamp olayları heap insertion sırasıyla çözülür. Hedef ölünce kalan damage kuyruğu uygulanmaz. Launch/impact stat snapshot ve bazı aynı-zaman expiry kuralları WR testi bekler.

Components için finite/nonnegative raw damage, geçerli tag ve Shock origin denetimleri fight matrisine eklendi. Bilinmeyen tag'in sırf test geçsin diye doldurulması yapılmadı.

## Otomatik test sonuçları

176 test geçti. Güncel engine için3312 vaka/6912 fight kontrolü sıfır hatayla tamamlandı; level1 ve15,23 champion ve3 target,36 tekli item ve altı profil denetlendi. Test sonucu engine integrity kanıtıdır; WR gameplay parity kanıtı değildir. Self-buff uyarılarının temizlenmesinden sonra runtime uyarı toplamı96; bunların bazıları yetkilendirilmiş proxy bilgisidir, hepsi eksik hasar formülü değildir.

## Ölçüm gerektirenlerin durumu

Aktif liste [ingame-test-todo.md](ingame-test-todo.md). Önceki adapter/timing yok açıklamaları ve kullanıcı kilidi olan itemlere gereksiz yeniden ölçüm talepleri kaldırıldı. Dash geometry, snapshot, multihit eligibility, Yunara stats ve provisional champion scaling açıkları korunuyor.

## Duyarlılık ve optimizer kapsamı

Sonuçlar data/offline-rankings-v565.json içinde. Bu kayıt üretim build cache'i veya full-pool build önerisi değildir. Altı build profili; level15,23 champion,3 target. ±20% AA windup, Muramana every-hit ve Hexoptics skill-scope-off varsayımları yalnız analiz içindir. Hexoptics skill-scope-off kernel'in basic-AA magnification'ını kapatmaz. Yunara için iki örnek mana/MS/range endpoint kullanılır; bunlar kaynak veya güven aralığı değildir.

Optimizer altı itemlik küçük havuzda her legal stage subset'ine karşı denetlenir. Dört temsilci champion'un squishy hücresinde bütün full-build finalistleri deep policy ile ayrıca karşılaştırılır. Küçük havuz sonucu36 itemlik üretim havuzunun exhaustive olduğunu göstermez.

## Yeniden üretim

```bash
python scripts/research_offline_sources.py
python -m unittest discover -s tests
python scripts/audit_combat_matrix.py
python scripts/audit_offline_rankings.py
```

Üretim katsayıları korunmuştur. Oyun içi parity ve gerçek full-pool global optimum, bu offline raporun kanıtladığı şeyler değildir.

## Tamamlanan sıralama analizi

282 duyarlılık hücresi ve69 optimizer hücresi tamamlandı. Küçük havuzdaki6/15/20/15/6 legal stage adaylarının tamamı her optimizer hücresinde görüldü; kontrol hatası0. Dört deep-oracle hücresinde (Ezreal/Xayah/Jhin/Samira vs squishy) bütün altı full-build derin tarandı ve bounded finalist aramasıyla aynı kazanan bulundu. Bu,36 itemlik havuz için global optimum kanıtı değildir.

| Varsayım | Hücre | İlk3 sıra değişti | Kazanan değişti |
|---|---:|---:|---:|
| hexoptics_skill_scope_off | 69 | 1 | 0 |
| hypothetical_mana1000_ms300_range550 | 3 | 3 | 2 |
| hypothetical_mana2000_ms400_range650 | 3 | 3 | 2 |
| muramana_every_hit | 69 | 1 | 0 |
| windup_minus20 | 69 | 5 | 1 |
| windup_plus20 | 69 | 7 | 2 |

Duyarlılık tablosu yalnız altı örnek profilin sırasıdır; production pool search sonuçlarının tümü değildir. ±20% windup ve every-hit Muramana gerçek WR değerleri olarak kaydedilmedi. Yunara endpoint'leri mana/MS/range'i birlikte değiştirir; tek bir değişkenin etkisini izole etmez. Her iki örnek endpoint'te3 hedefin tamamında ilk3 sıra değişti ve2 hedefte kazanan değişti. Yunara için eksik statları kapatmadan sıralamaya güvenilmemeli. Windup bazı senaryolarda kazananı değiştiriyor; PC proxy parity önemli. Muramana/Hexoptics stres testlerinde bu profil setinde kazanan değişmedi ama birer hücrede ilk3 sırası değişti; oyun doğrulaması gereksiz demek değildir.

Analiz toplam sayacı146088 fight çağrısıdır. İlk uzun taramanın ek deep-oracle counter eksikliği, cache dışı3 build × (144+432+144+48) =2304 çağrıyla tamamlandı; dosyada ilk sayaç ve ek oracle sayısı ayrı korunur. Yeniden üretim script'i sayacı oracle çalışmaları sonrasında toplar.

Öncelik: Yunara core statları → windup/proxy parity için erişilebilir kaynak → item trio/Hexoptics/Muramana kapsamı → provisional champion scaling. Mevcut oyun içi ölçüm protokolü korunur; video zorunlu değildir.
