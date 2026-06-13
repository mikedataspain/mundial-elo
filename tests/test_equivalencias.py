"""Tests for equivalencias.py — name mappings and data integrity."""

import pytest

from equivalencias import (
    EQUIVALENCIAS_EN_ES,
    EQUIPOS_MUNDIAL_48,
    GRUPOS,
    a_castellano,
    es_equipo_mundial,
)


# ---------------------------------------------------------------------------
# a_castellano — name mapping
# ---------------------------------------------------------------------------

class TestACastellano:
    @pytest.mark.parametrize("english,expected_spanish", [
        ("Spain",        "España"),
        ("Germany",      "Alemania"),
        ("Brazil",       "Brasil"),
        ("Mexico",       "México"),
        ("South Korea",  "Corea del Sur"),
        ("England",      "Inglaterra"),
        ("France",       "Francia"),
        ("Argentina",    "Argentina"),
        ("Netherlands",  "Países Bajos"),
        ("Saudi Arabia", "Arabia Saudí"),
    ])
    def test_known_mappings(self, english, expected_spanish):
        assert a_castellano(english) == expected_spanish

    def test_case_insensitive_match(self):
        # Direct lookup is case-sensitive; fallback loop is case-insensitive
        assert a_castellano("SPAIN") == "España"
        assert a_castellano("germany") == "Alemania"
        assert a_castellano("brazil") == "Brasil"

    def test_unknown_name_returned_as_is(self):
        assert a_castellano("Gondor FC") == "Gondor FC"

    def test_strips_leading_trailing_whitespace(self):
        assert a_castellano("  Spain  ") == "España"

    def test_variant_names_map_to_same_team(self):
        assert a_castellano("Korea Republic") == a_castellano("South Korea")
        assert a_castellano("Czechia") == a_castellano("Czech Republic")
        assert a_castellano("USA") == a_castellano("United States")

    def test_all_world_cup_teams_have_mapping(self):
        # Every team in GRUPOS should be reachable via some English name in the map
        mapped_spanish = set(EQUIVALENCIAS_EN_ES.values())
        for team in EQUIPOS_MUNDIAL_48:
            assert team in mapped_spanish, f"No English→Spanish mapping leads to '{team}'"


# ---------------------------------------------------------------------------
# es_equipo_mundial — qualified team check
# ---------------------------------------------------------------------------

class TestEsEquipoMundial:
    def test_all_48_teams_return_true(self):
        for team in EQUIPOS_MUNDIAL_48:
            assert es_equipo_mundial(team), f"'{team}' should be a World Cup team"

    @pytest.mark.parametrize("non_qualifier", [
        "Italia", "Dinamarca", "Polonia", "Grecia", "Gales",
    ])
    def test_non_qualified_teams_return_false(self, non_qualifier):
        assert not es_equipo_mundial(non_qualifier)

    def test_empty_string_returns_false(self):
        assert not es_equipo_mundial("")

    def test_case_sensitive(self):
        assert not es_equipo_mundial("españa")   # lowercase → not in list
        assert not es_equipo_mundial("ESPAÑA")


# ---------------------------------------------------------------------------
# GRUPOS data integrity
# ---------------------------------------------------------------------------

class TestGruposDataIntegrity:
    def test_exactly_12_groups(self):
        assert len(GRUPOS) == 12, f"Expected 12 groups, got {len(GRUPOS)}"

    def test_group_keys_are_A_through_L(self):
        expected = set("ABCDEFGHIJKL")
        assert set(GRUPOS.keys()) == expected

    def test_each_group_has_exactly_4_teams(self):
        for grupo, equipos in GRUPOS.items():
            assert len(equipos) == 4, f"Group {grupo} has {len(equipos)} teams, expected 4"

    def test_all_group_teams_are_in_mundial_48(self):
        mundial_set = set(EQUIPOS_MUNDIAL_48)
        for grupo, equipos in GRUPOS.items():
            for team in equipos:
                assert team in mundial_set, f"'{team}' in group {grupo} not in EQUIPOS_MUNDIAL_48"

    def test_no_team_appears_in_multiple_groups(self):
        seen = {}
        for grupo, equipos in GRUPOS.items():
            for team in equipos:
                assert team not in seen, (
                    f"'{team}' appears in both group {seen.get(team)} and group {grupo}"
                )
                seen[team] = grupo

    def test_grupos_covers_all_48_teams(self):
        teams_in_grupos = {eq for eqs in GRUPOS.values() for eq in eqs}
        assert teams_in_grupos == set(EQUIPOS_MUNDIAL_48)


# ---------------------------------------------------------------------------
# EQUIPOS_MUNDIAL_48 integrity
# ---------------------------------------------------------------------------

class TestEquiposMundial48Integrity:
    def test_exactly_48_teams(self):
        assert len(EQUIPOS_MUNDIAL_48) == 48

    def test_no_duplicates(self):
        assert len(EQUIPOS_MUNDIAL_48) == len(set(EQUIPOS_MUNDIAL_48))

    def test_no_empty_strings(self):
        for team in EQUIPOS_MUNDIAL_48:
            assert team.strip() != "", "Found empty team name in EQUIPOS_MUNDIAL_48"
