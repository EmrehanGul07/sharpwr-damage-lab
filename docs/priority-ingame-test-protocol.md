# Öncelikli üç oyun içi test — 1 Ekim 2026

Durum: **Hexoptics ve Smolder item AA kombinasyonları ölçüldü; açık kalan skill etkileşimleri aşağıdadır.** Sıra: Hexoptics → Rageblade/Kraken/Terminus → Xayah. Video veya ekran kaydı gerekmiyor; sayı ve tooltip metni yeterli. Önce kolay kontrol noktaları, yalnızca fark bulunursa ek ölçüm.

Bu testler yeni damage katsayısı atamaz. [Engine tahminleri](../data/priority-test-predictions.json) mevcut modelin hipotezleridir; doğrulanmış oyun sonuçları değildir. AD/HP/armor değişirse JSON'daki örnek hasarları birebir bekleme.

## Her ölçümde ortak kurulum

- Practice tool, sabit tek kukla. Mevcut referans: 10.000 HP, 100 armor, 100 MR. MR değiştirilemiyorsa değiştirmeye çalışma.
- Hero level15: beklerken level değişmesi sorunu olmasın. Skill ranklarını belirtilen şekilde ayarla. Ability dışında kalan puanların dağılımı zarar vermiyorsa önemli değil.
- Practice tool sabit rünle açılıyorsa aynı rünleri kullan. Sayfayı değiştirmeye çalışma. Başlangıçta isimleri bir kere yaz; özellikle Brutal, Cut Down, Battle Zeal, Conqueror/First Strike aktifliği önemli.
- Her item değişiminde ekrandaki **toplam AD/AP/AS, crit chance/damage** değerlerini yaz. Aynı build ile mesafe karşılaştırırken statlar değişmesin.
- Fiziksel ve büyü hasarını ayrı yaz: `31 physical + 4 magical`. Ekrandaki yuvarlamadan dolayı ±1 fark tek başına yanlış formül demek değildir.
- Kuklanın hasar öncesi HP'sini kaydet. Art arda AA testinde HP azalır; Kraken missing-HP bonusu ile Cut Down eşikleri bunu değiştirir. Engine örneklerinde HP her vuruş öncesi sabittir; gerçek kuklanın kendiliğinden tam kaldığını varsayma.
- Testler arasında item/champion stacklerini sıfırla ve kuklayı iyileştir. Reset düğmesi stackleri silmiyorsa şampiyonu değiştirip geri dön; level ve itemleri yeniden kontrol et. Her AA arasında reset yapma: sayaç testini bozar.
- Rune tetiklenmesi normaldir. Tooltip rün bonusu ve buff aktifliği kayıt altına alınır; hasar farkı hemen item formülüne bağlanmaz.

## 1. Hexoptics C44 — I02

### H01 — Tooltip ve AA yakın/uzak karşılaştırması

**Ezreal level15, yalnızca Hexoptics, Q rank1.** W/E/R kullanma. Önce itemin pasif açıklamasını yaz. Toplam AD, crit chance/damage ve rünleri kaydet.

1. Kuklaya olabildiğince yakınken tek **kritiksiz** AA ölç.
2. Aynı item/statlarla maksimum AA menzilinde tek **kritiksiz** AA ölç. Auto için karakterin kendiliğinden yaklaşıp durduğu sınır kullanılabilir.
3. Her iki deneme öncesi kuklanın HP'si ve rune durumu aynı olsun. Crit gelirse o sonucu ayrı işaretle; bir sonraki normal AA'yı önceki rune/item state'iyle karıştırma.

Mevcut model ana AA fiziksel hasarını mesafeye göre büyütür. 550 birimde +%10; 100'den yakınsa +%0. Yakın konumun gerçekten 100'den küçük olduğu bilinmiyorsa ratio'nun tam1.10 olmaması modeli otomatik çürütmez. Oyunda sayısal mesafe yoksa 99/100 gibi piksel ölçümleri istenmez.

| Model mesafesi | Mevcut bonus |
|---:|---:|
| <100 | %0 |
| 100–149 | %1 |
| 150–199 | %2 |
| 200–249 | %3 |
| 500–549 | %9 |
| ≥550 | %10 |

Kullanıcının aktardığı oyun içi tooltip (2026-10-02): “Deal 0-10% increased damage with attacks, based on how far the enemy is(max damage at 550 range.)” %10 cap ve550 maksimum mesafe teyitli. Kullanıcı aynı gün önceki oyun içi teyidini yeniden belirtti:100 mesafede %1, her50 birimde +%1, 550 mesafede %10. Runtime basamakları kullanıcı teyidiyle korunuyor; yalnız edge/center mesafe tanımı açık.

### H02 — Skill hasarına uygulanıyor mu?

Aynı Ezreal/build ile yakın ve maksimum AA mesafesinden Q rank1 vur. Maksimum Q menziline çıkmak gerekmiyor; AA testindeki iki konumu kullan. Her denemede tam HP ve aynı rune başlangıç durumu.

**Güncel model ve oyun içi teyit (2026-10-02):** Ezreal Q pozitif basic damage olarak etiketlidir ve Hexoptics kapsamındadır. Kullanıcı yakın148/uzak159 fiziksel hasar ölçtü; AA yakın102/uzak109. Wits End ile AA ve Q'da büyü hasarı iki mesafede de22 kaldı. Eski 'Q hasarı değişmemeli' yönergesi V5.62 classification bağlantısından önce kalmıştı ve kaldırıldı. Numeric mesafe/Brutal/Conqueror/yuvarlama ayrıştırılmadan breakpoint veya maksimum katsayı değiştirilmez.

### H03 — Magic on-hit kapsamı (H01/H02 sonrası)

Ezreal'a **Hexoptics + Wit's End** tak. Statları tekrar yaz. Yakın/uzak kritiksiz AA'da kırmızı ve mavi sayıları ayrı kaydet. Mevcut model mavi Wit's End on-hit'ini Hexoptics ile büyütmüyor. Hedefin MR'ı sabitken mavi sayı mesafeyle değişirse bu varsayım yanlıştır.

True damage/passive kapsamı ancak bunlar tamamlandıktan sonra: Vayne W üçüncü-hit veya Smolder burn kontrollü A/B. Champion pasifi, hedef HP ve rune amplifikasyonlarını ayırmadan tek sayıdan genelleme yapılmaz; şimdilik açık kalır.

**Bana yazılacak ilk paket:**

```text
Ezreal15 / sadece Hexoptics
AD ... AP ... AS ... crit ... crit damage ...
Rünler: ...
Tooltip: ...
Yakın normal AA: ... physical + ... magical / HP önce ...
Max AA range normal AA: ... physical + ... magical / HP önce ...
Yakın Q1: ... / Max AA range'den Q1: ...
Aktif rune/buff farkı: ...
```

## 2. Rageblade + Kraken + Terminus — I01

**Smolder level15, skill kullanmadan AA.** Kullanıcı Fleet/Battle Zeal/Cut Down/Bloodline/Bone Plating ile yalnız AA ölçtü; tüm sonuçlar `data/smolder-item-aa-tests-20261002.json` içinde.

### K01 — Kraken tek başına: teyit
AA3/6/9 proc. AD148: 79/79/170, 79/79/172, 79/79/174. Eksik can katsayısı tooltipte her %1 eksik HP için %0.75, maksimum %75.

### K02 — Rageblade tek başına: teyit
Phantom AA6/9; kombinasyonlarda AA12 de teyit edildi. AS stack cap/değer/süre bağımsız ölçülmedi.

### K03 — Terminus tek başına: teyit
Fiziksel hasar AA2/4/6'da, büyü AA3/5/7'de artar. Magic on-hit stack artışından önce, fiziksel hasar artıştan sonra hesaplanır. %10 Dark penetration katsayısı değişmedi.

### K04 — Rageblade + Kraken: teyit
İlk12 AA içinde Kraken **3/6/8/10/12**, Phantom **6/9/12**. AA12'de Kraken fiziksel hasarı ayrı gösterge olarak çıkar: 98+102.

### K05 — Rageblade + Terminus ve üçlü: teyit
Phantom Terminus stacklerini ilerletir. AA6 magic **36+38**; aynı AA içindeki olaylar ayrı dirençlerle hesaplanır. Sonraki magic38; Phantom38+38. Üçlü setup aynı stack/proc sırasını doğrular.

**Açık:** üçlü AA6 249 hesaplanan/250 görünen farkı ve ayrı fiziksel göstergelerin yuvarlaması. Proc anındaki hedef HP ve event içi HP snapshot ölçülmedi; katsayı uydurulmadı.

### K06 — Q on-hit kapsamı (AA tablolarından sonra)

Kraken yalnızken Q1→Q1→Q1 (cooldown/reset sayacı koruyorsa) veya **AA→AA→Q1**. Q Kraken'ı tamamlıyor mu? Rageblade/Terminus ile ayrıca Q sonrası item stackleri artıyor mu? Her champion'un skill'ine genelleme yapmadan önce yalnızca Ezreal Q kaydedilir.

**Bana yazılacak paket:**

```text
Build: ... / AD ... AP ... AS ... crit ...
Rünler: ... / başlangıç kukla HP ... armor ... MR ...
AA1: ... physical + ... magical / HP önce ... / stack ...
AA2: ...
...
Kraken proc AA numaraları: ...
Phantom AA numaraları: ...
Dark stack AA2/4/6 ve phantom sonrası: ...
```

## 3. Xayah — tüy hasarı ve yol testi

**Level15, Q1/W1/E4; ilk karşılaştırmada itemsiz.** AD/AP/crit chance/damage ve rünleri kaydet. R kullanma: fan geometrisi tüy sayısı ile isabet sayısını karıştırır. Önce kuklayla aynı doğru üzerinde dur; E anında konumu değiştirme.

### X01 — Tek tüy referansı

W→1AA→E. W sonrası pasif AA tek yerdeki tüyü üretmeli. **Sadece E hasarı** kaydedilir, setup AA ve W bonusu dahil edilmez. Kuklanın E öncesi HP'sini yaz. Bu değer `D1`.

### X02 — Üç ve beş aynı doğrultudaki tüy

Ayrı resetlenmiş denemeler:

- W→3AA→E: üç tüy. E toplamı `D3`; root geldi mi?
- Q→3AA→E: Q'dan iki, pasif AA'lardan üç = beş tüy. E toplamı `D5`; Q ve AA hasarını toplama dahil etme.

Her setup **ilk tüyden itibaren6s dolmadan** tamamlansın. Geç kalınırsa tüy silinmesi formül farkı gibi görünür. Q1/W1 ile AS yeterliyse ilave item gerekmez. Hedef HP farklılığı Battle Zeal/Cut Down/Coup de Grace gibi rünleri etkiliyorsa ayni durumla yeniden ölç veya buff bilgisi yaz.

| Gerçek isabet sayısı | Kaynaklı model E toplamı / D1 |
|---:|---:|
| 1 | 1 |
| 2 | 1.9 |
| 3 | 2.7 |
| 5 | 4 |
| 7 | 4.9 |
| 10 | 5.5 |
| 12 | 5.7 |

İlk zorunlu noktalar **1/3/5**. On tüy oluşturmak için karmaşık AH/AS buildi kurmak gerekmiyor; %10 tabanını oyunda doğrulamak ayrı ileri test olarak kalabilir. Itemsiz E4/bonusAD0/crit0, 100 armor/rune yoksa model D1=50, D3=135, D5=200; bunlar rune ve statlar eşleşmeden birebir hedef sayı değildir.

### X03 — Sağ-sol hareketin etkisi

X02 beş-tüy setup'ını tekrar et. Tüyleri oluşturduktan sonra, E'den önce:

1. Aynı hat üzerinde durup E (referans).
2. Aynı mesafeyi yaklaşık koruyarak sağa kısa yürüyüp E.
3. Aynı mesafeyi yaklaşık koruyarak sola kısa yürüyüp E.

Video gerekmez: E fiziksel hasarı, root var/yok, mümkünse kaç tüy çizgisinin kukladan geçtiği. **Atılan beş tüyün beşi de isabet etti varsayımı yapılmaz.** Lateral hasar farkı hit sayısından da kaynaklanır; per-feather katsayısı hemen değiştirilmez. Root, en az3hit için yardımcı işarettir; tam kaç tüy vurduğunu tek başına kanıtlamaz.

### X04 — R fanı (X01–X03 sonrasında)

AA/Q olmadan R→E; yakın ve normal AA mesafesinde dene. Her durumda beş R tüyünün hedefe geri dönerken gerçekten isabet etmesi garanti değil. D1 ile hasar/root karşılaştırılır. Exact lateral collision width/target hitbox/range kaynağı olmadan general collision engine doğrulanmış sayılmaz.

**Bana yazılacak paket:**

```text
Xayah15 Q1 W1 E4 / AD ... AP ... crit ... crit damage ...
Rünler: ...
W→1AA→E: E ... physical / HP önce ... / rune buff ...
W→3AA→E: E ... physical / root ... / HP önce ...
Q→3AA→E: E ... physical / root ... / HP önce ...
Beş tüy sonrası sağa kısa hareket→E: ... / root ...
Beş tüy sonrası sola kısa hareket→E: ... / root ...
```

## Sonuç geldiğinde kapanış kuralı

Ölçülen statlar ve rune durumu ile modele tekrar hesap yaptır. İlk farkta kaynak/engine/game state ayrımını yap; birbiriyle çelişen ölçümleri silme. İki tutarlı karşılaştırma ile desteklenen scope/sayaç kuralını uygula; bilinmeyen alanı açık bırak. Katsayı değişirse regression ve Jhin/Xayah sıralama doğrulaması tekrar çalıştırılır.

RFC/Stormrazor/Statikk, YunTal ve PD için kullanıcı onaylı değerler bu testlerin konusu değil. Spellblade satın alma kısıtı tamamlandı; tekrar birden fazla Spellblade alma testi istenmez.
