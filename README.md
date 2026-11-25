# CekBuah – Flask Starter

Template awal aplikasi web untuk klasifikasi kesegaran buah dengan dua kelas: **Segar** dan **Busuk**.

## Struktur folder

```text
cekbuah_flask/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/app.js
    └── uploads/
```

## Menjalankan aplikasi

1. Buka terminal pada folder proyek.
2. Buat virtual environment (opsional tetapi disarankan):
   ```bash
   python -m venv venv
   ```
3. Aktifkan environment:
   - Windows: `venv\\Scripts\\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan:
   ```bash
   python app.py
   ```
6. Buka `http://127.0.0.1:5000` pada browser.

## Mode demo frontend

Saat ini alur **unggah gambar → prediksi → hasil** dapat dicoba tanpa model CNN. Di `static/js/app.js`, baris paling atas berisi:

```js
const DEMO_MODE = true;
```

Hasil yang ditampilkan adalah contoh. Setelah model CNN dihubungkan pada `predict_freshness(image_path)`, ubah menjadi `const DEMO_MODE = false;` agar tombol Prediksi memanggil endpoint `/predict`.

## Integrasi model

Endpoint `/predict` sudah menerima file, memeriksa format dan ukuran, lalu menyimpan gambar di `static/uploads/`.

Model belum disambungkan. Letakkan kode pemuatan model, preprocessing, dan inferensi pada fungsi `predict_freshness(image_path)` di `app.py`. Fungsi tersebut harus mengembalikan dictionary seperti:

```python
{"label": "Segar", "confidence": 96.7}
```

Nilai di atas hanya contoh format respons, bukan hasil model. Jangan gunakan confidence contoh sebagai hasil prediksi sungguhan.
