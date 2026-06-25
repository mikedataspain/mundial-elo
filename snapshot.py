"""
snapshot.py
Genera una imagen PNG de la tabla de probabilidades del día.
Estilo visual idéntico al pronosticador web: gradiente por columna,
"—" para ceros, cabecera oscura.
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # sin pantalla (necesario en CI/servidor)
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

# Nombres de columna CSV → etiqueta de display
_COL_MAP = {
    "Selección": "SELECCIÓN",
    "Grupos%":   "GRUPOS",
    "1/32%":     "R32",
    "1/16%":     "OCTAVOS",
    "Cuartos%":  "CUARTOS",
    "Semis%":    "SEMIS",
    "Campeón%":  "CAMPEÓN",
}

_PCT_COLS = ["Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"]

# Gradiente igual al de la web: blanco → amarillo → naranja → rojo → granate → morado oscuro
_GRAD = [
    (0.00, (1.00, 1.00, 1.00)),
    (0.04, (1.00, 0.97, 0.78)),
    (0.14, (1.00, 0.88, 0.30)),
    (0.30, (1.00, 0.56, 0.08)),
    (0.52, (0.88, 0.15, 0.15)),
    (0.76, (0.56, 0.04, 0.28)),
    (1.00, (0.10, 0.04, 0.18)),
]


def _color_cell(val: float, col_max: float) -> tuple:
    """Devuelve color RGB (0-1) proporcional a val/col_max según el gradiente."""
    if col_max <= 0 or val <= 0:
        return (1.0, 1.0, 1.0)
    t = min(val / col_max, 1.0)
    for i in range(len(_GRAD) - 1):
        t0, c0 = _GRAD[i]
        t1, c1 = _GRAD[i + 1]
        if t <= t1:
            s = (t - t0) / (t1 - t0)
            return tuple(c0[j] + s * (c1[j] - c0[j]) for j in range(3))
    return _GRAD[-1][1]


def _text_color(bg: tuple) -> str:
    """Blanco sobre fondos oscuros, oscuro sobre fondos claros."""
    lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    return "white" if lum < 0.50 else "#1a1a1a"


def _fmt_fecha(fecha_iso: str) -> str:
    meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} {meses[int(m)]} {y}"


def generar_snapshot(df: pd.DataFrame, fecha_iso: str, ruta_salida: Path) -> None:
    """
    Genera y guarda la imagen PNG de la tabla completa.

    Args:
        df:          DataFrame de simular_torneo_completo (ordenado por Campeón%)
        fecha_iso:   Fecha en formato 'YYYY-MM-DD'
        ruta_salida: Ruta completa del archivo PNG a guardar
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    # Columnas disponibles en el orden correcto
    src_cols  = ["Selección"] + [c for c in _PCT_COLS if c in df.columns]
    raw_nums  = {c: df[c].values.copy() for c in _PCT_COLS if c in df.columns}
    col_maxes = {c: float(df[c].max()) for c in _PCT_COLS if c in df.columns}

    tabla = df[src_cols].copy().reset_index(drop=True)
    n_rows = len(tabla)

    # Formatear: "—" para 0.0%, "X.X%" para el resto
    for c in _PCT_COLS:
        if c in tabla.columns:
            tabla[c] = tabla[c].apply(lambda v: "—" if v == 0.0 else f"{v:.1f}%")

    # Añadir nº de ranking al frente
    tabla.insert(0, "#", range(1, n_rows + 1))
    display_cols = ["#"] + [_COL_MAP.get(c, c) for c in src_cols]
    n_cols = len(display_cols)

    # --- Dimensiones ---
    row_h_in   = 0.30
    header_h_in = 0.44
    titles_h_in = 0.68
    fig_h = titles_h_in + header_h_in + n_rows * row_h_in + 0.15
    fig_w = 15.5

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")

    # Títulos
    tf = titles_h_in / fig_h
    fig.text(0.013, 1 - 0.12 / fig_h,
             "El pronosticador del Mundial 2026",
             ha="left", va="top",
             fontsize=14, fontweight="bold", color="#1a1a2e")
    fig.text(0.013, 1 - 0.42 / fig_h,
             f"Probabilidades de pasar cada ronda al {_fmt_fecha(fecha_iso)} · "
             "Predicciones basadas en el Modelo Elo-MARCA",
             ha="left", va="top",
             fontsize=9.5, color="#666666")

    # Eje de la tabla
    ax = fig.add_axes([0.005, 0.005, 0.990, 1 - tf - 0.008])
    ax.axis("off")

    # Anchuras: # / SELECCIÓN / 6 columnas %
    pct_w = (1 - 0.030 - 0.195) / max(n_cols - 2, 1)
    col_w = [0.030, 0.195] + [pct_w] * (n_cols - 2)

    tbl = ax.table(
        cellText=tabla.values,
        colLabels=display_cols,
        cellLoc="center",
        loc="upper center",
        colWidths=col_w,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.8)

    avail_h    = 1 - 0.01
    hdr_h      = avail_h / (n_rows + 1.8) * 1.6
    data_h     = (avail_h - hdr_h) / n_rows

    # ── Cabecera ────────────────────────────────────────────────────────────
    hdr_bg = (0.10, 0.10, 0.18)
    for ci in range(n_cols):
        cell = tbl[0, ci]
        cell.set_facecolor(hdr_bg)
        cell.set_text_props(color="white", fontweight="bold", fontsize=9)
        cell.set_edgecolor((0.20, 0.20, 0.30))
        cell.set_height(hdr_h)

    # ── Filas de datos ───────────────────────────────────────────────────────
    # Construir reverse map display_col → src_col para coloreado
    rev_map = {v: k for k, v in _COL_MAP.items()}

    for ri in range(1, n_rows + 1):
        for ci in range(n_cols):
            cell = tbl[ri, ci]
            cell.set_height(data_h)
            cell.set_edgecolor((0.88, 0.88, 0.88))

            col_label = display_cols[ci]
            orig_col  = rev_map.get(col_label)

            if orig_col and orig_col in raw_nums:
                val = float(raw_nums[orig_col][ri - 1])
                bg  = _color_cell(val, col_maxes[orig_col])
                fg  = _text_color(bg)
                cell.set_facecolor(bg)
                cell.set_text_props(color=fg, fontweight="bold", fontsize=9)
            else:
                # Columna # o SELECCIÓN: fondo neutro alterno
                bg = (0.96, 0.96, 0.97) if ri % 2 == 1 else (1.0, 1.0, 1.0)
                cell.set_facecolor(bg)
                cell.set_text_props(color="#1a1a1a", fontsize=8.8)

            # SELECCIÓN: alineada a la izquierda con sangría
            if col_label == "SELECCIÓN":
                cell.get_text().set_ha("left")
                cell.PAD = 0.025

    # ── Guardar ─────────────────────────────────────────────────────────────
    plt.savefig(
        ruta_salida,
        dpi=120,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.close(fig)
    logger.info("Snapshot guardado → %s", ruta_salida)
