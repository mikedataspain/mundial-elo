"""Tests for modelo.py — ELO math and Monte Carlo simulation."""

import numpy as np
import pytest

from modelo import (
    elo_win_prob,
    draw_rate,
    probabilidades_partido,
    simular_fase_grupos,
    simular_torneo_completo,
    seleccionar_mejores_terceros,
    calcular_probabilidades_fase_grupos,
)
from equivalencias import GRUPOS, EQUIPOS_MUNDIAL_48
from config import DRAW_CALIBRATION

# ---------------------------------------------------------------------------
# Fixtures shared across tests
# ---------------------------------------------------------------------------

# Two-group mini-tournament for fast group-stage tests
_GRUPOS_2 = {
    "H": ["España", "Uruguay", "Arabia Saudí", "Cabo Verde"],
    "J": ["Argentina", "Argelia", "Austria", "Jordania"],
}
_ELOS_2 = {
    "España": 1844.0, "Uruguay": 1700.0, "Arabia Saudí": 1550.0, "Cabo Verde": 1450.0,
    "Argentina": 1820.0, "Argelia": 1650.0, "Austria": 1600.0, "Jordania": 1500.0,
}

# Full 48-team ELOs for complete tournament tests (all at 1500 except one clear favourite)
_ELOS_FULL = {eq: 1500.0 for eq in EQUIPOS_MUNDIAL_48}
_ELOS_FULL["España"] = 1844.0


# ---------------------------------------------------------------------------
# elo_win_prob
# ---------------------------------------------------------------------------

class TestEloWinProb:
    def test_equal_elos_returns_half(self):
        assert elo_win_prob(1500.0, 1500.0) == pytest.approx(0.5)

    def test_stronger_team_has_higher_prob(self):
        assert elo_win_prob(1600.0, 1500.0) > 0.5

    def test_weaker_team_has_lower_prob(self):
        assert elo_win_prob(1400.0, 1500.0) < 0.5

    def test_400_point_gap(self):
        # We = 1 / (10^(-400/400) + 1) = 1 / (0.1 + 1) = 10/11
        assert elo_win_prob(1900.0, 1500.0) == pytest.approx(10 / 11, rel=1e-6)

    def test_symmetric(self):
        assert elo_win_prob(1800.0, 1600.0) + elo_win_prob(1600.0, 1800.0) == pytest.approx(1.0)

    def test_various_pairs_sum_to_one(self):
        pairs = [(1500, 1500), (1800, 1400), (2000, 1200), (1844, 1700)]
        for a, b in pairs:
            assert elo_win_prob(a, b) + elo_win_prob(b, a) == pytest.approx(1.0)

    def test_result_in_unit_interval(self):
        for a, b in [(1200, 2300), (2300, 1200), (1500, 1500)]:
            p = elo_win_prob(a, b)
            assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# draw_rate
# ---------------------------------------------------------------------------

class TestDrawRate:
    def test_exact_calibration_knots(self):
        for delta, expected in DRAW_CALIBRATION:
            assert draw_rate(delta) == pytest.approx(expected, abs=1e-9)

    def test_monotone_decreasing(self):
        deltas = [0, 50, 100, 150, 200, 300, 400, 500, 600]
        rates = [draw_rate(d) for d in deltas]
        for i in range(len(rates) - 1):
            assert rates[i] >= rates[i + 1], (
                f"draw_rate not monotone at delta={deltas[i+1]}: "
                f"{rates[i]:.4f} < {rates[i+1]:.4f}"
            )

    def test_clamped_above_max_delta(self):
        assert draw_rate(700) == pytest.approx(draw_rate(600))
        assert draw_rate(1000) == pytest.approx(draw_rate(600))

    def test_negative_delta_same_as_positive(self):
        assert draw_rate(-100) == pytest.approx(draw_rate(100))
        assert draw_rate(-300) == pytest.approx(draw_rate(300))

    def test_result_in_unit_interval(self):
        for delta in range(0, 700, 50):
            r = draw_rate(delta)
            assert 0.0 <= r <= 1.0, f"draw_rate({delta}) = {r} out of [0, 1]"


# ---------------------------------------------------------------------------
# probabilidades_partido
# ---------------------------------------------------------------------------

class TestProbabilidadesPartido:
    def test_sum_to_one(self):
        for a, b in [(1500, 1500), (1800, 1400), (1844, 1700), (2000, 1200)]:
            pa, pd, pb = probabilidades_partido(a, b)
            assert pa + pd + pb == pytest.approx(1.0, abs=1e-9)

    def test_all_non_negative(self):
        pa, pd, pb = probabilidades_partido(1600.0, 1500.0)
        assert pa >= 0 and pd >= 0 and pb >= 0

    def test_draw_probability_matches_draw_rate(self):
        pa, pd, pb = probabilidades_partido(1700.0, 1500.0)
        assert pd == pytest.approx(draw_rate(200.0))

    def test_stronger_team_wins_more_often(self):
        pa, _, pb = probabilidades_partido(1800.0, 1400.0)
        assert pa > pb

    def test_symmetric_swap(self):
        pa, pd, pb = probabilidades_partido(1800.0, 1600.0)
        pa2, pd2, pb2 = probabilidades_partido(1600.0, 1800.0)
        assert pa == pytest.approx(pb2)
        assert pd == pytest.approx(pd2)
        assert pb == pytest.approx(pa2)


# ---------------------------------------------------------------------------
# simular_fase_grupos
# ---------------------------------------------------------------------------

class TestSimularFaseGrupos:
    def test_reproducible_with_same_seed(self):
        r1 = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=200, seed=42)
        r2 = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=200, seed=42)
        np.testing.assert_array_equal(
            r1["clasificados_1"]["H"], r2["clasificados_1"]["H"]
        )

    def test_different_seeds_give_different_results(self):
        r1 = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=500, seed=1)
        r2 = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=500, seed=2)
        # Very unlikely to be identical
        assert not np.array_equal(r1["clasificados_1"]["H"], r2["clasificados_1"]["H"])

    def test_output_has_required_keys(self):
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=100, seed=0)
        for key in (
            "clasificados_1", "clasificados_2", "clasificados_3",
            "terceros_puntos", "equipo_idx", "equipo_nombre", "n_sims",
        ):
            assert key in r

    def test_all_groups_present_in_output(self):
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=100, seed=0)
        assert set(r["clasificados_1"].keys()) == set(_GRUPOS_2.keys())

    def test_output_array_shapes(self):
        n = 200
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=n, seed=0)
        for grupo in _GRUPOS_2:
            for key in ("clasificados_1", "clasificados_2", "clasificados_3"):
                assert r[key][grupo].shape == (n,), f"{key}[{grupo}] has wrong shape"

    def test_indices_within_valid_range(self):
        n_eq = sum(len(v) for v in _GRUPOS_2.values())  # 8
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=200, seed=0)
        for grupo in _GRUPOS_2:
            for key in ("clasificados_1", "clasificados_2", "clasificados_3"):
                arr = r[key][grupo]
                assert np.all(arr >= 0) and np.all(arr < n_eq), (
                    f"{key}[{grupo}] has out-of-range indices"
                )

    def test_top_team_finishes_first_most_often(self):
        # España (1844) should lead group H in most simulations
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=2000, seed=42)
        espana_idx = r["equipo_idx"]["España"]
        p_first = np.mean(r["clasificados_1"]["H"] == espana_idx)
        assert p_first > 0.5, f"España expected 1st in >50% of sims, got {p_first:.1%}"

    def test_n_sims_stored_correctly(self):
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=333, seed=0)
        assert r["n_sims"] == 333

    def test_equipo_idx_covers_all_teams(self):
        r = simular_fase_grupos(_GRUPOS_2, _ELOS_2, n_sims=100, seed=0)
        all_teams = [eq for eqs in _GRUPOS_2.values() for eq in eqs]
        for team in all_teams:
            assert team in r["equipo_idx"]


# ---------------------------------------------------------------------------
# seleccionar_mejores_terceros  (requires full 12-group input)
# ---------------------------------------------------------------------------

class TestSeleccionarMejoresTerceros:
    @pytest.fixture(scope="class")
    def res_grupos_full(self):
        return simular_fase_grupos(GRUPOS, _ELOS_FULL, n_sims=500, seed=42)

    def test_output_shape(self, res_grupos_full):
        mejores = seleccionar_mejores_terceros(GRUPOS, res_grupos_full, _ELOS_FULL, n_mejores=8)
        assert mejores.shape == (8, 500)

    def test_no_duplicates_within_simulation(self, res_grupos_full):
        mejores = seleccionar_mejores_terceros(GRUPOS, res_grupos_full, _ELOS_FULL, n_mejores=8)
        # For each simulation column, the 8 selected indices should be unique
        for sim in range(0, 500, 50):  # sample every 50th sim for speed
            assert len(set(mejores[:, sim])) == 8, (
                f"Duplicate third-place teams in simulation {sim}"
            )

    def test_indices_in_valid_range(self, res_grupos_full):
        mejores = seleccionar_mejores_terceros(GRUPOS, res_grupos_full, _ELOS_FULL, n_mejores=8)
        n_eq = len(EQUIPOS_MUNDIAL_48)
        assert np.all(mejores >= 0) and np.all(mejores < n_eq)


# ---------------------------------------------------------------------------
# simular_torneo_completo
# ---------------------------------------------------------------------------

class TestSimularTorneoCompleto:
    @pytest.fixture(scope="class")
    def df(self):
        return simular_torneo_completo(GRUPOS, _ELOS_FULL, n_sims=2000, seed=42)

    def test_returns_48_rows(self, df):
        assert len(df) == 48

    def test_required_columns_present(self, df):
        for col in ("Selección", "Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"):
            assert col in df.columns

    def test_campeon_sums_to_100(self, df):
        total = df["Campeón%"].sum()
        assert abs(total - 100.0) < 3.0, f"Campeón% sum = {total:.1f}, expected ~100"

    def test_monotone_advancement_per_team(self, df):
        rounds = ["Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"]
        for _, row in df.iterrows():
            for earlier, later in zip(rounds, rounds[1:]):
                assert row[earlier] >= row[later], (
                    f"{row['Selección']}: {earlier}={row[earlier]} < {later}={row[later]}"
                )

    def test_all_probabilities_non_negative(self, df):
        for col in ("Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"):
            assert (df[col] >= 0).all(), f"Negative values found in {col}"

    def test_highest_elo_team_has_top_championship_prob(self, df):
        top = df.sort_values("Campeón%", ascending=False).iloc[0]["Selección"]
        assert top == "España", f"Expected España as top pick, got {top}"

    def test_reproducible_with_same_seed(self):
        df1 = simular_torneo_completo(GRUPOS, _ELOS_FULL, n_sims=300, seed=7)
        df2 = simular_torneo_completo(GRUPOS, _ELOS_FULL, n_sims=300, seed=7)
        assert df1["Campeón%"].tolist() == df2["Campeón%"].tolist()

    def test_all_48_teams_represented(self, df):
        assert set(df["Selección"]) == set(EQUIPOS_MUNDIAL_48)

    def test_grupo_column_present(self, df):
        assert "Grupo" in df.columns
        assert df["Grupo"].notna().all()


# ---------------------------------------------------------------------------
# calcular_probabilidades_fase_grupos
# ---------------------------------------------------------------------------

_MATCH_TEMPLATE = {
    "grupo": "H", "jornada": 1, "fecha": "2026-06-15",
    "hora": "TBD", "sede": "Miami", "estadio": "Hard Rock Stadium",
}


class TestCalcularProbabilidadesFaseGrupos:
    def test_output_length_matches_input(self):
        partidos = [
            {**_MATCH_TEMPLATE, "equipo1": "España", "equipo2": "Uruguay"},
            {**_MATCH_TEMPLATE, "equipo1": "Arabia Saudí", "equipo2": "Cabo Verde"},
        ]
        elos = {"España": 1844.0, "Uruguay": 1700.0, "Arabia Saudí": 1550.0, "Cabo Verde": 1450.0}
        result = calcular_probabilidades_fase_grupos(partidos, elos)
        assert len(result) == 2

    def test_required_fields_added(self):
        partidos = [{**_MATCH_TEMPLATE, "equipo1": "España", "equipo2": "Uruguay"}]
        elos = {"España": 1844.0, "Uruguay": 1700.0}
        result = calcular_probabilidades_fase_grupos(partidos, elos)
        match = result[0]
        for key in ("elo1", "elo2", "delta_elo", "pct_vic1", "pct_empate", "pct_vic2", "favorito"):
            assert key in match, f"Missing key: {key}"

    def test_probabilities_sum_to_100(self):
        partidos = [
            {**_MATCH_TEMPLATE, "equipo1": "España", "equipo2": "Uruguay"},
            {**_MATCH_TEMPLATE, "equipo1": "Argentina", "equipo2": "Austria"},
        ]
        elos = {"España": 1844.0, "Uruguay": 1700.0, "Argentina": 1820.0, "Austria": 1600.0}
        result = calcular_probabilidades_fase_grupos(partidos, elos)
        for match in result:
            total = match["pct_vic1"] + match["pct_empate"] + match["pct_vic2"]
            assert abs(total - 100.0) < 0.15, f"Probabilities sum to {total:.2f}"

    def test_favourite_identified_correctly(self):
        partidos = [{**_MATCH_TEMPLATE, "equipo1": "España", "equipo2": "Uruguay"}]
        elos = {"España": 1844.0, "Uruguay": 1700.0}
        result = calcular_probabilidades_fase_grupos(partidos, elos)
        assert result[0]["favorito"] == "España"

    def test_equilibrado_when_close_elos(self):
        partidos = [{**_MATCH_TEMPLATE, "equipo1": "TeamA", "equipo2": "TeamB"}]
        elos = {"TeamA": 1502.0, "TeamB": 1500.0}  # delta = 2, within ±5 threshold
        result = calcular_probabilidades_fase_grupos(partidos, elos)
        assert result[0]["favorito"] == "Equilibrado"

    def test_unknown_teams_default_to_1500_elo(self):
        partidos = [{**_MATCH_TEMPLATE, "equipo1": "UnknownA", "equipo2": "UnknownB"}]
        result = calcular_probabilidades_fase_grupos(partidos, {})
        match = result[0]
        assert match["elo1"] == 1500
        assert match["elo2"] == 1500
        assert match["favorito"] == "Equilibrado"
