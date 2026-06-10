"""
validacion.py
Validaciones obligatorias antes de sobrescribir cualquier output.
Si falla alguna, lanza ValidationError (o devuelve False) y el sistema
conserva todos los datos anteriores sin modificar.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from config import (
    MIN_EQUIPOS_REQUERIDOS, ELO_MIN, ELO_MAX, MAX_CAMBIO_ELO_DIARIO,
    JSON_CACHE_ELOS,
)
from equivalencias import EQUIPOS_MUNDIAL_48

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Excepción personalizada para fallos de validación."""
    pass


# ---------------------------------------------------------------------------
# 1. Mínimo de selecciones extraídas
# ---------------------------------------------------------------------------

def validar_cobertura(elos: dict[str, float]) -> bool:
    """
    Verifica que se han extraído Elos de al menos MIN_EQUIPOS_REQUERIDOS
    de las 48 selecciones del Mundial.
    """
    presentes = [eq for eq in EQUIPOS_MUNDIAL_48 if eq in elos]
    n = len(presentes)
    if n < MIN_EQUIPOS_REQUERIDOS:
        ausentes = [eq for eq in EQUIPOS_MUNDIAL_48 if eq not in elos]
        msg = (
            f"Cobertura insuficiente: {n}/{len(EQUIPOS_MUNDIAL_48)} equipos extraídos "
            f"(mínimo: {MIN_EQUIPOS_REQUERIDOS}). "
            f"Ausentes: {', '.join(ausentes)}"
        )
        logger.error(msg)
        raise ValidationError(msg)
    logger.info(f"Cobertura OK: {n}/{len(EQUIPOS_MUNDIAL_48)} equipos.")
    return True


# ---------------------------------------------------------------------------
# 2. Rango válido de Elo
# ---------------------------------------------------------------------------

def validar_rango_elo(elos: dict[str, float]) -> bool:
    """
    Verifica que ningún Elo está fuera del rango [ELO_MIN, ELO_MAX].
    """
    fuera_de_rango = {
        eq: v for eq, v in elos.items()
        if not (ELO_MIN <= v <= ELO_MAX)
    }
    if fuera_de_rango:
        detalles = "; ".join(f"{eq}={v}" for eq, v in fuera_de_rango.items())
        msg = f"Elos fuera de rango [{ELO_MIN}, {ELO_MAX}]: {detalles}"
        logger.error(msg)
        raise ValidationError(msg)
    logger.info("Rango de Elo OK.")
    return True


# ---------------------------------------------------------------------------
# 3. Variación máxima respecto al día anterior
# ---------------------------------------------------------------------------

def cargar_elos_anteriores() -> Optional[dict[str, float]]:
    """Carga el caché de Elos del día anterior. Devuelve None si no existe."""
    if not JSON_CACHE_ELOS.exists():
        logger.info("No existe caché de Elos anteriores (primera ejecución).")
        return None
    try:
        with open(JSON_CACHE_ELOS, encoding="utf-8") as f:
            data = json.load(f)
        return {k: float(v) for k, v in data.get("elos", {}).items()}
    except Exception as exc:
        logger.warning(f"No se pudo leer el caché de Elos: {exc}")
        return None


def guardar_elos_cache(elos: dict[str, float], fecha: str = "") -> None:
    """Guarda los Elos actuales en el caché para usar mañana."""
    JSON_CACHE_ELOS.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_CACHE_ELOS, "w", encoding="utf-8") as f:
        json.dump({"fecha": fecha, "elos": elos}, f, ensure_ascii=False, indent=2)
    logger.info(f"Caché de Elos guardado ({len(elos)} equipos).")


def validar_variacion_diaria(
    elos_hoy: dict[str, float],
    elos_ayer: Optional[dict[str, float]],
) -> bool:
    """
    Verifica que ningún Elo ha cambiado más de MAX_CAMBIO_ELO_DIARIO
    respecto al día anterior. Si no hay datos anteriores, pasa sin error.
    """
    if elos_ayer is None:
        logger.info("Sin datos anteriores: validación de variación diaria omitida.")
        return True

    cambios_excesivos = {}
    for eq, elo_hoy in elos_hoy.items():
        if eq in elos_ayer:
            cambio = abs(elo_hoy - elos_ayer[eq])
            if cambio > MAX_CAMBIO_ELO_DIARIO:
                cambios_excesivos[eq] = (elos_ayer[eq], elo_hoy, cambio)

    if cambios_excesivos:
        detalles = "; ".join(
            f"{eq}: {ant:.0f}→{nvo:.0f} (Δ={d:.0f})"
            for eq, (ant, nvo, d) in cambios_excesivos.items()
        )
        msg = f"Variación diaria excesiva (>{MAX_CAMBIO_ELO_DIARIO} pts): {detalles}"
        logger.error(msg)
        raise ValidationError(msg)

    logger.info("Variación diaria OK.")
    return True


# ---------------------------------------------------------------------------
# 4. Validación completa (orquesta las tres anteriores)
# ---------------------------------------------------------------------------

def validar_todo(elos: dict[str, float]) -> bool:
    """
    Ejecuta las tres validaciones en orden.
    Lanza ValidationError en el primer fallo.
    Devuelve True si todo está OK.
    """
    elos_ayer = cargar_elos_anteriores()
    validar_cobertura(elos)
    validar_rango_elo(elos)
    validar_variacion_diaria(elos, elos_ayer)
    return True


# ---------------------------------------------------------------------------
# 5. Caché de probabilidades (para comparación diaria en Sheets)
# ---------------------------------------------------------------------------

def cargar_probs_anteriores(path: Path) -> Optional[dict]:
    """Carga probabilidades del día anterior desde JSON."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning(f"No se pudo leer caché de probabilidades: {exc}")
        return None


def guardar_probs_cache(probs: dict, path: Path, fecha: str = "",
                        ultimo_cambio_elo: dict | None = None) -> None:
    """Guarda probabilidades actuales en caché, incluyendo el último cambio de Elo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fecha": fecha, "probs": probs}
    if ultimo_cambio_elo:
        payload["ultimo_cambio_elo"] = ultimo_cambio_elo
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("Caché de probabilidades guardado.")
