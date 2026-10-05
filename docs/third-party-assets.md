# Üçüncü taraf içerik envanteri

Durum: 5 Ekim 2026. SharpWR ücretsiz bir fan projesidir ve Riot Games ile bağlantısı yoktur. Riot'un fan projesi notu README'de ve sitenin alt bilgisinde gösterilir (`RIOT_NOTICE`, `streamlit_app.py`).

Bu dosyanın amacı: Riot'a ait görselleri ve dış bağlantıları tek bir listede toplamak, böylece gerektiğinde kolayca değiştirilebilir veya çıkarılabilir olmalarını sağlamak. Play Store yayınından önce Riot Games'in fan projesi politikası ("Legal Jibber Jabber") ve Google Play'in fikri mülkiyet politikası ayrıca okunmalıdır.

## Projede duran Riot görselleri

Hepsi `riot/` adlı klasörlerde tutulur.

| Yol | İçerik | Kaynak |
|---|---|---|
| `assets/riot/items/` | 28 Wild Rift item ve boots ikonu (PNG/WebP) | Topluluk wiki'leri ve fan siteleri; dosya bazında kaynak kaydedilmemiş |
| `data/riot/marksman-skill-icons.json` | 23 şampiyon için 115 yetenek ikonu (base64) | 20 şampiyon kullanıcının Wild Rift ekran görüntülerinden kırpıldı, 3 şampiyon Riot Data Dragon'dan. Her şampiyonun `source` alanı kaynağı belirtir. |

## Site çalışırken dışarıdan yüklenenler

| Adres | Ne için | Kodda | Sahibi | Mobil uygulama için |
|---|---|---|---|---|
| `cdn.jsdelivr.net/npm/three@0.169.0` | 3D kütüphanesi (Three.js) | `assets/marksman-3d/scene.js`, `studio.html`, `assets/combat_replay.html`, `assets/ezreal_replay_3d.js` | Açık kaynak (MIT) | Uygulamaya gömülmeli; paket zaten `package.json`'da |
| `raw.communitydragon.org` | Yerel kopyası olmayan item ikonları ve 4 rün ağacı ikonu | `CD_ITEM_ICON_BASE`, `ITEM_ICON_FILE`, `TREE_ICON_URL` (`streamlit_app.py`) | Riot görselleri (PC oyun dosyalarından) | Yerel kopyaları `assets/riot/` altına alınmalı |
| `www.riftpatchnotes.com/runes/` | Rün ikonları | `rune_icon()` (`streamlit_app.py`) | Riot görselleri, bir fan sitesinden doğrudan bağlanıyor | Resmi bir kaynaktan yerel kopya ile değiştirilmeli |
| `ddragon.leagueoflegends.com/cdn/15.15.1` | Şampiyon portreleri | `_champion_profile()` (`streamlit_app.py`) | Riot'un resmi Data Dragon'u (PC görselleri) | Yerel kopyaları `assets/riot/` altına alınmalı |
| `raw.githubusercontent.com/.../static/marksman-3d` | 3D modeller için yedek adres | `MODEL_FALLBACK` (`scene.js`) | Bu proje | Gerekmez; modeller uygulamanın içinde |
| `github.com/.../releases/download/art-sources` | Blender kaynakları ve indirme paketleri | `RELEASE_URL` (`marksman_art.py`) | Bu proje | Gerekmez |

## Orijinal içerik

- `static/marksman-3d/` ve `assets/marksman-3d/models/` altındaki 3D modeller ve animasyonlar bu proje için çizildi; oyundan çıkarılmış dosya değildir. Ancak Riot karakterlerini tasvir ettikleri için fan çalışmasıdır.
- Hesaplama motoru, arayüz kodu ve hesaplanmış veriler bu projeye aittir.

## Kaynak gösterimleri

`data/*.json` dosyalarındaki bağlantılar (`wiki.leagueoflegends.com`, `raw.communitydragon.org`, `drive.google.com`) yalnız kaynak gösterimidir; site çalışırken yüklenmez. `data/marksman-ability-evidence.json` içinde 182 Google Drive klasör bağlantısı vardır. Depo herkese açık olduğu için bu klasörlerin paylaşım ayarları kontrol edilmelidir.
