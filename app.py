from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "ganti-dengan-secret-key-anda"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Maksimal 5 MB

UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def predict_freshness(image_path):
    """
    TEMPAT INTEGRASI MODEL CNN.

    Hubungkan model klasifikasi Anda di fungsi ini.
    Fungsi diharapkan mengembalikan:
        {
            "label": "Segar" atau "Busuk",
            "confidence": 96.7
        }

    Contoh alur integrasi:
      1. Load model yang sudah dilatih.
      2. Preprocessing gambar sesuai preprocessing saat training.
      3. Jalankan prediksi.
      4. Ubah output model menjadi label Segar/Busuk dan confidence.

    Untuk mencegah hasil palsu, fungsi ini belum memberikan prediksi dummy.
    """
    raise NotImplementedError("Model CNN belum dihubungkan.")


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

    safe_name = secure_filename(image.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    image_path = UPLOAD_FOLDER / filename
    image.save(image_path)

    try:
        result = predict_freshness(str(image_path))
        label = result["label"]
        confidence = float(result["confidence"])

        if label not in {"Segar", "Busuk"}:
            raise ValueError("Label model harus 'Segar' atau 'Busuk'.")

        return jsonify({
            "label": label,
            "confidence": round(confidence, 2),
            "image_url": url_for("static", filename=f"uploads/{filename}")
        })
    except NotImplementedError:
        return jsonify({
            "error": "Tampilan upload sudah siap, tetapi model CNN belum dihubungkan. Hubungkan model pada fungsi predict_freshness() di app.py."
        }), 501
    except Exception as exc:
        app.logger.exception("Terjadi kesalahan saat prediksi")
        return jsonify({"error": f"Prediksi gagal: {str(exc)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
