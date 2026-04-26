# SalstudioZ — Sistem Cerdas
### Responsi 1 Praktikum KB

Dua aplikasi web berbasis Flask:

| Sistem | Folder | Port | URL |
|---|---|---|---|
| **SalstudioZ.Fuzzy** (Logika Fuzzy Mamdani) | `fuzzy/` | 5001 | http://localhost:5001 |
| **SalstudioZ.Pakar** (Sistem Pakar Forward Chaining) | `pakar/` | 5002 | http://localhost:5002 |

---

## Struktur Direktori

```
fuzzy/
├── app.py              Flask app (port 5001)
├── fuzzy_logic.py      Engine Mamdani: fuzzify → evaluate → defuzzify
├── requirements.txt
├── logs/               Log request (dibuat otomatis)
├── static/style.css
├── templates/index.html
└── tests/test_fuzzy.py

pakar/
├── app.py              Flask app (port 5002)
├── knowledge_base.py   16 aturan + 17 gejala
├── inference.py        Forward chaining iteratif
├── requirements.txt
├── logs/
├── static/style.css
├── templates/index.html
└── tests/test_expert.py
```

---

## Cara Menjalankan

### Terminal 1 — SalstudioZ.Fuzzy

```bash
cd fuzzy
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# → http://localhost:5001
```

### Terminal 2 — SalstudioZ.Pakar

```bash
cd pakar
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://localhost:5002
```

---

## Unit Test

```bash
# Fuzzy
cd fuzzy && pytest tests/ -v     # 39 tests

# Pakar
cd pakar && pytest tests/ -v     # 31 tests
```

---

## API

### SalstudioZ.Fuzzy  `POST /calculate`

```json
{ "jenis_bahan": "sayur_daun", "lama_simpan": 7, "kelembaban_ruangan": 55 }
```
Response: `{ "suhu": 3.2, "rh": 72.5, "suhu_label": "Sangat Dingin", "rh_label": "Tinggi", "suhu_set": {...}, "rh_set": {...} }`

### SalstudioZ.Pakar  `POST /diagnose`

```json
{ "symptoms": ["sayur_layu", "tepi_kecoklatan", "suhu_kulkas_diatas_5"] }
```
Response: `{ "diagnoses": [ { "rule_id": 1, "diagnosis": "...", "saran": "..." } ] }`

---

## Stack

- **Backend**: Python 3.10+, Flask 3.0, NumPy
- **Frontend**: HTML5, CSS3 (Grid/Flexbox + CSS Variables), Vanilla JS
- **Font**: Syne + DM Sans (Fuzzy) · Archivo + Instrument Sans (Pakar)
- **Icons**: Font Awesome 6
- **Test**: pytest
