"""Tests for validacion.py — data validation and cache round-trips."""

import json
import pytest

import validacion
from validacion import (
    ValidationError,
    validar_cobertura,
    validar_rango_elo,
    validar_variacion_diaria,
    validar_todo,
    guardar_elos_cache,
    cargar_elos_anteriores,
    guardar_probs_cache,
    cargar_probs_anteriores,
)
from equivalencias import EQUIPOS_MUNDIAL_48
from config import MIN_EQUIPOS_REQUERIDOS, ELO_MIN, ELO_MAX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elos_all_48(value: float = 1600.0) -> dict:
    return {eq: value for eq in EQUIPOS_MUNDIAL_48}


def _elos_n_teams(n: int, value: float = 1600.0) -> dict:
    return {eq: value for eq in EQUIPOS_MUNDIAL_48[:n]}


# ---------------------------------------------------------------------------
# validar_cobertura
# ---------------------------------------------------------------------------

class TestValidarCobertura:
    def test_all_48_teams_passes(self):
        assert validar_cobertura(_elos_all_48()) is True

    def test_exactly_minimum_threshold_passes(self):
        # MIN_EQUIPOS_REQUERIDOS teams present → should pass
        elos = _elos_n_teams(MIN_EQUIPOS_REQUERIDOS)
        assert validar_cobertura(elos) is True

    def test_one_below_minimum_raises(self):
        elos = _elos_n_teams(MIN_EQUIPOS_REQUERIDOS - 1)
        with pytest.raises(ValidationError):
            validar_cobertura(elos)

    def test_error_message_mentions_missing_teams(self):
        elos = _elos_n_teams(MIN_EQUIPOS_REQUERIDOS - 1)
        with pytest.raises(ValidationError, match="Ausentes"):
            validar_cobertura(elos)

    def test_empty_dict_raises(self):
        with pytest.raises(ValidationError):
            validar_cobertura({})

    def test_non_world_cup_teams_dont_count_toward_coverage(self):
        # Only non-qualified teams → should fail coverage
        elos = {"Italia": 1700.0, "Dinamarca": 1650.0}
        with pytest.raises(ValidationError):
            validar_cobertura(elos)


# ---------------------------------------------------------------------------
# validar_rango_elo
# ---------------------------------------------------------------------------

class TestValidarRangoElo:
    def test_all_in_range_passes(self):
        assert validar_rango_elo(_elos_all_48(1600.0)) is True

    def test_exact_lower_boundary_passes(self):
        elos = {"España": float(ELO_MIN)}
        assert validar_rango_elo(elos) is True

    def test_exact_upper_boundary_passes(self):
        elos = {"España": float(ELO_MAX)}
        assert validar_rango_elo(elos) is True

    def test_one_below_min_raises(self):
        elos = _elos_all_48()
        elos["España"] = ELO_MIN - 1
        with pytest.raises(ValidationError):
            validar_rango_elo(elos)

    def test_one_above_max_raises(self):
        elos = _elos_all_48()
        elos["España"] = ELO_MAX + 1
        with pytest.raises(ValidationError):
            validar_rango_elo(elos)

    def test_error_message_identifies_offending_team(self):
        elos = {"España": 999.0}
        with pytest.raises(ValidationError, match="España"):
            validar_rango_elo(elos)


# ---------------------------------------------------------------------------
# validar_variacion_diaria
# ---------------------------------------------------------------------------

class TestValidarVariacionDiaria:
    def test_no_previous_data_always_passes(self):
        assert validar_variacion_diaria(_elos_all_48(), None) is True

    def test_identical_elos_passes(self):
        elos = _elos_all_48(1600.0)
        assert validar_variacion_diaria(elos, elos) is True

    def test_small_change_passes(self):
        elos_hoy = _elos_all_48(1600.0)
        elos_ayer = _elos_all_48(1598.0)
        assert validar_variacion_diaria(elos_hoy, elos_ayer) is True


# ---------------------------------------------------------------------------
# validar_todo
# ---------------------------------------------------------------------------

class TestValidarTodo:
    def test_valid_input_returns_true(self, monkeypatch):
        monkeypatch.setattr(validacion, "cargar_elos_anteriores", lambda: None)
        assert validar_todo(_elos_all_48()) is True

    def test_fails_on_low_coverage(self, monkeypatch):
        monkeypatch.setattr(validacion, "cargar_elos_anteriores", lambda: None)
        with pytest.raises(ValidationError):
            validar_todo(_elos_n_teams(MIN_EQUIPOS_REQUERIDOS - 1))

    def test_fails_on_out_of_range_elo(self, monkeypatch):
        monkeypatch.setattr(validacion, "cargar_elos_anteriores", lambda: None)
        elos = _elos_all_48()
        elos["España"] = ELO_MAX + 100
        with pytest.raises(ValidationError):
            validar_todo(elos)

    def test_short_circuits_on_first_failure(self, monkeypatch):
        # Coverage fails first; range check should not be reached
        monkeypatch.setattr(validacion, "cargar_elos_anteriores", lambda: None)
        elos = {"España": ELO_MAX + 100}  # only 1 team (fails coverage) AND bad elo
        with pytest.raises(ValidationError, match="Cobertura"):
            validar_todo(elos)


# ---------------------------------------------------------------------------
# Cache round-trips
# ---------------------------------------------------------------------------

class TestElosCache:
    def test_round_trip_preserves_data(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "elos_test.json"
        monkeypatch.setattr(validacion, "JSON_CACHE_ELOS", cache_file)

        original = {"España": 1844.0, "Argentina": 1820.0, "Francia": 1780.0}
        guardar_elos_cache(original, "2026-06-13")
        loaded = cargar_elos_anteriores()

        assert loaded == original

    def test_returns_none_when_file_absent(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "nonexistent.json"
        monkeypatch.setattr(validacion, "JSON_CACHE_ELOS", cache_file)

        result = cargar_elos_anteriores()
        assert result is None

    def test_cache_file_contains_fecha(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "elos_test.json"
        monkeypatch.setattr(validacion, "JSON_CACHE_ELOS", cache_file)

        guardar_elos_cache({"España": 1844.0}, "2026-06-13")
        data = json.loads(cache_file.read_text())
        assert data["fecha"] == "2026-06-13"

    def test_overwrites_previous_cache(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "elos_test.json"
        monkeypatch.setattr(validacion, "JSON_CACHE_ELOS", cache_file)

        guardar_elos_cache({"España": 1800.0}, "2026-06-12")
        guardar_elos_cache({"España": 1844.0}, "2026-06-13")
        loaded = cargar_elos_anteriores()
        assert loaded == {"España": 1844.0}


class TestProbsCache:
    def test_round_trip_preserves_data(self, tmp_path):
        path = tmp_path / "probs.json"
        probs = {"España vs Uruguay": {"vic1": 65.0, "empate": 20.0, "vic2": 15.0}}
        guardar_probs_cache(probs, path, fecha="2026-06-13")
        loaded = cargar_probs_anteriores(path)
        assert loaded["probs"] == probs

    def test_returns_none_when_absent(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        assert cargar_probs_anteriores(path) is None
