"""
Flask Application – SalstudioZ.Fuzzy
"""
import os, logging, logging.handlers
from flask import Flask, render_template, request, jsonify
from fuzzy_logic import run_fuzzy, JENIS_MAP

app = Flask(__name__)
os.makedirs("logs", exist_ok=True)
handler = logging.handlers.RotatingFileHandler("logs/fuzzy.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()])
logger = logging.getLogger(__name__)
VALID_JENIS = list(JENIS_MAP.keys())

@app.route("/")
def index():
    return render_template("index.html", jenis_list=VALID_JENIS)

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json(force=True)
        if data is None:
            return jsonify({"error": "Body harus berupa JSON."}), 400
        jenis_bahan = data.get("jenis_bahan", "")
        if jenis_bahan not in VALID_JENIS:
            return jsonify({"error": f"jenis_bahan tidak valid. Pilih dari: {VALID_JENIS}"}), 400
        try:
            lama_simpan = float(data["lama_simpan"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "lama_simpan harus berupa angka."}), 400
        if not (1 <= lama_simpan <= 14):
            return jsonify({"error": "lama_simpan harus antara 1 dan 14."}), 400
        if "kelembaban_ruangan" in data and data["kelembaban_ruangan"] is not None:
            try:
                kelembaban_ruangan = float(data["kelembaban_ruangan"])
            except (TypeError, ValueError):
                return jsonify({"error": "kelembaban_ruangan harus berupa angka."}), 400
            if not (30 <= kelembaban_ruangan <= 80):
                return jsonify({"error": "kelembaban_ruangan harus antara 30 dan 80."}), 400
        else:
            kelembaban_ruangan = 50.0
        logger.info(f"POST /calculate – jenis={jenis_bahan}, lama={lama_simpan}, kelembaban={kelembaban_ruangan} | IP={request.remote_addr}")
        result = run_fuzzy(jenis_bahan, lama_simpan, kelembaban_ruangan)
        return jsonify(result), 200
    except Exception as exc:
        logger.exception(f"Error di /calculate: {exc}")
        return jsonify({"error": "Terjadi kesalahan internal."}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5001)
