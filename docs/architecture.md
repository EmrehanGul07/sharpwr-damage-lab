# SharpWR mimarisi ve yol haritası

Durum: 5 Ekim 2026 · Sürüm: `VERSION` dosyası

## Hedef

SharpWR, Wild Rift oyuncuları için **tamamen ücretsiz bir fan aracıdır**. Bugün Streamlit ile web'de yayında. İleride Google Play'den indirilebilen bir Android uygulaması olarak da sunulacak.

Streamlit uygulaması mobil uygulama olarak paketlenemez: sunucuda çalışan, sürekli bağlantı isteyen bir web sayfasıdır. Bu yüzden projenin kalıcı değeri olan parçalar (hesaplama motoru, veriler, 3D stüdyo) Streamlit'ten bağımsız ve yeniden kullanılabilir olmalıdır. Streamlit, bu parçaları kullanan ince bir arayüz kabuğu olarak kalır.

## Katmanlar

```
data/ (JSON, sayıların tek kaynağı)
        │
        ▼
Çekirdek motor ── UI'dan bağımsız; JSON girdi → JSON çıktı; deterministik
        │
        ├──────────────► Streamlit arayüzü (web / araştırma aracı)
        │
        └──────────────► Mobil uygulama (Android, Play Store)

3D stüdyo ── bağımsız web modülü; Streamlit'te ve mobilde aynı kod
```

| Katman | Bugün | Hedef |
|---|---|---|
| Veri | `data/*.json`, `*_database.py` | Aynı. Sayılar yalnız JSON/veri modüllerinde durur, arayüz kodunda kopyası olmaz. |
| Motor | `fight_engine.py`, `marksman_fight_engine.py`, `build_fight_optimizer.py` vb. Streamlit import etmez. Ancak `sim`, `sim_build`, `_combat_hits`, `stats`, `rm`, `lvl_scale`, hedef profilleri ve item tabloları `streamlit_app.py` içinde. 17 test dosyası ve 8 script bunları o dosyadan AST + `exec` ile çıkarıyor. | `sharpwr/` paketi. Tek, belgelenmiş bir giriş noktası: girdi (şampiyon, seviye, item, rün, hedef) → olay kaydı + özet. Testler ve scriptler normal `import` kullanır. |
| Arayüz | `streamlit_app.py`: tek dosyada 6 sekme | Sekme başına modül; yalnız motoru çağırır, hesap yapmaz. |
| 3D stüdyo | `assets/marksman-3d/*.js`; `marksman_art.studio_html()` dosyaları tek HTML'e metin olarak birleştirir. GLB'ler `static/marksman-3d/` klasöründen uygulamanın kendisi tarafından sunulur (`app/static/`); GitHub kopyası yalnız yedektir. | Kendi başına açılan bir sayfa; veriyi JSON'dan, modelleri uygulamanın kendi dosyalarından yükler. |
| Mobil | Yok | Capacitor ile paketlenmiş web uygulaması (aşağıya bakın). |

## Mobil uygulama yaklaşımı (öneri; 6. adımda kesinleşir)

- **Kabuk:** Capacitor. Aynı web kodu Android'de (ileride iOS'ta) çalışır. 3D stüdyo zaten JavaScript/Three.js olduğu için doğrudan taşınır.
- **Motor:** Telefonda çalışır: internet ve sunucu gerekmez, sunucu masrafı yoktur. Bunun için motorun TypeScript'e taşınması gerekir.
- **Doğruluk:** Taşınan motor, Python motorundan üretilen referans (golden) çıktılara karşı birebir test edilir. Kaynak olarak mevcut entegrasyon matrisi (3.312 senaryo / 6.912 dövüş) kullanılır. İki motor sürümü yan yana durduğu sürece Python sürümü referanstır.
- **Değerlendirilen alternatifler:** Sunucuda Python (FastAPI) internet ve sunucu maliyeti gerektirir. Pyodide (Python'ı telefonda çalıştırmak) uygulamayı büyütür ve açılışı yavaşlatır.

## Mobil boyut ölçümü (5 Ekim 2026)

23 şampiyonun GLB'lerinde doku yoktur; boyutun tamamı geometri ve animasyondur. `gltf-transform` 4.5.1 ile ölçüldü, depodaki dosyalar değiştirilmedi:

| Set | Bugün | meshopt | optimize + meshopt (palet ve simplify kapalı) |
|---|---|---|---|
| Tam modeller (`character.glb`) | 27,3 MB | 6,4 MB | 5,6 MB |
| Önizlemeler (`preview.glb`) | 10,1 MB | 3,9 MB | 3,5 MB |
| Toplam | 37,4 MB | 10,3 MB | 9,1 MB |

Sıkıştırılmış 92 dosyanın hepsi Three.js `GLTFLoader` + `MeshoptDecoder` ile açıldı ve 8 klibini korudu. Tüm kliplerde kemik pozisyonu sapması en fazla 0,0016 dünya birimi (≈0,16 oyun birimi). `optimize` varsayılan olarak malzemeleri bir palet dokusuna dönüştürür; bu yüzden `--palette false` gerekir. Uygulamadan önce `scene.js` yükleyicisine `MeshoptDecoder` eklenmeli ve yazılım (CPU skinning) yolu tarayıcıda görsel olarak karşılaştırılmalıdır.

## Kurallar

1. **Bağımlılık tek yönlüdür:** arayüz → motor → veri. Motor Streamlit'i veya arayüz modüllerini import etmez.
2. **Yeniden düzenleme davranışı değiştirmez.** Her adımda Python ve JS testleri çalışır. Motora dokunan adımlarda entegrasyon matrisinin çıktıları önce/sonra birebir karşılaştırılır.
3. **Yeni ve taşınan kod okunabilir yazılır:** açıklayıcı isimler, makul satır uzunluğu, motor API'sinde tip bilgisi.
4. **Model kaynakları depoya girmez.** `.blend` dosyaları ve indirme paketleri `art-sources` GitHub Release'inde tutulur; CI yalnız kaynak değiştiğinde Blender ile yeniden üretir. Depoda yalnız uygulamanın çalışırken kullandığı GLB'ler (`static/marksman-3d/`) kalır.
5. **Riot kaynaklı görseller ayrı tutulur.** Projede duranlar `assets/riot/` ve `data/riot/` klasörlerindedir. Bunların ve site çalışırken dışarıdan yüklenen her şeyin listesi: [third-party-assets.md](third-party-assets.md). 3D modeller orijinal çizimdir ama Riot karakterlerini tasvir eder.
6. **Sürüm tek kaynaktan gelir:** `VERSION`. Python kodu değişen her yayında artırılır. Canlı sunucu motor modüllerini yalnız sürüm değiştiğinde yeniden yükler (`engine_runtime.py`).

## Yasal

Uygulama ücretsizdir ve Riot Games ile bağlantısı yoktur. Play Store yayınından önce şunlar okunmalıdır:
- Riot Games'in fan projesi politikası ("Legal Jibber Jabber"),
- Google Play'in fikri mülkiyet politikası.

Riot'un standart feragat metni README'de ve sitenin alt bilgisinde gösterilir; bir test ikisinin aynı kalmasını denetler.

## Yol haritası

| # | Adım | Durum |
|---|---|---|
| 1 | Hızlı temizlik: stüdyo önbelleği, `use_container_width` → `width`, tek kaynaklı sürüm, bu doküman | Tamamlandı (7.0.1) |
| 2a | Model dosyaları: `.blend`/zip → `art-sources` Release; GLB'leri uygulamanın kendisinden sunmak; Ezreal'i sayfaya gömmeyi bırakmak (sayfa 4,4 MB → 0,75 MB) | Tamamlandı (7.0.2) |
| 2b | Riot kaynaklı görselleri ayırmak, dış bağlantıların envanteri, feragat metnini arayüze eklemek, mobil için model boyutu ölçümü | Tamamlandı (7.0.3) |
| 3 | Çekirdek motor: `streamlit_app.py` içindeki hesapları `sharpwr/` paketine taşımak, JSON API, referans (golden) çıktılar; ardından arayüzü sekme modüllerine bölmek | |
| 4 | 3D stüdyoyu bağımsız web modülü yapmak | |
| 5 | Build Lab dövüşünü 3D'de izlemek (hasar sayıları, HP, stack göstergeleri) | |
| 6 | Mobil prototip: Capacitor + TypeScript motor + Play Store kapalı test kanalı | |
| 7 | Görsel kalite (telefon performans bütçesiyle) | |
| 8 | Gerçek 1v1 düello (hedefin karşılık vermesi) | |

Paralel kol: yeni oyun içi ölçümler geldikçe [ingame-test-todo.md](ingame-test-todo.md) kapatılır.
