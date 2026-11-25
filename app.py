import io
import json
import os
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import numpy as np
from flask import Flask, render_template, request, jsonify, url_for
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

# Backend Keras ringan (CPU) agar bundle Vercel tetap di bawah batas ukuran.
# TensorFlow tidak diperlukan untuk inference model .keras ini.
os.environ.setdefault("KERAS_BACKEND", "jax")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ganti-dengan-secret-key-anda")
# Batas body request Vercel Functions adalah 4,5 MB.
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # Maksimal 4 MB

UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
try:
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
except OSError:
    # Filesystem Vercel bersifat read-only; upload tidak disimpan di sana.
    pass
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

MODEL_DIR = Path(app.root_path) / "model"
MODEL_PATH = MODEL_DIR / "best_mobilenetv2_fruit.keras"
LABELS_PATH = MODEL_DIR / "labels.json"

IMAGE_SIZE = (224, 224)
CONFIDENCE_THRESHOLD = 0.80

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@lru_cache(maxsize=1)
def load_labels() -> dict:
    with LABELS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_model():
    """Muat model sekali, lalu pakai ulang untuk setiap permintaan."""
    try:
        from keras.models import load_model
    except ImportError as exc:
        raise RuntimeError(
            "Keras belum terpasang. Jalankan: pip install -r requirements.txt"
        ) from exc

    if not MODEL_PATH.exists():
        raise RuntimeError(f"File model tidak ditemukan: {MODEL_PATH}")

    return load_model(MODEL_PATH)


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    # 1. Buka gambar & perbaiki rotasi EXIF kamera HP
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)

    # 2. Pastikan 3 channel RGB (buang alpha channel RGBA jika ada)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 3. Direct resize ke 224x224 sesuai pipeline training Keras
    img = img.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)

    # 4. Ubah ke float32 rentang [0, 255] & tambah dimensi batch -> (1, 224, 224, 3)
    img_array = np.asarray(img, dtype=np.float32)
    return np.expand_dims(img_array, axis=0)


def predict_freshness(image_bytes: bytes) -> dict:
    labels = load_labels()

    # Inferensi (data_augmentation otomatis bypass, preprocess_input jalan otomatis)
    probs = get_model().predict(preprocess_image(image_bytes), verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    confidence = float(probs[pred_idx])
    raw_label = labels[str(pred_idx)]  # Contoh: "FreshApple" atau "RottenBanana"

    # Pisahkan status kesegaran dan jenis buah untuk respons UI yang bersih
    is_fresh = raw_label.startswith("Fresh")
    fruit_type = raw_label.replace("Fresh", "").replace("Rotten", "")

    return {
        "predicted_class": raw_label,
        "fruit": fruit_type,
        "status": "Segar" if is_fresh else "Busuk",
        "confidence": confidence,
        "is_uncertain": confidence < CONFIDENCE_THRESHOLD,
        "all_probabilities": {
            labels[str(i)]: round(float(prob), 4) for i, prob in enumerate(probs)
        },
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Silakan pilih gambar terlebih dahulu."}), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({"error": "Belum ada gambar yang dipilih."}), 400

    if not allowed_file(image.filename):
        return jsonify({"error": "Format file harus JPG, JPEG, atau PNG."}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"error": "File gambar kosong."}), 400

    safe_name = secure_filename(image.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    image_path = UPLOAD_FOLDER / filename

    # Simpan salinan hanya jika filesystem writable (tidak pada Vercel).
    image_url = None
    try:
        image_path.write_bytes(image_bytes)
        image_url = url_for("static", filename=f"uploads/{filename}")
    except OSError:
        app.logger.info("Upload folder tidak writable; lewati penyimpanan salinan gambar.")

    try:
        result = predict_freshness(image_bytes)

        return jsonify({
            # Format yang dipakai frontend: label Segar/Busuk, confidence dalam persen
            "label": result["status"],
            "confidence": round(result["confidence"] * 100, 2),
            "fruit": result["fruit"],
            "predicted_class": result["predicted_class"],
            "is_uncertain": result["is_uncertain"],
            "all_probabilities": result["all_probabilities"],
            "image_url": image_url
        })
    except Exception as exc:
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            pass
        app.logger.exception("Terjadi kesalahan saat prediksi")
        return jsonify({"error": f"Prediksi gagal: {str(exc)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
