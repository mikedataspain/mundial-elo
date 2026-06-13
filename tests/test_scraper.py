"""Tests for scraper.py — fallback behaviour (Playwright mocked out)."""

from datetime import date
from unittest.mock import patch, AsyncMock

import pytest

import scraper
from scraper import obtener_elos_con_fallback


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PREV_ELOS = {
    "España": 1844.0,
    "Argentina": 1820.0,
    "Francia": 1780.0,
    "Brasil": 1760.0,
}

_SCRAPED_ELOS = {
    "España": 1850.0,
    "Argentina": 1815.0,
    "Francia": 1790.0,
    "Brasil": 1755.0,
    "Alemania": 1730.0,
    "Inglaterra": 1710.0,
    "Portugal": 1700.0,
    "Uruguay": 1680.0,
    "Países Bajos": 1670.0,
    "Bélgica": 1660.0,
    "Croacia": 1640.0,
    "México": 1620.0,
    "Japón": 1600.0,
    "Marruecos": 1590.0,
    "Senegal": 1580.0,
    "EE.UU.": 1570.0,
    "Colombia": 1560.0,
    "Ecuador": 1550.0,
    "Suiza": 1540.0,
    "Corea del Sur": 1530.0,
    "Australia": 1520.0,
}


# ---------------------------------------------------------------------------
# Scraper fallback when extraction fails
# ---------------------------------------------------------------------------

class TestObtenerElosConFallback:
    def test_returns_previous_elos_on_exception(self):
        with patch.object(scraper.asyncio, "run", side_effect=Exception("network down")):
            result_elos, fecha = obtener_elos_con_fallback(_PREV_ELOS)
        assert result_elos == _PREV_ELOS

    def test_fallback_fecha_is_today(self):
        with patch.object(scraper.asyncio, "run", side_effect=Exception("timeout")):
            _, fecha = obtener_elos_con_fallback(_PREV_ELOS)
        assert fecha == date.today().isoformat()

    def test_returns_empty_dict_and_today_when_no_fallback(self):
        with patch.object(scraper.asyncio, "run", side_effect=Exception("failed")):
            result_elos, fecha = obtener_elos_con_fallback(elos_anteriores=None)
        assert result_elos == {}
        assert fecha == date.today().isoformat()

    def test_returns_empty_dict_when_fallback_is_empty_dict(self):
        with patch.object(scraper.asyncio, "run", side_effect=Exception("failed")):
            result_elos, _ = obtener_elos_con_fallback(elos_anteriores={})
        assert result_elos == {}

    def test_uses_scraper_result_on_success(self):
        scraped = (_SCRAPED_ELOS, "2026-06-13")
        with patch.object(scraper.asyncio, "run", return_value=scraped):
            result_elos, fecha = obtener_elos_con_fallback(_PREV_ELOS)
        assert result_elos == _SCRAPED_ELOS
        assert fecha == "2026-06-13"

    def test_scraped_result_has_string_keys_and_float_values(self):
        scraped = (_SCRAPED_ELOS, "2026-06-13")
        with patch.object(scraper.asyncio, "run", return_value=scraped):
            result_elos, _ = obtener_elos_con_fallback(None)
        for team, elo in result_elos.items():
            assert isinstance(team, str), f"Key '{team}' is not a string"
            assert isinstance(elo, float), f"ELO for '{team}' is not a float"

    def test_fallback_when_too_few_teams_scraped(self):
        # If fewer than 20 World Cup teams are found, it should fall back to previous
        few_elos = {"España": 1844.0}  # only 1 team, below 20-team threshold
        with patch.object(scraper.asyncio, "run", return_value=(few_elos, "2026-06-13")):
            result_elos, _ = obtener_elos_con_fallback(_PREV_ELOS)
        assert result_elos == _PREV_ELOS
