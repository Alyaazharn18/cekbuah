# CekBuah – Flask + MobileNetV2

Aplikasi web klasifikasi kesegaran buah (Apel, Pisang, Jeruk → Segar/Busuk)
menggunakan model `MobileNetV2` yang sudah dilatih. Siap dijalankan lokal
maupun di-deploy ke Vercel.

## Struktur folder

```text
cekbuah_flask/
├── app.py
├── requirements.txt
├── vercel.json          # konfigurasi function Vercel
├── .vercelignore        # file yang tidak ikut di-upload
├── .python-version      # Python 3.12 di Vercel
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

## Menjalankan lokal

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

## Deploy ke Vercel

1. Pastikan semua perubahan sudah ter-commit dan tersedia di repository Git.
2. Import repository ke Vercel (Add New → Project). Vercel akan mendeteksi
   Flask dari `requirements.txt` dan menjadikan `app.py` sebagai entrypoint.
3. Klik **Deploy**. Atau lewat CLI:
   ```bash
   npm i -g vercel
   vercel --prod
   ```
4. Set environment variable `SECRET_KEY` di Project Settings → Environment
   Variables (opsional, untuk mengganti nilai default).

Catatan deployment:

- `vercel.json` mengatur `maxDuration: 60` detik dan memastikan folder
  `model/`, `templates/`, dan `static/` ikut ter-bundle. File `.keras`
  (sekitar 24 MB) tidak perlu disimpan di Vercel Blob.
- Backend Keras yang dipakai adalah **JAX CPU** (`KERAS_BACKEND=jax`,
  di-set otomatis di `app.py`). Ini jauh lebih ringan daripada TensorFlow
  sehingga bundle tetap di bawah batas 500 MB untuk Python di Vercel.
- Batas body request Vercel adalah 4,5 MB, jadi upload dibatasi **4 MB**
  (depan dan belakang). Untuk gambar lebih besar, kompres dulu sebelum
  di-unggah.
- Filesystem function bersifat read-only. Di Vercel, gambar tidak disimpan
  ke `static/uploads/`, sehingga `image_url` bernilai `null`. Pratinjau di
  UI tetap memakai object URL dari browser.
- Prediksi pertama setelah cold start bisa memakan beberapa detik karena
  model harus dimuat; permintaan berikutnya dalam instance yang sama lebih
  cepat.

## Endpoint `/predict`

- Method: `POST`, field form-data: `image` (JPG/JPEG/PNG, maks. 4 MB).
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
`image_url` bernilai `null` saat di-deploy di Vercel.

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
