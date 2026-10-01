# Samira offline engine audit — V5.57

## Tamamlanan düzeltmeler

- AA timer sabit bir gelecek timestamp yerine bir saldırılık kalan ilerleme olarak tutulur. E/Lethal Tempo ve item AS değişimleri kalan süreyi günceller; buff bitişi ayrı clock olayıyla işlenir. Fiendhunter/Yun Tal expiry ve Rageblade/Phantom Dancer stack'leri UI AS callback'inde görünür.
- Windup hesaplaması yalnızca PC base0.149999994/0.658 kullanır; WR formülüyle bonusAS×0.5. PC damage/AD/AS tabloları aktarılmaz. AA iptal edilmez.
- Dash devam ederken gelecek bir AA'nın eski pozisyona göre planlanması düzeltildi. Auto scheduler dash sonrasında range'i yeniden değerlendirir; hedefe yürür ve saldırır. Float sınırlarında tolerans eklendi.
- Hexoptics AA etkisi başlangıç mesafesini değil olayın güncel mesafesini kullanır.
- Style expiry yeni R cast doğrulamasından önce kontrol edilir; aktif R içindeyken ikinci R açılamaz.
- Manamune/Muramana %15 mana iadesi eklenir. Resource kontrolü önce tam cast cost gerektirir, iade sonra uygulanır.
- Muramana ranged ability %3 max mana Shock ilk başarılı cast hit'ine eklenir. Çoklu-hit tekrar eligibility henüz bilinmediğinden cast içinde yalnız bir defa uygulanır ve log TODO notu taşır. Bu, tam WR tekrar kuralı olduğu iddiası değildir.
- Damage ledger gerçek hedef HP kaybını toplar; overkill ayrı raw_damage alanındadır. Collector dahil HP kaybı/total/sum(log) korunur.

## Offline doğrulama

Gerçek shared item kernel ile her completed item ve her boot tek tek Ornn statlarında test edilir. Level1/5/9/15, None/Conqueror/Lethal Tempo ve üç örnek build kombinasyonu için finite değerler, mana sınırı, HP sürekliliği, damage conservation, target-range rejection olmaması kontrol edilir. Expected replay deterministik karşılaştırılır. Unit testler ayrıca W/R kilitleri, W iptali, E-Q/W, mana/refund, expiry, movement, AA windup, mid-cycle AS değişimi ve AS buff bitişini kapsar.

Bu testler hesaplama/akış regresyonunu doğrular; oyuna birebir eşitliğin kanıtı değildir. Açık mekanikler docs/ingame-test-todo.md içindedir. Kaynak bilinmeyen proc/charge/radius katsayıları uydurularak kapatılmadı.

## Resmî kaynak

https://wildrift.leagueoflegends.com/en-us/news/game-updates/wild-rift-patch-notes-7-3/

Awe:2% max mana AD ve15% mana iadesi. Muramana Shock:AA1.5% max mana; ability3.5%/3% melee/ranged. Samira'nın kısa mesafeli animasyonu ranged champion sınıflandırmasını değiştirdiği varsayılmadı. Cast içi tekrar kuralı kaynakta belirtilmiyor.

## Son doğrulama

66 test geçti. Matris:36 item +14 boot +36 level/rün/build senaryosu; deterministik Expected replay ayrıca karşılaştırıldı. Son Battle Zeal düzeltmesinden sonra39 fight-engine ve3 matrix testi tekrar geçti. Battle Zeal basic-skill amplifikasyonu skill'in toplam hasar bileşenlerine uygulanır; AA/R'ye aktarılmaz. Kullanıcıya sorulacak oyun içi ölçümler tek TODO listesinde16madde olarak toplandı.
