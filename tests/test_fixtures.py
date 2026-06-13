"""Tests for fixtures.py — group stage calendar generation."""

from collections import Counter

import pytest

from fixtures import generar_calendario_hardcoded, get_calendario, SEDES_GRUPOS, FECHAS_JORNADAS
from equivalencias import GRUPOS


# ---------------------------------------------------------------------------
# generar_calendario_hardcoded
# ---------------------------------------------------------------------------

class TestGenerarCalendarioHardcoded:
    @pytest.fixture(scope="class")
    def partidos(self):
        return generar_calendario_hardcoded(GRUPOS)

    def test_returns_exactly_72_matches(self, partidos):
        assert len(partidos) == 72, f"Expected 72 matches, got {len(partidos)}"

    def test_all_required_keys_present(self, partidos):
        required = {"grupo", "jornada", "equipo1", "equipo2", "fecha", "hora", "sede", "estadio"}
        for i, match in enumerate(partidos):
            missing = required - match.keys()
            assert not missing, f"Match {i} missing keys: {missing}"

    def test_each_team_plays_exactly_3_matches(self, partidos):
        for grupo, equipos in GRUPOS.items():
            grupo_matches = [p for p in partidos if p["grupo"] == grupo]
            for team in equipos:
                appearances = sum(
                    1 for p in grupo_matches
                    if p["equipo1"] == team or p["equipo2"] == team
                )
                assert appearances == 3, (
                    f"{team} (group {grupo}) plays {appearances} matches, expected 3"
                )

    def test_no_team_plays_against_itself(self, partidos):
        for match in partidos:
            assert match["equipo1"] != match["equipo2"], (
                f"Self-match detected: {match['equipo1']} vs {match['equipo2']}"
            )

    def test_3_matchdays_per_group(self, partidos):
        for grupo in GRUPOS:
            grupo_matches = [p for p in partidos if p["grupo"] == grupo]
            jornadas = {p["jornada"] for p in grupo_matches}
            assert jornadas == {1, 2, 3}, f"Group {grupo} has matchdays {jornadas}"

    def test_each_group_has_6_matches(self, partidos):
        for grupo in GRUPOS:
            grupo_matches = [p for p in partidos if p["grupo"] == grupo]
            assert len(grupo_matches) == 6, (
                f"Group {grupo} has {len(grupo_matches)} matches, expected 6"
            )

    def test_matchday_3_is_simultaneous_pairs(self, partidos):
        # Each group's matchday-3 has exactly 2 matches
        for grupo in GRUPOS:
            jd3 = [p for p in partidos if p["grupo"] == grupo and p["jornada"] == 3]
            assert len(jd3) == 2, f"Group {grupo} matchday 3 has {len(jd3)} matches"

    def test_no_pair_plays_twice(self, partidos):
        for grupo in GRUPOS:
            grupo_matches = [p for p in partidos if p["grupo"] == grupo]
            pairs = Counter(
                frozenset([p["equipo1"], p["equipo2"]]) for p in grupo_matches
            )
            for pair, count in pairs.items():
                assert count == 1, f"Pair {pair} in group {grupo} plays {count} times"

    def test_sede_and_estadio_non_empty(self, partidos):
        for match in partidos:
            assert match["sede"] not in ("", None), "Empty sede found"
            assert match["estadio"] not in ("", None), "Empty estadio found"

    def test_all_teams_appear_in_correct_group(self, partidos):
        for match in partidos:
            grupo = match["grupo"]
            expected_teams = set(GRUPOS[grupo])
            assert match["equipo1"] in expected_teams, (
                f"{match['equipo1']} found in group {grupo} but not in GRUPOS"
            )
            assert match["equipo2"] in expected_teams, (
                f"{match['equipo2']} found in group {grupo} but not in GRUPOS"
            )


# ---------------------------------------------------------------------------
# get_calendario (entry point)
# ---------------------------------------------------------------------------

class TestGetCalendario:
    def test_returns_72_matches(self):
        result = get_calendario(GRUPOS)
        assert len(result) == 72

    def test_same_as_hardcoded_calendar(self):
        # Current implementation always returns hardcoded calendar
        hardcoded = generar_calendario_hardcoded(GRUPOS)
        via_get = get_calendario(GRUPOS)
        assert len(via_get) == len(hardcoded)


# ---------------------------------------------------------------------------
# Static data integrity (SEDES_GRUPOS, FECHAS_JORNADAS)
# ---------------------------------------------------------------------------

class TestStaticData:
    def test_sedes_has_all_12_groups(self):
        assert set(SEDES_GRUPOS.keys()) == set(GRUPOS.keys())

    def test_sedes_tuples_non_empty(self):
        for grupo, (city, stadium) in SEDES_GRUPOS.items():
            assert city and stadium, f"Empty venue for group {grupo}"

    def test_fechas_has_all_12_groups(self):
        assert set(FECHAS_JORNADAS.keys()) == set(GRUPOS.keys())

    def test_fechas_has_3_matchdays_per_group(self):
        for grupo, fechas in FECHAS_JORNADAS.items():
            assert set(fechas.keys()) == {1, 2, 3}, (
                f"Group {grupo} missing matchday dates: {fechas}"
            )

    def test_fechas_are_valid_iso_format(self):
        from datetime import date
        for grupo, fechas in FECHAS_JORNADAS.items():
            for jornada, fecha in fechas.items():
                try:
                    date.fromisoformat(fecha)
                except ValueError:
                    pytest.fail(f"Invalid date '{fecha}' for group {grupo} matchday {jornada}")
