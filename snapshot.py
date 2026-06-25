"""
snapshot.py
Genera una imagen PNG de la tabla de probabilidades del día.
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # sin pantalla (necesario en servidor CI)
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

logger = logging.getLogger(__name__)

_COLS = ["Selección", "Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"]

_HDR_BG    = "#1a1a2e"
_HDR_FG    = "#ffffff"
_ROW_ODD   = "#f7f7f7"
_ROW_EVEN  = "#ffffff"
_EDGE      = "#dddddd"
_TITLE_FG  = "#0f3460"

# Verde escalonado para la columna Campeón%
_CAMP_LOW  = (1.00, 1.00, 1.00)   # blanco
_CAMP_HIGH = (0.18, 0.65, 0.35)   # verde


def _camp_color(val: float, vmax: float) -> tuple:
    if vmax == 0:
        return _CAMP_LOW
    t = min(val / vmax, 1.0) ** 0.6   # raíz para exagerar diferencias bajas
    r = _CAMP_LOW[0] + t * (_CAMP_HIGH[0] - _CAMP_LOW[0])
    g = _CAMP_LOW[1] + t * (_CAMP_HIGH[1] - _CAMP_LOW[1])
    b = _CAMP_LOW[2] + t * (_CAMP_HIGH[2] - _CAMP_LOW[2])
    return (r, g, b)


def _fmt_fecha(fecha_iso: str) -> str:
    """'2026-06-25' → '25 junio 2026'"""
    meses = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} {meses[int(m)]} {y}"


def generar_snapshot(df: pd.DataFrame, fecha_iso: str, ruta_salida: Path) -> None:
    """
    Genera y guarda una imagen PNG con la tabla completa de probabilidades.

    Args:
        df:          DataFrame de simular_torneo_completo (ya ordenado por Campeón%)
        fecha_iso:   Fecha en formato 'YYYY-MM-DD'
        ruta_salida: Ruta completa del archivo PNG a crear
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    cols = [c for c in _COLS if c in df.columns]
    tabla = df[cols].copy().reset_index(drop=True)
    tabla.insert(0, "#", range(1, len(tabla) + 1))
    all_cols = list(tabla.columns)
    n_rows = len(tabla)
    n_cols = len(all_cols)

    vmax = df["Campeón%"].max() if "Campeón%" in df.columns else 1.0
    camp_vals = df["Campeón%"].values if "Campeón%" in df.columns else None
    camp_col_idx = all_cols.index("Campeón%") if "Campeón%" in all_cols else None

    # Formatear columnas numéricas
    for c in all_cols:
        if c.endswith("%"):
            tabla[c] = tabla[c].apply(lambda x: f"{x:.1f}%")

    # --- Dimensiones de la figura ---
    row_h_in = 0.36
    header_h_in = 0.52
    title_h_in = 0.7
    fig_h = title_h_in + header_h_in + n_rows * row_h_in + 0.3
    fig_w = 14

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")

    # Título
    title_frac = title_h_in / fig_h
    fig.text(0.5, 1 - 0.18 * title_frac / title_h_in,
             f"Mundial 2026 — Probabilidades al {_fmt_fecha(fecha_iso)}",
             ha="center", va="top",
             fontsize=15, fontweight="bold", color=_TITLE_FG)
    fig.text(0.5, 1 - 0.78 * title_frac / title_h_in,
             "Modelo Elo · Monte Carlo 100 000 simulaciones",
             ha="center", va="top",
             fontsize=9.5, color="#777777")

    # Área de la tabla (debajo del título)
    ax_bottom = 0.01
    ax_top    = 1 - title_frac
    ax = fig.add_axes([0.01, ax_bottom, 0.98, ax_top - ax_bottom])
    ax.axis("off")

    # Anchuras de columna: # / Selección / 6 porcentajes
    col_widths = [0.035, 0.20] + [0.127] * (n_cols - 2)

    tbl = ax.table(
        cellText=tabla.values,
        colLabels=all_cols,
        cellLoc="center",
        loc="upper center",
        colWidths=col_widths,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)

    total_h = ax_top - ax_bottom
    cell_h  = total_h / (n_rows + 1.5)

    # Cabecera
    for ci in range(n_cols):
        cell = tbl[0, ci]
        cell.set_facecolor(_HDR_BG)
        cell.set_text_props(color=_HDR_FG, fontweight="bold", fontsize=9.5)
        cell.set_edgecolor(_HDR_BG)
        cell.set_height(cell_h * 1.4)

    # Filas de datos
    for ri in range(1, n_rows + 1):
        base_bg = _ROW_ODD if ri % 2 == 1 else _ROW_EVEN
        val_camp = camp_vals[ri - 1] if camp_vals is not None else 0.0

        for ci in range(n_cols):
            cell = tbl[ri, ci]
            cell.set_edgecolor(_EDGE)
            cell.set_height(cell_h)

            if ci == camp_col_idx:
                cell.set_facecolor(_camp_color(val_camp, vmax))
            else:
                cell.set_facecolor(base_bg)

            if ci == 1:   # Selección en negrita
                cell.set_text_props(fontweight="bold", ha="left")
                cell.PAD = 0.04

    plt.savefig(
        ruta_salida,
        dpi=120,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.close(fig)
    logger.info("Snapshot guardado → %s", ruta_salida)
