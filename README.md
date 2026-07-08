# Water Reminder Desktop App

![Water Reminder Demo](example.gif)

Water Reminder adalah aplikasi desktop sederhana berbasis **Python + PyQt5** untuk mengingatkan pengguna agar minum air secara berkala. Aplikasi berjalan di background, muncul di pojok kanan bawah layar, menampilkan karakter GIF, lalu memberi pilihan **Sudah minum** atau **Snooze**.

## Fitur

- Reminder otomatis setiap 30 menit.
- Tombol **Sudah minum** untuk mereset interval kembali ke 30 menit.
- Tombol **Snooze 10 menit** jika belum ingin minum.
- Jika user menekan snooze berkali-kali, aplikasi akan menampilkan alert tambahan.
- Bisa berjalan otomatis saat Windows startup.
- Bisa berjalan tanpa terminal menggunakan `pythonw.exe`.
- Karakter ditampilkan dari file GIF transparan.

---

## Struktur Folder

Contoh struktur project:

```text
water-reminder/
├─ venv/
├─ app.py
├─ make_transparent.py
├─ target.gif
├─ target_transparent.gif
└─ start_water_reminder.vbs
```

Penjelasan file:

```text
app.py
```

File utama untuk menjalankan aplikasi reminder.

```text
make_transparent.py
```

File utility untuk mengubah `target.gif` menjadi `target_transparent.gif`.

```text
target.gif
```

GIF mentah/original. Siapkan file GIF kamu dengan nama ini.

```text
target_transparent.gif
```

GIF hasil remove background. File ini yang dipakai oleh `app.py`.

```text
start_water_reminder.vbs
```

File untuk menjalankan aplikasi tanpa terminal dan bisa dipakai untuk auto-startup Windows.

---

## Persiapan

Pastikan Python sudah terinstall.

Cek versi Python:

```bash
python --version
```

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan virtual environment:

```bash
venv\Scripts\activate
```

Install dependency:

```bash
pip install PyQt5 pillow numpy
```

---

## Persiapan GIF

Siapkan GIF original dengan nama:

```text
target.gif
```

Simpan di folder project yang sama dengan `app.py`.

Rekomendasi GIF:

- Background sebaiknya **solid green** `#00FF00` atau warna mencolok lain.
- Hindari background gelap jika karakter memakai jas hitam.
- Hindari shadow, gradient, atau background rumit.
- Pastikan karakter berada dalam canvas yang cukup, tidak terpotong.
- Untuk hasil optimal, ukuran GIF tidak perlu terlalu besar. Idealnya lebar sekitar 400–700 px.

Contoh prompt jika membuat GIF dari AI:

```text
Create a pixel art animated GIF of the character drinking water.
Use a solid bright green background color #00FF00.
No shadow, no gradient, no texture, no checkerboard.
Keep the full body visible and centered.
```

---

## Convert GIF Jadi Transparan

Jalankan:

```bash
python make_transparent.py
```

Jika berhasil, akan muncul file:

```text
target_transparent.gif
```

File inilah yang akan dipakai oleh aplikasi utama.

Jika background belum bersih, atur nilai berikut di `make_transparent.py`:

```python
TOLERANCE = 40
```

Panduan:

```text
Background masih nyisa      → naikkan TOLERANCE
Jas/karakter ikut hilang    → turunkan TOLERANCE
```

Jika animasi jalan jadi hilang atau karakter selalu di tengah, pastikan jangan melakukan crop per frame. Gunakan global trim, bukan center per frame.

---

## Menjalankan Aplikasi

Jalankan:

```bash
python app.py
```

Jika berhasil, aplikasi akan berjalan dan menunggu sesuai interval yang diatur.

Untuk menghentikan aplikasi:

- Klik kanan tray icon Water Reminder → **Quit**
- Atau saat testing di terminal, tekan `Ctrl + C`

Jika proses stuck, bisa paksa stop:

```bash
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

---

## Konfigurasi Utama di `app.py`

Beberapa variabel penting yang bisa disesuaikan:

### Interval reminder normal

```python
NORMAL_INTERVAL_MS = 30 * 60 * 1000
```

Artinya reminder muncul setiap 30 menit setelah user klik **Sudah minum**.

Untuk testing cepat:

```python
NORMAL_INTERVAL_MS = 30 * 1000
```

### Interval snooze

```python
SNOOZE_INTERVAL_MS = 10 * 60 * 1000
```

Artinya jika user klik **Snooze**, reminder akan muncul lagi 10 menit kemudian.

Untuk testing cepat:

```python
SNOOZE_INTERVAL_MS = 10 * 1000
```

### Ukuran tampilan GIF

```python
DISPLAY_WIDTH = 600
```

Jika karakter terlalu kecil, naikkan:

```python
DISPLAY_WIDTH = 700
```

Jika terasa berat atau lag, turunkan:

```python
DISPLAY_WIDTH = 500
```

### Frame pause saat karakter sampai tengah

```python
HOLD_FRAME = 50
```

Ini adalah frame ketika karakter berhenti dan pertanyaan muncul.

Jika pertanyaan muncul terlalu cepat:

```python
HOLD_FRAME = 60
```

Jika pertanyaan muncul terlalu lambat:

```python
HOLD_FRAME = 40
```

### Frame mulai jalan keluar saat snooze

```python
WALK_OUT_FRAME = 130
```

Ini frame yang dipakai ketika user klik **Snooze**, supaya karakter langsung lanjut ke animasi pergi/back tanpa minum.

Jika saat snooze masih sempat masuk animasi minum, naikkan nilainya.

Jika saat snooze langsung hilang, turunkan nilainya.

### Debug frame

```python
DEBUG_FRAMES = False
```

Gunakan `True` hanya saat mencari frame yang pas.

```python
DEBUG_FRAMES = True
```

Setelah selesai setting, kembalikan ke:

```python
DEBUG_FRAMES = False
```

Catatan: debug frame bisa membuat terminal penuh dan aplikasi terasa lag.

### Popup Horeee

```python
CELEBRATION_DURATION_MS = 1500
```

Artinya popup “Horeee” muncul selama 1.5 detik.

### Warning jika terlalu sering snooze

```python
SNOOZE_WARNING_THRESHOLD = 3
```

Artinya warning mulai muncul saat user menekan snooze ke-3 dan seterusnya.

Alur yang dipakai:

```text
Klik Snooze pertama  → reminder lagi 10 menit
Klik Snooze kedua    → reminder lagi 10 menit
Klik Snooze ketiga   → muncul warning, lalu reminder lagi 10 menit
Klik Snooze keempat  → warning makin tegas, lalu reminder lagi 10 menit
Klik Sudah minum     → snooze counter reset ke 0, balik ke 30 menit
```

### Muncul saat app pertama dibuka

```python
SHOW_ON_START = False
```

Jika `False`, aplikasi tidak langsung muncul saat startup. Dia langsung menghitung 30 menit.

Jika ingin muncul langsung untuk testing:

```python
SHOW_ON_START = True
```

Untuk mode final/startup, disarankan:

```python
SHOW_ON_START = False
```

---

## Auto Run Saat Windows Startup

Agar aplikasi berjalan otomatis saat laptop menyala, gunakan file VBS.

Buat file:

```text
start_water_reminder.vbs
```

Isi:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\water-reminder"
WshShell.Run """E:\water-reminder\venv\Scripts\pythonw.exe"" ""E:\water-reminder\app.py""", 0, False
```

Sesuaikan path jika folder project berbeda.

Yang penting gunakan:

```text
pythonw.exe
```

bukan:

```text
python.exe
```

Karena `pythonw.exe` menjalankan app tanpa terminal.

---

## Menambahkan ke Startup Folder

Tekan:

```text
Win + R
```

Ketik:

```text
shell:startup
```

Lalu tekan Enter.

Copy file atau shortcut berikut ke folder Startup:

```text
start_water_reminder.vbs
```

Setelah itu, aplikasi akan otomatis berjalan saat Windows login.

---

## Cara Test Startup Tanpa Restart

Double click langsung file:

```text
start_water_reminder.vbs
```

Jika benar, tidak akan muncul terminal.

Cek kanan bawah taskbar/tray icon. Harusnya ada icon aplikasi Water Reminder.

Jika terminal masih muncul, kemungkinan:

- Yang dijalankan masih `python.exe`, bukan `pythonw.exe`.
- Shortcut Startup masih mengarah ke `app.py`.
- Masih ada proses lama dari `python app.py`.

Stop proses lama:

```bash
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

Lalu jalankan ulang `.vbs`.

---

## Build ke EXE Opsional

Jika ingin dibuat menjadi aplikasi `.exe`, install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --noconsole --onefile --add-data "target_transparent.gif;." app.py
```

Hasil `.exe` ada di folder:

```text
dist/
```

Untuk mode `.exe`, Startup bisa diarahkan ke file `.exe` tersebut.

---

## Troubleshooting

### Terminal masih muncul

Pastikan file startup menjalankan:

```text
pythonw.exe
```

bukan:

```text
python.exe
```

### Karakter terlalu kecil

Ubah:

```python
DISPLAY_WIDTH = 600
```

menjadi:

```python
DISPLAY_WIDTH = 700
```

### Aplikasi terasa lag

Coba:

```python
DISPLAY_WIDTH = 500
DEBUG_FRAMES = False
```

Kurangi ukuran GIF atau jumlah frame GIF.

### Snooze tidak lanjut animasi

Pastikan di fungsi snooze ada:

```python
self.movie.setPaused(False)
self.movie.start()
```

### GIF background masih terlihat

Jalankan ulang:

```bash
python make_transparent.py
```

Lalu cek `TOLERANCE` di `make_transparent.py`.

### Aplikasi tidak muncul saat startup

Cek:

1. File `.vbs` sudah ada di folder startup.
2. Path di `.vbs` sudah benar.
3. Virtual environment masih ada.
4. `target_transparent.gif` ada di folder project.
5. Coba double click `.vbs` secara manual.

---

## Alur Final Aplikasi

```text
Windows login
→ app berjalan di background
→ menunggu 30 menit
→ karakter muncul
→ karakter jalan ke tengah
→ pertanyaan muncul

Jika klik Sudah minum:
→ popup Horeee 1.5 detik
→ animasi minum lanjut sampai selesai
→ app hilang
→ reminder berikutnya 30 menit lagi

Jika klik Snooze:
→ karakter pergi/back
→ app hilang
→ reminder berikutnya 10 menit lagi

Jika user snooze terus:
→ counter snooze bertambah
→ mulai snooze ke-3 muncul warning
→ counter reset setelah user klik Sudah minum
```

---

## Catatan Best Practice

Untuk versi final:

```python
NORMAL_INTERVAL_MS = 30 * 60 * 1000
SNOOZE_INTERVAL_MS = 10 * 60 * 1000
DEBUG_FRAMES = False
SHOW_ON_START = False
```

Untuk testing:

```python
NORMAL_INTERVAL_MS = 30 * 1000
SNOOZE_INTERVAL_MS = 10 * 1000
DEBUG_FRAMES = True
SHOW_ON_START = True
```
