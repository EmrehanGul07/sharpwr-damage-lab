# Üçüncü taraf içerik envanteri

Durum: 5 Ekim 2026. SharpWR ücretsiz bir fan projesidir ve Riot Games ile bağlantısı yoktur. Riot'un fan projesi notu README'de ve sitenin alt bilgisinde gösterilir (`RIOT_NOTICE`, `streamlit_app.py`).

Bu dosyanın amacı: Riot'a ait görselleri ve dış bağlantıları tek bir listede toplamak, böylece gerektiğinde kolayca değiştirilebilir veya çıkarılabilir olmalarını sağlamak. Play Store yayınından önce Riot Games'in fan projesi politikası ("Legal Jibber Jabber") ve Google Play'in fikri mülkiyet politikası ayrıca okunmalıdır.

## Projede duran Riot görselleri

Hepsi `riot/` adlı klasörlerde tutulur. Uygulamanın gösterdiği her ikon, dosya yolu ve kaynağıyla `data/riot/icons.json` listesindedir. Listede olup projede olmayan dosyaları "Fetch bundled Riot icons" GitHub iş akışı (`scripts/fetch_riot_icons.py`) indirir; liste değiştiğinde kendiliğinden çalışır.

| Yol | İçerik | Kaynak |
|---|---|---|
| `assets/riot/items/` | 14 Wild Rift item ve 14 boots ikonu | Topluluk wiki'leri ve fan siteleri; dosya bazında kaynak kaydedilmemiş |
| `assets/riot/items/` (sayısal adlar) | 22 item ikonu | Community Dragon (PC oyun dosyaları) |
| `assets/riot/runes/` | 51 rün ikonu | riftpatchnotes.com (fan sitesi) |
| `assets/riot/rune-trees/` | 4 rün ağacı ikonu | Community Dragon |
| `assets/riot/champions/` | 23 şampiyon portresi | Riot Data Dragon 15.15.1 (PC) |
| `data/riot/marksman-skill-icons.json` | 23 şampiyon için 115 yetenek ikonu (base64) | 20 şampiyon kullanıcının Wild Rift ekran görüntülerinden kırpıldı, 3 şampiyon Riot Data Dragon'dan. Her şampiyonun `source` alanı kaynağı belirtir. |
| `assets/riot/abilities/` | Aynı 115 yetenek ikonu, telefon uygulaması için dosya olarak | `scripts/export_app_data.py` yukarıdaki JSON'dan üretir; elle düzenlenmez. |

## Site çalışırken dışarıdan yüklenenler

| Adres | Ne için | Kodda | Sahibi | Mobil uygulama için |
|---|---|---|---|---|
| `cdn.jsdelivr.net/npm/three@0.169.0` | 3D kütüphanesi (Three.js) | `assets/marksman-3d/scene.js`, `studio.html`, `assets/combat_replay.html`, `assets/ezreal_replay_3d.js` | Açık kaynak (MIT) | Uygulamaya gömülmeli; paket zaten `package.json`'da |
| `raw.githubusercontent.com/.../static/marksman-3d` | 3D modeller için yedek adres | `MODEL_FALLBACK` (`scene.js`) | Bu proje | Gerekmez; modeller uygulamanın içinde |
| `github.com/.../releases/download/art-sources` | Blender kaynakları ve indirme paketleri | `RELEASE_URL` (`marksman_art.py`) | Bu proje | Gerekmez |

İkonlar için dış adresler yalnız yedek olarak kalır: bir ikon dosyası projede yoksa site, `icons.json`'daki kaynak adresi kullanır.

## Mobil uygulamanın internetten aldıkları

Uygulama internetsiz çalışır; bu adresler yalnız güncelleme içindir. Hepsi bu projenindir ve `mobile/src/online.ts` ile `mobile/src/live-update.ts` dosyalarındadır. Telefondan GitHub'a kişisel veri gönderilmez; GitHub yalnız her sitenin gördüğü bağlantı bilgilerini (IP adresi gibi) görür.

| Adres | Ne için | Ne zaman |
|---|---|---|
| `raw.githubusercontent.com/.../main/app-data/database.json` | Güncel Database verisi | Her açılışta |
| `raw.githubusercontent.com/.../main/assets/riot/...` | Yeni eklenen, uygulamada olmayan bir ikon | Yalnız böyle bir ikon gösterilirken |
| `github.com/.../releases/download/mobile-preview/sharpwr-web.json` | Yeni ekranlar (canlı güncelleme) var mı | Her açılışta, yalnız önizleme (GitHub) sürümünde |
| `github.com/.../releases/download/mobile-preview/sharpwr-web-<sürüm>.zip` | Yeni ekranları indirmek (SHA-256 ile doğrulanır) | Yeni sürüm olduğunda, arka planda |
| `github.com/.../releases/download/mobile-preview/sharpwr-database-preview.apk` | Yeni APK'yı indirmek (yalnız Android kabuğu değiştiğinde) | Kullanıcı "Download"a dokununca, telefonun tarayıcısında |

Canlı güncellemeyi `@capgo/capacitor-updater` eklentisi yapar. Eklentinin kendi sunucularına (`plugin.capgo.app`: güncelleme, istatistik, kanal) bağlanması kapalıdır (`mobile/capacitor.config.json`).

## Orijinal içerik

- `static/marksman-3d/` ve `assets/marksman-3d/models/` altındaki 3D modeller ve animasyonlar bu proje için çizildi; oyundan çıkarılmış dosya değildir. Ancak Riot karakterlerini tasvir ettikleri için fan çalışmasıdır.
- Hesaplama motoru, arayüz kodu ve hesaplanmış veriler bu projeye aittir.

## Kaynak gösterimleri

`data/*.json` dosyalarındaki bağlantılar (`wiki.leagueoflegends.com`, `raw.communitydragon.org`, `drive.google.com`) yalnız kaynak gösterimidir; site çalışırken yüklenmez. `data/marksman-ability-evidence.json` içinde 182 Google Drive klasör bağlantısı vardır. Depo herkese açık olduğu için bu klasörlerin paylaşım ayarları kontrol edilmelidir.
