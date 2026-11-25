# CekBuah – Flask + MobileNetV2

Aplikasi web klasifikasi kesegaran buah (Apel, Pisang, Jeruk → Segar/Busuk)
menggunakan model `MobileNetV2` yang sudah dilatih.

## Struktur folder

```text
cekbuah_flask/
├── app.py
├── requirements.txt
├── model/
│   ├── best_mobilenetv2_fruit.keras
│   └── labels.json
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
   - Windows: `venv\Scripts\activate`
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

Model dimuat lazily saat prediksi pertama dan disimpan di memori untuk
permintaan berikutnya, sehingga startup server tetap cepat.

## Endpoint `/predict`

- Method: `POST`, field form-data: `image` (JPG/JPEG/PNG, maks. 5 MB).
- Contoh respons:

```json
{
  "label": "Segar",
  "confidence": 97.42,
  "fruit": "Apple",
  "predicted_class": "FreshApple",
  "is_uncertain": false,
  "all_probabilities": { "FreshApple": 0.9742, "...": 0.0 },
  "image_url": "/static/uploads/<nama>.jpg"
}
```

`confidence` dikirim dalam persen (0–100) agar sesuai dengan tampilan UI;
`is_uncertain` bernilai `true` jika confidence model di bawah 0,80.

Preprocessing di `preprocess_image()` mengikuti pipeline training:
EXIF transpose → RGB → resize 224×224 (bilinear) → `float32` [0, 255].
Layer `preprocess_input` sudah tertanam di dalam file `.keras`, jadi tidak
perlu dipanggil manual.

## Mode demo frontend

Jika ingin mencoba tampilan tanpa model, ubah di `static/js/app.js`:

```js
const DEMO_MODE = true;
```

Nilai bawaan adalah `false`, sehingga tombol Prediksi memanggil endpoint
`/predict` dan memakai hasil model sungguhan.
