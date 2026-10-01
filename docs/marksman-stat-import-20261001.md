# Marksman stat veritabanı — 1 Ekim 2026

23 şampiyon kaydı. Yunara hariç 22 şampiyonun Wild Rift wiki parametre tabloları doğrudan okundu. Her şampiyona 14 eksik temel stat eklendi: toplam 308 yeni sayısal alan. Mevcut altı AD/AS alanının 138 değeri aynen korundu.

Wiki referansı güncel oyun içi 7.3a ölçümüyle eşdeğer kabul edilmez. Sayfanın kendi son değişiklik yaması ve erişim tarihi her kayıtta tutulur. Çatışan wiki AD/AS ve crit verileri modele uygulanmadı. PC stat fallback kullanılmadı.

## Eklenen temel alanlar

| Alan | Büyüme alanı |
|---|---|
| HP | HP growth |
| HP regen / 5 saniye | HP regen growth / 5 saniye |
| Mana | Mana growth |
| Mana regen / 5 saniye | Mana regen growth / 5 saniye |
| Armor | Armor growth |
| MR | MR growth |
| Movement speed | — |
| Attack range | — |

Bu 14 alan 22 şampiyonun tamamında bulundu. Regen değerleri saniye başına değil, 5 saniye başınadır. Büyüme katsayıları kaynakta yazıldığı gibi saklanır; bu import sırasında yeni level büyüme formülü varsayılmadı.

## Kaynakta bulunmayan alanlar

| Alan | Eksik şampiyon sayısı (Yunara hariç) |
|---|---|
| attack_cast_time | 22 |
| attack_total_time | 22 |
| attack_delay_offset | 22 |
| attack_windup | 22 |
| windup_modifier | 21 |
| attack_projectile_speed | 21 |
| gameplay_radius | 22 |

Senna için kaynakta windup_modifier = 0.60000002384186 ve attack_projectile_speed = 0 açıkça verilmiş. Bu iki alan sıfırla doldurulmadı; kaynaktaki sayılar aynen kaydedildi. Diğer 21 şampiyonda bu iki alan boş.

Yunara: mevcut altı AD/AS değeri korunuyor; 14 temel stat ve yedi timing/hitbox alanı manuel veri bekliyor.

Samira için daha önce gönderilen PC timing referansı bu WR stat tablosundaki boşlukları doldurmak için kullanılmadı. WR/PC kaynakları ayrı tutulur.

## Kayıt bazında kaynak ve eksikler

| Şampiyon | Son wiki değişiklik yaması | Kaynak | Eksik alan sayısı |
|---|---|---|---|
| Kalista | V6.3e | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Kalista) | 7 |
| Tristana | V7.0f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Tristana) | 7 |
| Twitch | V6.2c | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Twitch) | 7 |
| Draven | V6.1d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Draven) | 7 |
| Kog'Maw | V6.3f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Kog'Maw) | 7 |
| Vayne | 7.0a | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Vayne) | 7 |
| Ashe | V7.0c | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Ashe) | 7 |
| Varus | V6.2e | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Varus) | 7 |
| Xayah | V7.0d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Xayah) | 7 |
| Samira | V6.1d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Samira) | 7 |
| Miss Fortune | V6.3f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Miss_Fortune) | 7 |
| Yunara | — | Manuel bekleniyor | 21 |
| Kai'Sa | V5.1d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Kai'Sa) | 7 |
| Corki | V7.1 | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Corki) | 7 |
| Lucian | V6.3d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Lucian) | 7 |
| Smolder | 7.0f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Smolder) | 7 |
| Caitlyn | V6.3f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Caitlyn) | 7 |
| Jinx | V6.3f | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Jinx) | 7 |
| Ezreal | V7.0 | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Ezreal) | 7 |
| Zeri | V6.3d | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Zeri) | 7 |
| Jhin | V6.0 | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Jhin) | 7 |
| Sivir | V6.1a | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Sivir) | 7 |
| Senna | V6.2c | [WR stat tablosu](https://wiki.leagueoflegends.com/en-us/Template:WR_Data_Senna) | 5 |

## Kullanım

`data/marksman_champion_stats.json`: değerler, alan kaynakları ve eksikler.

`data/marksman_champion_stats.csv`: karşılaştırma tablosu.

`champion_database.py`: uygulamada kayıt/stat erişimi. Database → Champions bölümünde arama, tüm statlar ve kaynaklar görünür.

Bu değişiklik veri katmanını ekler. Mana tüketimi, own-HP/iyileşme ve hareket motoru bu import ile otomatik olarak tamamlanmış sayılmaz.
