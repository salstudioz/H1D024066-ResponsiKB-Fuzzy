"""
Unit Tests – Sistem Fuzzy Logika Mamdani
Jalankan dengan: pytest tests/ -v
"""
import pytest
from fuzzy_logic import (
    MembershipFunction, fuzzify, evaluate_rules, defuzzify, run_fuzzy, JENIS_MAP
)

MF = MembershipFunction()

# ─────────────────────────────────────────
# Membership Function Tests
# ─────────────────────────────────────────

class TestMembershipFunction:
    def test_triangular_peak(self):
        assert MF.triangular(6, 4, 6, 8) == pytest.approx(1.0)

    def test_triangular_zero_at_edges(self):
        assert MF.triangular(4, 4, 6, 8) == pytest.approx(0.0)
        assert MF.triangular(8, 4, 6, 8) == pytest.approx(0.0)

    def test_triangular_midpoint_left(self):
        assert MF.triangular(5, 4, 6, 8) == pytest.approx(0.5)

    def test_triangular_outside_range(self):
        assert MF.triangular(0, 4, 6, 8) == 0.0
        assert MF.triangular(10, 4, 6, 8) == 0.0

    def test_trapezoid_flat_top(self):
        assert MF.trapezoid(5, 2, 4, 6, 8) == pytest.approx(1.0)
        assert MF.trapezoid(4.5, 2, 4, 6, 8) == pytest.approx(1.0)

    def test_trapezoid_zero_outside(self):
        assert MF.trapezoid(1, 2, 4, 6, 8) == 0.0
        assert MF.trapezoid(9, 2, 4, 6, 8) == 0.0

    def test_trapezoid_left_slope(self):
        assert MF.trapezoid(3, 2, 4, 6, 8) == pytest.approx(0.5)

    def test_trapezoid_right_slope(self):
        assert MF.trapezoid(7, 2, 4, 6, 8) == pytest.approx(0.5)

    def test_singleton_center(self):
        assert MF.singleton(0.0, 0.0) == pytest.approx(1.0)

    def test_singleton_far(self):
        assert MF.singleton(1.0, 0.0) < 0.01


# ─────────────────────────────────────────
# Fuzzification Tests
# ─────────────────────────────────────────

class TestFuzzify:
    def test_returns_all_variables(self):
        result = fuzzify("sayur_daun", 3, 50)
        assert "jenis" in result
        assert "lama" in result
        assert "kelembaban_ruangan" in result

    def test_jenis_sayur_daun_dominant(self):
        result = fuzzify("sayur_daun", 3, 50)
        j = result["jenis"]
        assert j["sayur_daun"] > j["skincare"]
        assert j["sayur_daun"] > j["daging_segar"]

    def test_lama_singkat_dominant(self):
        result = fuzzify("sayur_daun", 3, 50)
        l = result["lama"]
        # hari 3 → singkat atau sangat_singkat dominan
        assert l["singkat"] > l["panjang"]

    def test_lama_panjang_at_14(self):
        result = fuzzify("sayur_daun", 14, 50)
        l = result["lama"]
        assert l["panjang"] > 0.5

    def test_kelembaban_normal(self):
        result = fuzzify("sayur_daun", 5, 55)
        k = result["kelembaban_ruangan"]
        assert k["normal"] >= k["kering"]
        assert k["normal"] >= k["lembab"]

    def test_kelembaban_lembab_at_75(self):
        result = fuzzify("herbal_kering", 5, 75)
        k = result["kelembaban_ruangan"]
        assert k["lembab"] > 0.5


# ─────────────────────────────────────────
# Rule Evaluation Tests
# ─────────────────────────────────────────

class TestEvaluateRules:
    def test_sayur_daun_panjang_fires(self):
        fz = fuzzify("sayur_daun", 12, 50)
        agg = evaluate_rules(fz)
        # Harus menghasilkan sangat_dingin dan tinggi
        assert agg["suhu"]["sangat_dingin"] > 0
        assert agg["rh"]["tinggi"] > 0

    def test_skincare_lembab_fires(self):
        fz = fuzzify("skincare", 10, 75)
        agg = evaluate_rules(fz)
        assert agg["suhu"]["ruang"] > 0
        assert agg["rh"]["rendah"] > 0

    def test_herbal_kering_lembab(self):
        fz = fuzzify("herbal_kering", 5, 75)
        agg = evaluate_rules(fz)
        assert agg["suhu"]["sejuk"] > 0
        assert agg["rh"]["rendah"] > 0

    def test_daging_segar_sedang(self):
        fz = fuzzify("daging_segar", 6, 50)
        agg = evaluate_rules(fz)
        assert agg["suhu"]["sangat_dingin"] > 0
        assert agg["rh"]["rendah"] > 0

    def test_aggregation_values_in_range(self):
        fz = fuzzify("susu_olahan", 3, 50)
        agg = evaluate_rules(fz)
        for v in agg["suhu"].values():
            assert 0 <= v <= 1
        for v in agg["rh"].values():
            assert 0 <= v <= 1


# ─────────────────────────────────────────
# Defuzzification Tests
# ─────────────────────────────────────────

class TestDefuzzify:
    def _agg_for(self, jenis, lama, kelembaban=50):
        fz = fuzzify(jenis, lama, kelembaban)
        return evaluate_rules(fz)

    def test_suhu_in_range_sayur_daun(self):
        agg = self._agg_for("sayur_daun", 7)
        result = defuzzify(agg)
        assert 0 <= result["suhu"] <= 25

    def test_rh_in_range_sayur_daun(self):
        agg = self._agg_for("sayur_daun", 7)
        result = defuzzify(agg)
        assert 30 <= result["rh"] <= 85

    def test_skincare_produces_warm_temp(self):
        agg = self._agg_for("skincare", 10, 75)
        result = defuzzify(agg)
        # Skincare harus mendapat suhu di atas 14°C
        assert result["suhu"] >= 14

    def test_daging_produces_cold_temp(self):
        agg = self._agg_for("daging_segar", 10)
        result = defuzzify(agg)
        # Daging harus mendapat suhu di bawah 8°C
        assert result["suhu"] < 8

    def test_herbal_produces_low_rh(self):
        agg = self._agg_for("herbal_kering", 5, 75)
        result = defuzzify(agg)
        # Herbal kering harus kelembaban rendah
        assert result["rh"] < 60

    def test_label_returned(self):
        agg = self._agg_for("sayur_daun", 7)
        result = defuzzify(agg)
        assert result["suhu_label"] in ["Sangat Dingin","Dingin","Sejuk","Sedang","Suhu Ruang"]
        assert result["rh_label"]   in ["Rendah","Sedang","Tinggi"]


# ─────────────────────────────────────────
# Integration Tests (run_fuzzy)
# ─────────────────────────────────────────

class TestRunFuzzy:
    @pytest.mark.parametrize("jenis,lama,kelembaban", [
        ("sayur_daun",    2,  50),
        ("sayur_daun",   14,  75),
        ("sayur_buah",    5,  50),
        ("daging_segar",  7,  40),
        ("daging_segar", 14,  45),
        ("susu_olahan",   3,  50),
        ("susu_olahan",  10,  60),
        ("herbal_kering", 7,  70),
        ("herbal_kering",14,  35),
        ("skincare",      7,  75),
        ("skincare",     14,  50),
    ])
    def test_pipeline_output_in_valid_range(self, jenis, lama, kelembaban):
        result = run_fuzzy(jenis, lama, kelembaban)
        assert 0 <= result["suhu"] <= 25,  f"Suhu out of range: {result['suhu']}"
        assert 30 <= result["rh"]  <= 85,  f"RH out of range: {result['rh']}"
        assert result["suhu_label"] != ""
        assert result["rh_label"]   != ""

    def test_default_kelembaban(self):
        r1 = run_fuzzy("sayur_daun", 5, 50.0)
        r2 = run_fuzzy("sayur_daun", 5)          # default=50
        assert r1["suhu"] == r2["suhu"]
        assert r1["rh"]   == r2["rh"]
