# Combat engine denetimi — V5.64.0

Üç adım tamamlandı: combat akışı denetimi, item tetikleyici denetimi ve 23 şampiyon × üç hedef için test matrisi.

## Düzeltilen sorunlar

- Aynı anda havada bulunan AA'lar artık benzersiz komut kimliği taşıyor; Conqueror gibi kimliğe bağlı kazançlar kaybolmuyor.
- Jhin şarjörünü isabette değil AA komutunda tüketiyor. Dördüncü vuruş bilgisi mermiyle taşınıyor; reload windup sonundan itibaren 2.5 saniye.
- Jinx roket manasını komutta ödüyor. Havada bulunan roket, sonraki minigun geçişinden etkilenmiyor.
- RFC/Stormrazor/Statikk kullanıcı tarafından ölçülmüş periyodik proc varsayımları event-driven yolunda da çalışıyor. Açık energized_ready olayı verilirse o olay öncelikli.
- Generic champion yolundaki Muramana skill Shock ana hasarla aynı hedef/rün çarpanını kullanıyor; ilk cast hit kısıtı korunuyor.
- Sivir Q dönüşü sabit 0.25 saniye yerine 1250 menzilli uç nokta, 1450 gidiş ve 1200 dönüş hızıyla hesaplanıyor. Sabit hedef için dönüş isabeti: cast sonu + 1250/1450 + (1250 − ilk mesafe)/1200. Bu hızların WR wiki metadata kaydı mevcut.
- Başarılı cast ve AA komutları artık ayrı timeline kaydına sahip: kaynak tüketimi, windup, impact, range ve lock denetlenebiliyor. Trace saklama normal optimizer kullanımında kapalı; audit isteğinde açılıyor.

## Doğrulama kapsamı

170 otomatik test geçti. 3312 build/hedef vakası, 6912 gerçek fight çalıştırması, sıfır integrity hatası. Her şampiyon için 144 vaka.

- Level 1 ve 15: itemsiz, crit, AP hybrid, on-hit, penetration ve cast-proc profilleri; Jinx, Darius ve Ornn hedefleri.
- Level 15: 36 itemin her biri tek tek, üç hedefte, tüm şampiyonlarda.
- E açık/kapalı ve Jinx silah varyantları evaluator tarafından çalıştırılıyor.
- HP ve hasar muhasebesi, olay sırası, finite/nonnegative damage, mana sınırları, AA kimliği, menzil, windup/impact sırası, channel/cast kilitleri kontrol edildi.
- Duskblade 10s, Spellblade 1.5s ve Galeforce 50s proc aralıkları; Spellblade öncesinde başarılı cast; Fiendhunter R gereksinimi, 8s pencere ve üç attack limiti kontrol edildi.
- Aynı zaman damgasında AA impact sonrası yapılan R, önceki AA'yı yeni Fiendhunter penceresine saymıyor. Bu audit sıralama kontrolü düzeltmesidir.

Duskblade ilk AA/10s; Galeforce bağımsız active/50s/325 dash/600 range; tek Spellblade kuralı; Fiendhunter yalnız R; gerçek mana maliyetleri ve Muramana refund korundu. Yun Tal, RFC, Stormrazor ve Statikk ölçüm varsayımları değiştirilmedi.

Bu matris en iyi build kanıtı veya bütün item kombinasyonlarının taraması değildir. Kaydedilen sonuçlar build cache olarak kullanılmaz. Integrity kontrolünden geçmek Wild Rift ile birebir eşitlik kanıtı değildir.

## Şampiyon kapsamı

| Şampiyon | Vaka | Hata | Model uyarısı sayısı |
|---|---:|---:|---:|
| Twitch | 144 | 0 | 6 |
| Yunara | 144 | 0 | 7 |
| Lucian | 144 | 0 | 6 |
| Varus | 144 | 0 | 9 |
| Ezreal | 144 | 0 | 2 |
| Vayne | 144 | 0 | 9 |
| Tristana | 144 | 0 | 7 |
| Ashe | 144 | 0 | 6 |
| Kalista | 144 | 0 | 5 |
| Draven | 144 | 0 | 6 |
| Caitlyn | 144 | 0 | 8 |
| Jinx | 144 | 0 | 5 |
| Kai'Sa | 144 | 0 | 6 |
| Kog'Maw | 144 | 0 | 10 |
| Miss Fortune | 144 | 0 | 7 |
| Xayah | 144 | 0 | 8 |
| Sivir | 144 | 0 | 5 |
| Corki | 144 | 0 | 5 |
| Senna | 144 | 0 | 6 |
| Zeri | 144 | 0 | 6 |
| Jhin | 144 | 0 | 9 |
| Samira | 144 | 0 | 0 |
| Smolder | 144 | 0 | 0 |

Uyarı sayıları tüm runtime açıklamalarını içerir; örneğin yetkilendirilmiş PC AA timing proxy kaydı da uyarıdır. Buff yetenekleri için generic projectile metadata eksikliği hasarlı mermi eksikliğiyle aynı anlama gelmez. Tam liste JSON içindedir.

## Açık kalan önemli bilgiler

1. Yunara maksimum mana, mana büyümesi/regen, hareket hızı ve gerçek menzil manuel WR verisi bekliyor. Mana affordability ve spatial timing henüz doğrulanmış değil; W linger contact/tick kapsamı da eksik.
2. Xayah Q efektif mermi hızı, Jhin W efektif travel ve Jinx E teslim/arming detayları kesinleşmedi. PC proxy ile WR doğrulamasını ayırıyoruz.
3. Kalista hop, Vayne tumble, Draven axe catch, Xayah lateral feather collision ve bazı channel/tick/charge ayrıntıları oyun içi test bekliyor.
4. Caitlyn headshot/crit, Kai'Sa passive level scaling, Lucian ikinci vuruş level progression, Senna passive/soul gain ve Zeri flat damage progression gibi mevcut provisional formüller ranking etkileyebilir.
5. Hexoptics kapsamı; Rageblade–Kraken–Terminus etkileşimi; item damage classification; Muramana çoklu-hit tekrar eligibility oyun içi TODO'da. Kog'Maw R mana ramp ve Corki R recharge kaynak çelişkileri korunuyor, katsayı uydurulmadı.
6. Geniş kitlerde bazı WR skill range metadata kayıtları yok; conservative AA-range fallback kullanılıyor. Bunun maksimum DPS/range karşılaştırmasına etkisi JSON uyarılarından takip edilmeli.

## Yeniden üretim

```bash
python -m unittest discover -s tests
python scripts/audit_combat_matrix.py
```

- `data/combat-audit-v564.json`: tüm vakalar, proc/cast sayıları ve şampiyon bazında provisional kayıtları.
- `data/combat-audit-traces-v564.json`: Samira/Ezreal/Jhin/Jinx level15 Ornn cast-proc örneklerinin komut ve hasar izleri.
- `docs/ingame-test-todo.md`: oyun içi doğrulama listesi.
