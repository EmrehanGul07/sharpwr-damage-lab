# Oyun içi doğrulama TODO — 1 Ekim 2026

Bu liste kalıcıdır. Akşam test sonuçları geldikçe maddeler kapanacak; bilinmeyenler sıfır veya kesin değer olarak kaydedilmeyecek. Hedef sabit kukla, bize saldırmıyor. Her ölçümde champion level, skill rank, toplam AD/AP/AS, crit chance/damage, mana ve rünler yazılmalı. Aynı kukla, aynı HP/armor/MR; farklı denemelerde kukla/stack resetlenmeli. Rünlerin tetiklenmesi hasarı değiştirebileceği için hangi buff aktif olduğuna dikkat edilmeli.

## Öncelikli ve sayı/metin ile yapılabilecekler

- [ ] **T01 — Muramana Q/W/E/R Shock tekrarları.** Her skill için Muramana ile/olmadan karşılaştır. Itemlerden gelen AD/crit farkını kaydet. W'nin iki vuruşunda ayrı fark var mı? R'nin her atışında mı, ilkinde mi, aralıklarla mı? V5.57 yalnızca cast'in ilk başarılı vuruşuna %3 max mana ekliyor; çoklu-vuruş tekrar kuralı henüz doğrulanmadı. Samira ranged şampiyon olduğu için melee animasyonunun item sınıflandırmasını değiştirip değiştirmediği de ayrıca kontrol edilmeli.
- [ ] **T02 — Mana iadesi.** Manamune/Muramana ile Q: 30 harcama ve 4.5 iade; W:60/9; E:40/6. Regen nedeniyle anlık değişim okunamıyorsa tooltip açıklaması yeterli. Kısa süre sonra görülen mana ile anlık tüketimi karıştırma.
- [ ] **T03 — R cooldown ve ability haste.** R tooltip/cooldown'u 0 AH ve bilinen AH ile karşılaştır. 6 saniye static mi, AH ile azalıyor mu? Sayaç cast başlangıcında mı, channel sonunda mı başlıyor?
- [ ] **T04 — Level büyümesi.** Samira itemsiz level1/5/9/15 AD, AS, max mana, HP, armor/MR. Var olan AD/AS kullanıcı referansları korunuyor; engine'in eski büyüme eğrisi WR ile ayrıca doğrulanmalı. Sadece ekran statlarını yazmak yeterli.
- [ ] **T05 — Skill on-hit/Spellblade.** Tek itemle Q/W/E/R kullan; BORK, Wit's End, Nashor, Terminus, Kraken ve Rageblade stack/proc üretiyor mu? Essence Reaver/Trinity/Iceborn için skill'in kendisi proc hasarı veriyor mu, yoksa sonraki AA mı? Aynı cast içinde kaç kez? İtemler tek tek test edilmeli.
- [ ] **T06 — Energized dolumu.** Başlangıç charge, tek AA sonrası charge, skill sonrası charge, yürürken/dash sonrası charge. RFC/Stormrazor/Shiv için ortak charge olup olmadığı, reset ve dolum katsayıları. Engine hareketi artık hesaplıyor, fakat doğrulanmış dolum katsayısı olmadığından tekrar charge üretmiyor.
- [ ] **T07 — AS item buff süreleri.** Phantom Dancer/Rageblade stack süreleri ve reset şartları; Yun Tal Flurry süresi/CD/AA ile cooldown azaltımı; Fiendhunter R sonrasında AA sayısı ve AS buff sona ermesi. Metin tooltip yeterli olan alanlar önce kapatılmalı.
- [ ] **T08 — WR skill timing/range metinleri.** W aktif süresi, R süresi, E dash mesafesi/hızı, Q ve AA projectile hızları varsa kaynak/tooltip. Şu anda kullanıcı onaylı PC timing fallback'ları ayrı kayıtlı.
- [ ] **T09 — Style/Conqueror çoklu-hit davranışı.** W1→E→W2 hangi Style artışını veriyor? W2/R'nin sonraki atışları Conqueror süresini yeniliyor mu? Yeni stack mi yoksa yalnızca süre yenileme mi?
- [ ] **T10 — İtem unique grupları.** Birden fazla Spellblade itemini aynı build'e alınca hangi proc geçerli? Aynı isimli unique etkiler toplanıyor mu, tek güçlü etki mi uygulanıyor?

## Sonraya bırakılabilen, daha zor doğrulamalar

- [ ] **T11 — Gerçek WR AA base windup / melee-ranged ayrımı.** Şimdilik PC base0.2279635s ve WR bonusAS×0.5 formülü kullanılıyor; kullanıcı ekran kaydı yapmak zorunda değil, uygun kaynak bulunursa kapatılabilir.
- [ ] **T12 — R'nin kesin tek tek shot offsetleri.** Şimdilik PC reference2.013s içine eşit aralıklı10hit, channel2.277s. Kesin WR atış planı farklı olabilir.
- [ ] **T13 — Hitbox / edge-center mesafe / MS soft cap.** Nokta-hedef yaklaşımı ve build MS toplaması geçici. Kaynak bulunursa manuel ölçüm gerekmeyebilir.
- [ ] **T14 — Immobilize hedefe pasif özel AA.** Ranged/melee özel hit sayısı, toplam hasar, retrigger10s, on-hit bir kere mi, AA reset/dash davranışı. Kukla CC olmadığı standart testlerde devrede değil.
- [ ] **T15 — AA atış anı ile hasar anı snapshot.** AD/crit buff'ları, AS ve item stack'leri AA launch'ta mı impact'te mi değerlendiriliyor? Mevcut kernel on-hit durumunu impact'te ilerletir; hasar stat snapshot ayrımı doğrulanmalı.

- [ ] **T16 — Diğer offensive keystone/rünler.** Samira replay şu anda Conqueror/Lethal Tempo ve desteklenen damage rünleriyle sınırlı. First Strike vb. desteklenmeyen loadout çalıştırılmıyor; bunların ayrı proc/cooldown koşulları kaynak/test ile tamamlanmalı.

## Bilerek test istenmeyen kapsam

Rakibin bize hasar vermesi, kendi ölümümüz, kendi regen/lifesteal ile hayatta kalma bu sabit-hedef hasar modelinin kapsamına dahil değil. Başka marksmanların özel ability engine'leri bu Samira denetiminin tamamlanması anlamına gelmez; ayrı aşamalardır.
