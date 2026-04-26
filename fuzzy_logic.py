"""
Fuzzy Logic System (Mamdani) for Food/Skincare Storage Temperature & Humidity
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Membership Function Classes
# ─────────────────────────────────────────

class MembershipFunction:
    """Menyimpan dan menghitung nilai keanggotaan untuk himpunan fuzzy."""

    @staticmethod
    def triangular(x: float, a: float, b: float, c: float) -> float:
        """Fungsi keanggotaan segitiga dengan puncak di b, nol di a dan c."""
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        else:
            return (c - x) / (c - b)

    @staticmethod
    def trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:
        """Fungsi keanggotaan trapesium, nilai 1 di antara b dan c."""
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        elif b < x <= c:
            return 1.0
        else:
            return (d - x) / (d - c)

    @staticmethod
    def singleton(x: float, center: float, tolerance: float = 0.5) -> float:
        """Singleton (untuk nilai kategorikal), gaussian sempit."""
        return max(0.0, 1.0 - abs(x - center) / tolerance)


# ─────────────────────────────────────────
# Universe of Discourse
# ─────────────────────────────────────────

# Jenis bahan: nilai numerik yang mewakili kategori
JENIS_MAP = {
    "sayur_daun":   0.0,
    "sayur_buah":   0.2,
    "daging_segar": 0.4,
    "susu_olahan":  0.6,
    "herbal_kering":0.8,
    "skincare":     1.0,
}

MF = MembershipFunction()

def _jenis_mf(x: float) -> dict:
    return {
        "sayur_daun":    MF.singleton(x, 0.0, 0.15),
        "sayur_buah":    MF.singleton(x, 0.2, 0.15),
        "daging_segar":  MF.singleton(x, 0.4, 0.15),
        "susu_olahan":   MF.singleton(x, 0.6, 0.15),
        "herbal_kering": MF.singleton(x, 0.8, 0.15),
        "skincare":      MF.singleton(x, 1.0, 0.15),
    }

def _lama_mf(x: float) -> dict:
    return {
        "sangat_singkat": MF.trapezoid(x, 0, 1, 2, 3),
        "singkat":        MF.triangular(x, 2, 3.5, 5),
        "sedang":         MF.trapezoid(x, 4, 5, 7, 8),
        "panjang":        MF.trapezoid(x, 7, 9, 14, 15),
    }

def _kelembaban_ruangan_mf(x: float) -> dict:
    return {
        "kering":  MF.trapezoid(x, 29, 30, 42, 50),
        "normal":  MF.triangular(x, 42, 55, 68),
        "lembab":  MF.trapezoid(x, 60, 68, 80, 81),
    }

# ─────────────────────────────────────────
# Output membership functions (untuk defuzzifikasi centroid)
# ─────────────────────────────────────────

SUHU_UNIVERSE = np.arange(0, 25.1, 0.1)
RH_UNIVERSE   = np.arange(30, 85.5, 0.5)

def _suhu_mf_output(x_arr):
    """Himpunan fuzzy output suhu."""
    return {
        "sangat_dingin": np.vectorize(lambda x: MF.trapezoid(x, -1, 0, 3, 5))(x_arr),
        "dingin":        np.vectorize(lambda x: MF.triangular(x, 3, 6, 9))(x_arr),
        "sejuk":         np.vectorize(lambda x: MF.triangular(x, 7, 10, 14))(x_arr),
        "sedang":        np.vectorize(lambda x: MF.triangular(x, 12, 16, 20))(x_arr),
        "ruang":         np.vectorize(lambda x: MF.trapezoid(x, 18, 21, 25, 26))(x_arr),
    }

def _rh_mf_output(x_arr):
    """Himpunan fuzzy output kelembaban ideal."""
    return {
        "rendah":  np.vectorize(lambda x: MF.trapezoid(x, 29, 30, 42, 52))(x_arr),
        "sedang":  np.vectorize(lambda x: MF.triangular(x, 42, 55, 68))(x_arr),
        "tinggi":  np.vectorize(lambda x: MF.trapezoid(x, 60, 68, 85, 86))(x_arr),
    }

# ─────────────────────────────────────────
# Rule Base
# ─────────────────────────────────────────

class FuzzyRule:
    def __init__(self, rule_id: int, conditions: dict, suhu_label: str, rh_label: str):
        self.rule_id   = rule_id
        self.conditions = conditions   # {input_var: fuzzy_set}
        self.suhu_label = suhu_label
        self.rh_label   = rh_label

    def fire_strength(self, fuzzified: dict) -> float:
        """Hitung kekuatan aturan dengan operator AND (MIN)."""
        strength = 1.0
        for var, fuzzy_set in self.conditions.items():
            val = fuzzified.get(var, {}).get(fuzzy_set, 0.0)
            strength = min(strength, val)
        return strength


RULES = [
    # ── Sayur Daun ──
    FuzzyRule(1,  {"jenis": "sayur_daun",    "lama": "sangat_singkat"},                          "dingin",        "tinggi"),
    FuzzyRule(2,  {"jenis": "sayur_daun",    "lama": "singkat"},                                  "dingin",        "tinggi"),
    FuzzyRule(3,  {"jenis": "sayur_daun",    "lama": "sedang"},                                   "sangat_dingin", "tinggi"),
    FuzzyRule(4,  {"jenis": "sayur_daun",    "lama": "panjang"},                                  "sangat_dingin", "tinggi"),
    # ── Sayur Buah ──
    FuzzyRule(5,  {"jenis": "sayur_buah",    "lama": "sangat_singkat"},                           "dingin",        "sedang"),
    FuzzyRule(6,  {"jenis": "sayur_buah",    "lama": "singkat"},                                  "dingin",        "sedang"),
    FuzzyRule(7,  {"jenis": "sayur_buah",    "lama": "sedang"},                                   "sangat_dingin", "sedang"),
    FuzzyRule(8,  {"jenis": "sayur_buah",    "lama": "panjang"},                                  "sangat_dingin", "rendah"),
    # ── Daging Segar ──
    FuzzyRule(9,  {"jenis": "daging_segar",  "lama": "sangat_singkat"},                           "sangat_dingin", "rendah"),
    FuzzyRule(10, {"jenis": "daging_segar",  "lama": "singkat"},                                  "sangat_dingin", "rendah"),
    FuzzyRule(11, {"jenis": "daging_segar",  "lama": "sedang"},                                   "sangat_dingin", "rendah"),
    FuzzyRule(12, {"jenis": "daging_segar",  "lama": "panjang"},                                  "sangat_dingin", "rendah"),
    # ── Susu Olahan ──
    FuzzyRule(13, {"jenis": "susu_olahan",   "lama": "sangat_singkat"},                           "sangat_dingin", "sedang"),
    FuzzyRule(14, {"jenis": "susu_olahan",   "lama": "singkat"},                                  "sangat_dingin", "sedang"),
    FuzzyRule(15, {"jenis": "susu_olahan",   "lama": "sedang"},                                   "sangat_dingin", "rendah"),
    FuzzyRule(16, {"jenis": "susu_olahan",   "lama": "panjang"},                                  "dingin",        "rendah"),
    # ── Herbal Kering ──
    FuzzyRule(17, {"jenis": "herbal_kering", "kelembaban_ruangan": "kering"},                     "sejuk",         "rendah"),
    FuzzyRule(18, {"jenis": "herbal_kering", "kelembaban_ruangan": "normal"},                     "sejuk",         "rendah"),
    FuzzyRule(19, {"jenis": "herbal_kering", "kelembaban_ruangan": "lembab"},                     "sejuk",         "rendah"),
    FuzzyRule(20, {"jenis": "herbal_kering", "lama": "panjang"},                                  "sejuk",         "rendah"),
    # ── Skincare ──
    FuzzyRule(21, {"jenis": "skincare",      "kelembaban_ruangan": "kering"},                     "ruang",         "rendah"),
    FuzzyRule(22, {"jenis": "skincare",      "kelembaban_ruangan": "normal"},                     "ruang",         "rendah"),
    FuzzyRule(23, {"jenis": "skincare",      "kelembaban_ruangan": "lembab"},                     "ruang",         "rendah"),
    FuzzyRule(24, {"jenis": "skincare",      "lama": "panjang"},                                  "ruang",         "rendah"),
    FuzzyRule(25, {"jenis": "skincare",      "lama": "singkat"},                                  "sejuk",         "rendah"),
    # ── Kelembaban ruangan lembab (lintas bahan) ──
    FuzzyRule(26, {"jenis": "sayur_daun",    "kelembaban_ruangan": "lembab"},                     "sangat_dingin", "tinggi"),
    FuzzyRule(27, {"jenis": "daging_segar",  "kelembaban_ruangan": "lembab"},                     "sangat_dingin", "rendah"),
    FuzzyRule(28, {"jenis": "susu_olahan",   "kelembaban_ruangan": "lembab"},                     "sangat_dingin", "rendah"),
]


# ─────────────────────────────────────────
# Fuzzification
# ─────────────────────────────────────────

def fuzzify(jenis_bahan: str, lama_simpan: float, kelembaban_ruangan: float) -> dict:
    """Ubah nilai crisp menjadi derajat keanggotaan fuzzy."""
    jenis_val = JENIS_MAP[jenis_bahan]
    return {
        "jenis":               _jenis_mf(jenis_val),
        "lama":                _lama_mf(lama_simpan),
        "kelembaban_ruangan":  _kelembaban_ruangan_mf(kelembaban_ruangan),
    }


# ─────────────────────────────────────────
# Rule Evaluation
# ─────────────────────────────────────────

def evaluate_rules(fuzzified: dict) -> dict:
    """
    Evaluasi semua aturan, kembalikan kekuatan tiap aturan.
    Agregasi: MAX per himpunan output.
    """
    agg_suhu = {"sangat_dingin": 0.0, "dingin": 0.0, "sejuk": 0.0, "sedang": 0.0, "ruang": 0.0}
    agg_rh   = {"rendah": 0.0, "sedang": 0.0, "tinggi": 0.0}

    for rule in RULES:
        strength = rule.fire_strength(fuzzified)
        if strength > 0:
            agg_suhu[rule.suhu_label] = max(agg_suhu[rule.suhu_label], strength)
            agg_rh[rule.rh_label]     = max(agg_rh[rule.rh_label],     strength)
            logger.debug(f"Rule {rule.rule_id} fired with strength {strength:.3f} → {rule.suhu_label}/{rule.rh_label}")

    return {"suhu": agg_suhu, "rh": agg_rh}


# ─────────────────────────────────────────
# Defuzzification (Centroid)
# ─────────────────────────────────────────

def defuzzify(aggregated: dict) -> dict:
    """Defuzzifikasi centroid untuk suhu dan kelembaban."""
    # — Suhu —
    suhu_mfs = _suhu_mf_output(SUHU_UNIVERSE)
    suhu_agg_arr = np.zeros_like(SUHU_UNIVERSE)
    for label, strength in aggregated["suhu"].items():
        if strength > 0:
            clipped = np.minimum(suhu_mfs[label], strength)
            suhu_agg_arr = np.maximum(suhu_agg_arr, clipped)

    denom_s = np.sum(suhu_agg_arr)
    suhu_crisp = float(np.sum(SUHU_UNIVERSE * suhu_agg_arr) / denom_s) if denom_s > 0 else 4.0

    # — RH —
    rh_mfs = _rh_mf_output(RH_UNIVERSE)
    rh_agg_arr = np.zeros_like(RH_UNIVERSE)
    for label, strength in aggregated["rh"].items():
        if strength > 0:
            clipped = np.minimum(rh_mfs[label], strength)
            rh_agg_arr = np.maximum(rh_agg_arr, clipped)

    denom_r = np.sum(rh_agg_arr)
    rh_crisp = float(np.sum(RH_UNIVERSE * rh_agg_arr) / denom_r) if denom_r > 0 else 55.0

    # — Label —
    def suhu_label(v):
        if v < 4:   return "Sangat Dingin"
        if v < 8:   return "Dingin"
        if v < 14:  return "Sejuk"
        if v < 20:  return "Sedang"
        return "Suhu Ruang"

    def rh_label(v):
        if v < 50:  return "Rendah"
        if v < 68:  return "Sedang"
        return "Tinggi"

    return {
        "suhu":      round(suhu_crisp, 1),
        "rh":        round(rh_crisp, 1),
        "suhu_label": suhu_label(suhu_crisp),
        "rh_label":   rh_label(rh_crisp),
        "suhu_set":   aggregated["suhu"],
        "rh_set":     aggregated["rh"],
    }


# ─────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────

def run_fuzzy(jenis_bahan: str, lama_simpan: float, kelembaban_ruangan: float = 50.0) -> dict:
    """Jalankan seluruh pipeline fuzzy dan kembalikan hasil."""
    fuzzified  = fuzzify(jenis_bahan, lama_simpan, kelembaban_ruangan)
    aggregated = evaluate_rules(fuzzified)
    result     = defuzzify(aggregated)
    logger.info(
        f"run_fuzzy: jenis={jenis_bahan}, lama={lama_simpan}, kelembaban={kelembaban_ruangan} "
        f"→ suhu={result['suhu']}°C ({result['suhu_label']}), rh={result['rh']}% ({result['rh_label']})"
    )
    return result
