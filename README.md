# Mac Cleaner App - Documentation

## Proje Amacı
Bu proje, macOS (özellikle MacBook Air M1) cihazlar için disk alanını yönetmeye ve gereksiz dosyaları temizleyerek yer açmaya yarayan bir masaüstü uygulamasıdır.

## Özellikler
Uygulama aşağıdaki kategorilerdeki dosyaları tarar ve temizler:
1. **System Caches:** `~/Library/Caches` dizinindeki önbellek dosyaları.
2. **System Logs:** `~/Library/Logs` dizinindeki sistem logları.
3. **Trash Bin:** Çöp kutusundaki dosyalar (`~/.Trash`).
4. **Media Analysis Data:** macOS'un arka planda oluşturduğu medya analiz verileri (`~/Library/Containers/com.apple.mediaanalysisd/Data`).
5. **App Leftovers:** Kaldırılmış uygulamalardan geriye kalan artık klasörler (`~/Library/Application Support` içerisinde arama yapar. Güvenli kelimeler ve hali hazırda yüklü olan uygulamalar hariç tutulur).

**Ekstra Özellikler:**
- **Modern Arayüz:** `customtkinter` kütüphanesi ile geliştirilmiş modern, karanlık/aydınlık tema uyumlu bir kullanıcı arayüzü (UI).
- **Asenkron İşlemler:** Tarama ve temizleme işlemleri `threading` kullanılarak arka planda yapılır, böylece arayüz donmaz.
- **Boyut Formatlama:** Bulunan gereksiz dosyaların boyutları okunabilir bir formatta (KB, MB, GB) kullanıcıya sunulur.

## Dosya Yapısı
- `app.py`: Uygulamanın ana giriş noktasıdır. `MacCleanerApp` sınıfını barındırır ve grafiksel kullanıcı arayüzünü (GUI) yönetir.
- `scanner.py`: Sistemin taranması ve dosyaların silinmesi ile ilgili iş mantığını (`Scanner` sınıfı) içerir. Boyut hesaplama ve formatlama gibi yardımcı fonksiyonlar da buradadır.
- `requirements.txt`: Projenin bağımlılıklarını listeler (`customtkinter`, `psutil`).
- `run.sh`: Sanal ortamı (`venv`) aktif edip uygulamayı başlatmak için kullanılan pratik bir bash scriptidir.
- `MacCleaner.spec`: Uygulamayı tek bir çalıştırılabilir (executable) `.app` veya dosya haline getirmek için kullanılan `PyInstaller` konfigürasyon dosyası.
- `venv/`: Python sanal ortam (virtual environment) klasörü.
- `build/` & `dist/`: PyInstaller tarafından oluşturulan derleme çıktıları.

## Nasıl Çalıştırılır?
Uygulamayı çalıştırmak için terminal üzerinden proje dizinindeyken aşağıdaki komutu kullanabilirsiniz:
```bash
./run.sh
```

## Gelecekte Eklenebilecek Özellikler / Notlar
*(Yeni özellikler eklendikçe veya mevcut yapı değiştirildikçe bu döküman güncellenmelidir.)*
- Temizlenebilecek yeni dizinler eklenebilir.
- Kullanıcıya tarama sırasında detaylı bir dosya/klasör listesi gösterilebilir.
- Uygulama ayarları (Örn: tarama istisnaları) bir konfigürasyon dosyasına kaydedilebilir.

## Güncellemeler
- **Arayüz (UI) İyileştirmeleri (14 Mayıs 2026):** "CLEAN / DELETE" butonu görünürlüğü artırılacak şekilde sürekli aktif hale getirildi ve silme işleminin kolay fark edilmesi için sağ üst panele ("Scan Now" butonunun yanına) taşındı. Ekrandan taşma/gizlenme sorununun önüne geçmek için uygulamanın başlangıç boyutu 700x700 olarak büyütüldü ve ana ekrandaki dizin yazılarının boyutu (14'ten 11'e) küçültüldü.
- **Güvenlik ve Doğruluk Düzeltmeleri (14 Mayıs 2026):** Github vb. platformlarda kaynak kodu paylaşmaya uygun hale getirmek amacıyla ciddi güvenlik düzeltmeleri uygulandı:
  - **TOCTOU ve Symlink (Sembolik Bağlantı) Koruması:** `shutil.rmtree` kullanımı, sembolik bağlantıları takip ederek sistemin başka yerlerindeki kritik dosyaları silme (Symlink escape) riskine karşı özel bir `safe_delete` fonksiyonu ile değiştirildi. Klasör ve dosyalar silinmeden önce `os.path.realpath` ve `os.path.commonpath` ile hedeflenen güvenli dizinler (örn. `~/Library/Application Support`) içinde olup olmadıkları sıkı bir şekilde doğrulanıyor. Ayrıca `os.path.islink` kullanılarak symlinklerin içi değil, bizzat kendisi siliniyor.
  - **Kesin `find_leftovers` Eşleştirmesi:** Eski gevşek substring mantığı kaldırıldı. Artık `/Applications` altındaki uygulamaların `Info.plist` dosyaları `plistlib` ile okunarak `CFBundleIdentifier` (örn. `com.google.Chrome`) değerleri çıkarılıyor. Uygulama kalıntıları, sadece "içinde x geçen kelime" yerine bu resmi Bundle ID'ler ve tam uygulama isimleri üzerinden tespit ediliyor.
  - **Katı `safe_keywords` Denetimi:** Klasör isimlerinde sadece "apple" kelimesi geçtiği için Pineapple Studio gibi klasörlerin güvenli sayılması (veya tam tersi yanlış silinmesi) hatası düzeltildi. Bunun yerine tam eşleşme (exact) ve prefix (`com.apple.`) eşleşmesi mantığına geçildi.
  - **Hataların Gizlenmesi Engellendi (Error Swallowing):** `try/except Exception: pass` gibi hataları yutan bloklar düzeltildi. Olası permission (izin) hataları ve bozulan klasör durumları tespit edilip arayüze/hata listesine aktarıldı.
  - **Silme Boyutu Doğruluğu (Race Condition):** Dosya silmeden hemen önce boyut okuyup ardından silmeye çalışırken oluşabilecek durumlar önlendi. Artık ağaç yapısında `os.walk` ile anlık olarak her bir dosya silinirken boyutu alınarak %100 gerçeği yansıtan serbest bırakılmış (freed_space) alan hesaplanıyor.
  - **Cache Klasörü Koruması:** `~/Library/Caches` dizininin toptan silinmesinin bazı geliştirici/medya uygulamalarını bozabileceği gerçeğine karşılık, arayüzde bu seçenek varsayılan olarak kapalı (off) ayarlandı ve uyarı metni eklendi.
