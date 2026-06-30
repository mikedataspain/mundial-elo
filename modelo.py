"""
modelo.py
Fórmulas Elo, draw rate interpolado y simulación Monte Carlo 100k iteraciones.
Vectorizado con NumPy para máximo rendimiento.
"""

import logging
from typing import Optional
import numpy as np
import pandas as pd

from config import DRAW_CALIBRATION, N_SIMULACIONES
from equivalencias import GRUPOS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. MATEMÁTICAS DE PARTIDO
# ---------------------------------------------------------------------------

def elo_win_prob(elo_a: float, elo_b: float) -> float:
    """P(victoria A) en campo neutral. We(A) = 1 / (10^(-(EloA-EloB)/400) + 1)"""
    return 1.0 / (10.0 ** (-(elo_a - elo_b) / 400.0) + 1.0)


def draw_rate(delta_elo: float) -> float:
    """P(empate) interpolada linealmente en función de |ΔElo|."""
    d = abs(delta_elo)
    pts = DRAW_CALIBRATION
    if d <= pts[0][0]:
        return pts[0][1]
    if d >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        if x0 <= d <= x1:
            t = (d - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


def probabilidades_partido(elo_a: float, elo_b: float) -> tuple[float, float, float]:
    """
    Devuelve (P_victoria_A, P_empate, P_victoria_B) para un partido en campo neutro.
    La suma es 1.0 por construcción.
    """
    we_a = elo_win_prob(elo_a, elo_b)
    dr   = draw_rate(abs(elo_a - elo_b))
    p_a  = we_a * (1.0 - dr)
    p_b  = (1.0 - we_a) * (1.0 - dr)
    return p_a, dr, p_b


# ---------------------------------------------------------------------------
# 2. VECTORIZACIÓN (numpy): simular n_sims partidos de golpe
# ---------------------------------------------------------------------------

def _we_vec(elos_a: np.ndarray, elos_b: np.ndarray) -> np.ndarray:
    """We(A) vectorizado."""
    return 1.0 / (10.0 ** (-(elos_a - elos_b) / 400.0) + 1.0)


def _draw_rate_vec(delta: np.ndarray) -> np.ndarray:
    """Draw rate vectorizado mediante np.interp con los puntos de calibración."""
    pts = DRAW_CALIBRATION
    xp = [p[0] for p in pts]
    fp = [p[1] for p in pts]
    return np.interp(np.abs(delta), xp, fp)


def _simular_resultado_grupo(
    rand: np.ndarray,          # (n_sims,)
    p_win_a: float,
    p_draw:  float,
) -> np.ndarray:
    """
    Devuelve array (n_sims,) con:
      0 → A gana, 1 → empate, 2 → B gana
    """
    out = np.where(rand < p_win_a, 0,
           np.where(rand < p_win_a + p_draw, 1, 2))
    return out.astype(np.int8)


# ---------------------------------------------------------------------------
# 3. SIMULACIÓN FASE DE GRUPOS
# ---------------------------------------------------------------------------

def _simular_marcador(
    resultado: np.ndarray,
    delta_elo: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Dado el resultado de cada simulación (0=A gana, 1=empate, 2=B gana),
    genera un marcador plausible. No altera las probabilidades de resultado;
    sirve únicamente para calcular GD y GF en el desempate de grupo.
    """
    n = len(resultado)
    mu_margin = 1.2 + abs(delta_elo) / 400.0

    a_gana = resultado == 0
    empate  = resultado == 1
    b_gana  = resultado == 2

    goles_a = np.zeros(n, dtype=np.int32)
    goles_b = np.zeros(n, dtype=np.int32)

    if empate.any():
        g = rng.poisson(1.1, n)
        goles_a[empate] = g[empate]
        goles_b[empate] = g[empate]

    if a_gana.any():
        concedidos = rng.poisson(0.7, n)
        margen = np.maximum(1, rng.poisson(mu_margin, n))
        goles_a[a_gana] = (concedidos + margen)[a_gana]
        goles_b[a_gana] = concedidos[a_gana]

    if b_gana.any():
        concedidos = rng.poisson(0.7, n)
        margen = np.maximum(1, rng.poisson(mu_margin, n))
        goles_b[b_gana] = (concedidos + margen)[b_gana]
        goles_a[b_gana] = concedidos[b_gana]

    return goles_a, goles_b

# Índices de partidos dentro de un grupo de 4 equipos (posición 0-3)
# Orden: JD1: 0v1, 2v3 | JD2: 0v2, 1v3 | JD3: 0v3, 1v2
GROUP_MATCHUPS = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]


def simular_fase_grupos(
    grupos: dict[str, list[str]],
    elos: dict[str, float],
    n_sims: int = N_SIMULACIONES,
    seed: Optional[int] = None,
    resultados_reales: Optional[dict] = None,
) -> dict:
    """
    Simula la fase de grupos completa (72 partidos × n_sims).

    Devuelve:
    {
      "clasificados_1":  dict[grupo → array(n_sims) con idx del 1º]
      "clasificados_2":  dict[grupo → array(n_sims) con idx del 2º]
      "clasificados_3":  dict[grupo → array(n_sims) con idx del 3º]
      "terceros_puntos": dict[grupo → array(n_sims) con puntos del 3º]
      "terceros_gd":     dict[grupo → array(n_sims) con GD del 3º]
      "terceros_gf":     dict[grupo → array(n_sims) con GF del 3º]
      "equipo_idx":      dict[nombre_equipo → índice global 0-47]
      "equipo_nombre":   lista de 48 nombres indexados
    }
    """
    rng = np.random.default_rng(seed)

    # Índice global de equipos
    todos = [eq for equipos in grupos.values() for eq in equipos]
    equipo_idx  = {eq: i for i, eq in enumerate(todos)}
    equipo_nombre = todos  # índice → nombre

    lista_grupos = list(grupos.keys())  # orden estable

    # Resultados por grupo
    c1 = {}   # 1º por grupo → array (n_sims,) de índice GLOBAL
    c2 = {}
    c3 = {}
    c3_pts = {}
    c3_gd  = {}
    c3_gf  = {}

    for grupo in lista_grupos:
        equipos_g = grupos[grupo]   # lista 4 equipos
        elos_g = np.array([elos.get(eq, 1500.0) for eq in equipos_g])
        n_eq = len(equipos_g)       # siempre 4

        # Generar resultados de 6 partidos × n_sims
        rand_all = rng.random((6, n_sims))   # shape (6, n_sims)
        puntos       = np.zeros((n_eq, n_sims), dtype=np.int32)
        gf           = np.zeros((n_eq, n_sims), dtype=np.int32)   # goles a favor (global)
        gc           = np.zeros((n_eq, n_sims), dtype=np.int32)   # goles en contra (global)
        h2h_pts_arr  = np.zeros((n_eq, n_eq, n_sims), dtype=np.int8)   # H2H: pts de i vs j
        h2h_ga_arr   = np.zeros((n_eq, n_eq, n_sims), dtype=np.int8)   # H2H: goles de i vs j

        for match_i, (ia, ib) in enumerate(GROUP_MATCHUPS):
            key = frozenset({equipos_g[ia], equipos_g[ib]})
            if resultados_reales and key in resultados_reales:
                pts_map = resultados_reales[key]
                puntos[ia] += pts_map.get(equipos_g[ia], 0)
                puntos[ib] += pts_map.get(equipos_g[ib], 0)
                goles_map = pts_map.get("goles", {})
                ga_r = int(goles_map.get(equipos_g[ia], 0))
                gb_r = int(goles_map.get(equipos_g[ib], 0))
                gf[ia] += ga_r;  gc[ia] += gb_r
                gf[ib] += gb_r;  gc[ib] += ga_r
                # H2H real: mismo resultado en todas las simulaciones
                if ga_r > gb_r:
                    h2h_pts_arr[ia, ib] = 3
                elif ga_r == gb_r:
                    h2h_pts_arr[ia, ib] = 1
                    h2h_pts_arr[ib, ia] = 1
                else:
                    h2h_pts_arr[ib, ia] = 3
                h2h_ga_arr[ia, ib] = ga_r
                h2h_ga_arr[ib, ia] = gb_r
            else:
                ea, eb = elos_g[ia], elos_g[ib]
                pa, pd, _ = probabilidades_partido(ea, eb)
                res_sim = _simular_resultado_grupo(rand_all[match_i], pa, pd)
                a_gana = (res_sim == 0)
                empate  = (res_sim == 1)
                b_gana  = (res_sim == 2)
                puntos[ia] += np.where(a_gana, 3, np.where(empate, 1, 0))
                puntos[ib] += np.where(b_gana, 3, np.where(empate, 1, 0))
                ga, gb = _simular_marcador(res_sim, ea - eb, rng)
                gf[ia] += ga;  gc[ia] += gb
                gf[ib] += gb;  gc[ib] += ga
                # H2H simulado: varía por simulación
                h2h_pts_arr[ia, ib] = np.where(a_gana, 3, np.where(empate, 1, 0)).astype(np.int8)
                h2h_pts_arr[ib, ia] = np.where(b_gana, 3, np.where(empate, 1, 0)).astype(np.int8)
                h2h_ga_arr[ia, ib]  = np.minimum(ga, 127).astype(np.int8)
                h2h_ga_arr[ib, ia]  = np.minimum(gb, 127).astype(np.int8)

        # Desempate FIFA: puntos → H2H pts → H2H GD → H2H GF → GD global → GF global
        gd = gf - gc

        # Máscara de emparejados en puntos (excluyendo diagonal)
        pts_i  = puntos[:, np.newaxis, :]        # (4, 1, n_sims)
        pts_j  = puntos[np.newaxis, :, :]        # (1, 4, n_sims)
        tied   = (pts_i == pts_j)                # (4, 4, n_sims)
        tied  &= ~np.eye(n_eq, dtype=bool)[:, :, np.newaxis]

        h2h_i32  = h2h_pts_arr.astype(np.int32)
        h2h_ga32 = h2h_ga_arr.astype(np.int32)
        h2h_gd32 = h2h_ga32 - h2h_ga32.transpose(1, 0, 2)   # goles_i_vs_j - goles_j_vs_i

        h2h_eff_pts = (h2h_i32  * tied).sum(axis=1)   # (4, n_sims)
        h2h_eff_gd  = (h2h_gd32 * tied).sum(axis=1)   # (4, n_sims), puede ser negativo
        h2h_eff_gf  = (h2h_ga32 * tied).sum(axis=1)   # (4, n_sims)

        scores = (
            puntos.astype(np.float64)      * 1e15
            + h2h_eff_pts.astype(np.float64) * 1e13
            + (h2h_eff_gd + 60).astype(np.float64) * 1e10
            + h2h_eff_gf.astype(np.float64)  * 1e7
            + (gd + 200).astype(np.float64)  * 1e4
            + gf.astype(np.float64)           * 1e1
        )

        # Ordenar de mayor a menor (argsort inverso)
        ranking = np.argsort(-scores, axis=0)   # (4, n_sims): ranking[pos, sim] = idx_local

        # Convertir índices locales → índices globales
        base = equipo_idx[equipos_g[0]]   # índice global del primer equipo del grupo
        idx_global = base + ranking        # broadcasting: base es escalar, ranking (4, n_sims)

        sims_idx = np.arange(n_sims)
        c1[grupo]    = idx_global[0]
        c2[grupo]    = idx_global[1]
        c3[grupo]    = idx_global[2]
        c3_pts[grupo] = puntos[ranking[2], sims_idx]
        c3_gd[grupo]  = gd[ranking[2],     sims_idx]
        c3_gf[grupo]  = gf[ranking[2],     sims_idx]

    return {
        "clasificados_1":  c1,
        "clasificados_2":  c2,
        "clasificados_3":  c3,
        "terceros_puntos": c3_pts,
        "terceros_gd":     c3_gd,
        "terceros_gf":     c3_gf,
        "equipo_idx":      equipo_idx,
        "equipo_nombre":   equipo_nombre,
        "n_sims":          n_sims,
    }


def seleccionar_mejores_terceros(
    grupos: dict[str, list[str]],
    res_grupos: dict,
    elos: dict[str, float],
    n_mejores: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Por cada simulación selecciona los n_mejores 3ºs de los 12 grupos.
    Devuelve:
      mejores_idx  (n_mejores, n_sims) — índices globales de equipo
      mejores_grp  (n_mejores, n_sims) — índice de grupo (0=A … 11=L)
    ordenados por puntos desc → GD → GF → Elo desc.
    """
    lista_grupos = list(grupos.keys())
    n_sims = res_grupos["n_sims"]
    eq_nombre = res_grupos["equipo_nombre"]

    # Construir matrices (12, n_sims)
    pts_mat = np.zeros((12, n_sims), dtype=np.int32)
    gd_mat  = np.zeros((12, n_sims), dtype=np.int32)
    gf_mat  = np.zeros((12, n_sims), dtype=np.int32)
    elo_mat = np.zeros((12, n_sims), dtype=np.float64)
    idx_mat = np.zeros((12, n_sims), dtype=np.int32)
    grp_mat = np.zeros((12, n_sims), dtype=np.int8)   # índice de grupo 0-11

    elos_arr = np.array([elos.get(eq_nombre[j], 1500.0) for j in range(len(eq_nombre))])

    for i, grupo in enumerate(lista_grupos):
        idx = res_grupos["clasificados_3"][grupo]
        idx_mat[i]  = idx
        pts_mat[i]  = res_grupos["terceros_puntos"][grupo]
        gd_mat[i]   = res_grupos["terceros_gd"][grupo]
        gf_mat[i]   = res_grupos["terceros_gf"][grupo]
        elo_mat[i]  = elos_arr[idx]
        grp_mat[i]  = i

    # Desempate: puntos → GD → GF → Elo
    scores = (
        pts_mat.astype(np.float64) * 1e7
        + (gd_mat + 200).astype(np.float64) * 1e4
        + gf_mat.astype(np.float64) * 1e2
        + elo_mat
    )

    sims_idx = np.arange(n_sims)
    ranking = np.argsort(-scores, axis=0)[:n_mejores]   # (n_mejores, n_sims)
    mejores_idx = idx_mat[ranking, sims_idx[np.newaxis, :]]   # (n_mejores, n_sims)
    mejores_grp = grp_mat[ranking, sims_idx[np.newaxis, :]]   # (n_mejores, n_sims)

    return mejores_idx, mejores_grp


# ---------------------------------------------------------------------------
# 4. SIMULACIÓN ELIMINATORIAS
# ---------------------------------------------------------------------------

# Cuadro oficial del Mundial 2026 (32 slots = 16 cruces × 2 equipos).
# Cada slot es ("g", grupo, posición) o ("t3", subconjunto_grupos).
# Orden: los cruces 0-1 alimentan el octavo P89, 2-3 → P90, ..., 14-15 → P96.
SLOTS_R32: list[tuple] = [
    # Cruce P74: 1ºE vs mejor 3º(A,B,C,D,F)
    ("g", "E", 1), ("t3", "ABCDF"),
    # Cruce P77: 1ºI vs mejor 3º(C,D,F,G,H)
    ("g", "I", 1), ("t3", "CDFGH"),
    # Cruce P73: 2ºA vs 2ºB  ← RSA vs CAN ya confirmado
    ("g", "A", 2), ("g", "B", 2),
    # Cruce P75: 1ºF vs 2ºC
    ("g", "F", 1), ("g", "C", 2),
    # Cruce P83: 2ºK vs 2ºL
    ("g", "K", 2), ("g", "L", 2),
    # Cruce P84: 1ºH vs 2ºJ
    ("g", "H", 1), ("g", "J", 2),
    # Cruce P81: 1ºD vs mejor 3º(B,E,F,I,J)
    ("g", "D", 1), ("t3", "BEFIJ"),
    # Cruce P82: 1ºG vs mejor 3º(A,E,H,I,J)
    ("g", "G", 1), ("t3", "AEHIJ"),
    # Cruce P76: 1ºC vs 2ºF
    ("g", "C", 1), ("g", "F", 2),
    # Cruce P78: 2ºE vs 2ºI
    ("g", "E", 2), ("g", "I", 2),
    # Cruce P79: 1ºA vs mejor 3º(C,E,F,H,I)
    ("g", "A", 1), ("t3", "CEFHI"),
    # Cruce P80: 1ºL vs mejor 3º(E,H,I,J,K)
    ("g", "L", 1), ("t3", "EHIJK"),
    # Cruce P86: 1ºJ vs 2ºH
    ("g", "J", 1), ("g", "H", 2),
    # Cruce P88: 2ºD vs 2ºG
    ("g", "D", 2), ("g", "G", 2),
    # Cruce P85: 1ºB vs mejor 3º(E,F,G,I,J)
    ("g", "B", 1), ("t3", "EFGIJ"),
    # Cruce P87: 1ºK vs mejor 3º(D,E,I,J,L)
    ("g", "K", 1), ("t3", "DEIJL"),
]

# Bracket completo R32 → R16 → QF → SF → F
# Cada par de R32 alimenta un partido de R16, y así sucesivamente.
# 16 partidos R32: M0..M15
# R16: M0 vs M1 → R16-0, M2 vs M3 → R16-1, ...
# QF: R16-0 vs R16-1 → QF-0, ...
# SF: QF-0 vs QF-1 → SF-0, QF-2 vs QF-3 → SF-1
BRACKET_R16 = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15)]
BRACKET_QF  = [(0, 1), (2, 3), (4, 5), (6, 7)]
BRACKET_SF  = [(0, 1), (2, 3)]


def _simular_knockout_match(
    idx_a: np.ndarray,   # (n_sims,) índices globales
    idx_b: np.ndarray,   # (n_sims,)
    elos_arr: np.ndarray,  # (n_equipos,) todos los Elos indexados globalmente
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Simula n_sims partidos de eliminatoria (sin empate, penaltis → We directa).
    Devuelve (n_sims,) con índices del ganador.
    """
    ea = elos_arr[idx_a]
    eb = elos_arr[idx_b]
    we_a = _we_vec(ea, eb)
    rand = rng.random(len(idx_a))
    ganadores = np.where(rand < we_a, idx_a, idx_b)
    return ganadores


def simular_torneo_completo(
    grupos:  dict[str, list[str]],
    elos:    dict[str, float],
    n_sims:  int = N_SIMULACIONES,
    seed:    Optional[int] = None,
    resultados_reales: Optional[dict] = None,
    resultados_reales_playoff: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Simula el torneo completo (grupos + eliminatorias) n_sims veces.

    Devuelve DataFrame con columnas:
    Selección | Grupos% | 1/32% | 1/16% | Cuartos% | Semis% | Campeón%
    """
    rng = np.random.default_rng(seed)
    logger.info(f"Iniciando Monte Carlo: {n_sims:,} simulaciones…")

    # --- Fase de grupos ---
    res = simular_fase_grupos(grupos, elos, n_sims=n_sims, seed=seed,
                              resultados_reales=resultados_reales)
    todos = res["equipo_nombre"]
    n_eq  = len(todos)
    eq_idx = res["equipo_idx"]

    # Elos como array indexado (mismo orden que todos[])
    elos_arr = np.array([elos.get(eq, 1500.0) for eq in todos], dtype=np.float64)

    # Contadores de avance por equipo y ronda
    cnt_grupos  = np.zeros(n_eq, dtype=np.int64)
    cnt_r32     = np.zeros(n_eq, dtype=np.int64)
    cnt_r16     = np.zeros(n_eq, dtype=np.int64)
    cnt_qf      = np.zeros(n_eq, dtype=np.int64)
    cnt_sf      = np.zeros(n_eq, dtype=np.int64)
    cnt_campeon = np.zeros(n_eq, dtype=np.int64)

    lista_grupos = list(grupos.keys())

    # Acumular clasificados de grupos
    for g in lista_grupos:
        for idx_arr in [res["clasificados_1"][g], res["clasificados_2"][g]]:
            np.add.at(cnt_grupos, idx_arr, 1)

    mejores_3, mejores_grp = seleccionar_mejores_terceros(grupos, res, elos)
    for row in range(8):
        np.add.at(cnt_grupos, mejores_3[row], 1)

    # --- Asignar las 8 mejores 3ªs a sus 8 slots t3 del cuadro ---
    # Cada slot t3 acepta la mejor 3ª cuyo grupo esté en el subconjunto.
    # Procesamos en orden; si hay empate de cobertura, el mejor-ranked gana.
    grp_letra_a_idx = {g: i for i, g in enumerate(lista_grupos)}

    t3_slot_defs = [
        (i, s[1]) for i, s in enumerate(SLOTS_R32) if s[0] == "t3"
    ]  # [(índice_en_SLOTS_R32, subconjunto_str), ...]

    assigned   = np.zeros((8, n_sims), dtype=bool)
    t3_filled  = {}   # índice_en_SLOTS_R32 → array (n_sims,) de idx global

    for slot_idx, subset_str in t3_slot_defs:
        subset_idxs = {grp_letra_a_idx[g] for g in subset_str}
        in_subset = np.isin(mejores_grp.astype(int), list(subset_idxs))  # (8, n_sims)
        available = in_subset & ~assigned

        chosen_rank = np.full(n_sims, -1, dtype=np.int32)
        for rank in range(8):
            can_use = available[rank] & (chosen_rank < 0)
            chosen_rank = np.where(can_use, rank, chosen_rank)

        # Fallback: si ningún grupo coincide (no debería ocurrir) usar el mejor libre
        no_match = chosen_rank < 0
        if no_match.any():
            for rank in range(8):
                fallback = no_match & ~assigned[rank]
                chosen_rank = np.where(fallback & (chosen_rank < 0), rank, chosen_rank)
                no_match = chosen_rank < 0

        chosen_team = mejores_3[0].copy()
        for rank in range(8):
            chosen_team = np.where(chosen_rank == rank, mejores_3[rank], chosen_team)

        for rank in range(8):
            assigned[rank] |= (chosen_rank == rank)

        t3_filled[slot_idx] = chosen_team

    # --- Construir 32 slots del bracket: (32, n_sims) ---
    bracket = np.zeros((32, n_sims), dtype=np.int32)
    for slot_idx, slot_def in enumerate(SLOTS_R32):
        if slot_def[0] == "g":
            _, grupo, pos = slot_def
            src = res["clasificados_1"][grupo] if pos == 1 else res["clasificados_2"][grupo]
            bracket[slot_idx] = src
        else:
            bracket[slot_idx] = t3_filled[slot_idx]

    # Pre-construir lookup de resultados playoff: (idx_menor, idx_mayor) → gan_idx
    # Permite bloquear por simulación individual, no solo cuando el slot es uniforme.
    # Necesario cuando uno de los slots es un t3 (varía entre simulaciones).
    _playoff_idx: dict[tuple, int] = {}
    if resultados_reales_playoff:
        for key_set, gan_nombre in resultados_reales_playoff.items():
            nombres_par = list(key_set)
            if gan_nombre not in eq_idx:
                logger.warning("Ganador playoff '%s' no encontrado en eq_idx", gan_nombre)
                continue
            idxs = [eq_idx.get(n) for n in nombres_par]
            if None in idxs:
                logger.warning("Equipo playoff no encontrado en eq_idx: %s", nombres_par)
                continue
            pair = (min(idxs), max(idxs))
            _playoff_idx[pair] = eq_idx[gan_nombre]

    def _aplicar_resultado_real(
        w: np.ndarray,
        slot_a: np.ndarray,
        slot_b: np.ndarray,
    ) -> np.ndarray:
        """Para cada simulación donde los dos equipos coinciden con un resultado conocido,
        fuerza el ganador real. Funciona aunque los slots no sean uniformes (t3)."""
        for (ia, ib), gan_idx in _playoff_idx.items():
            mask = ((slot_a == ia) & (slot_b == ib)) | ((slot_a == ib) & (slot_b == ia))
            if mask.any():
                w = np.where(mask, gan_idx, w)
        return w

    # --- R32 (16 partidos) ---
    winners_r32 = np.zeros((16, n_sims), dtype=np.int32)
    for m in range(16):
        slot_a, slot_b = bracket[2 * m], bracket[2 * m + 1]
        w = _simular_knockout_match(slot_a, slot_b, elos_arr, rng)
        if _playoff_idx:
            w = _aplicar_resultado_real(w, slot_a, slot_b)
        winners_r32[m] = w
        np.add.at(cnt_r32, w, 1)

    # --- R16 (8 partidos) ---
    winners_r16 = np.zeros((8, n_sims), dtype=np.int32)
    for i, (ma, mb) in enumerate(BRACKET_R16):
        sa, sb = winners_r32[ma], winners_r32[mb]
        w = _simular_knockout_match(sa, sb, elos_arr, rng)
        if _playoff_idx:
            w = _aplicar_resultado_real(w, sa, sb)
        winners_r16[i] = w
        np.add.at(cnt_r16, w, 1)

    # --- Cuartos (4 partidos) ---
    winners_qf = np.zeros((4, n_sims), dtype=np.int32)
    for i, (ma, mb) in enumerate(BRACKET_QF):
        sa, sb = winners_r16[ma], winners_r16[mb]
        w = _simular_knockout_match(sa, sb, elos_arr, rng)
        if _playoff_idx:
            w = _aplicar_resultado_real(w, sa, sb)
        winners_qf[i] = w
        np.add.at(cnt_qf, w, 1)

    # --- Semifinales (2 partidos) ---
    winners_sf = np.zeros((2, n_sims), dtype=np.int32)
    losers_sf  = np.zeros((2, n_sims), dtype=np.int32)
    for i, (ma, mb) in enumerate(BRACKET_SF):
        ta, tb = winners_qf[ma], winners_qf[mb]
        ea = elos_arr[ta]; eb = elos_arr[tb]
        we_a = _we_vec(ea, eb)
        r = rng.random(n_sims)
        w = np.where(r < we_a, ta, tb)
        l = np.where(r < we_a, tb, ta)
        if _playoff_idx:
            w_orig = w.copy()
            w = _aplicar_resultado_real(w, ta, tb)
            l = np.where(w != w_orig, np.where(w == ta, tb, ta), l)
        winners_sf[i] = w
        losers_sf[i]  = l
        np.add.at(cnt_sf, w, 1)

    # --- Final ---
    ta, tb = winners_sf[0], winners_sf[1]
    ea = elos_arr[ta]; eb = elos_arr[tb]
    we_a = _we_vec(ea, eb)
    r = rng.random(n_sims)
    campeon = np.where(r < we_a, ta, tb)
    np.add.at(cnt_campeon, campeon, 1)

    # --- Construir DataFrame de resultados ---
    df = pd.DataFrame({
        "Selección": todos,
        "Grupos%":   (cnt_grupos  / n_sims * 100).round(1),
        "1/32%":     (cnt_r32     / n_sims * 100).round(1),
        "1/16%":     (cnt_r16     / n_sims * 100).round(1),
        "Cuartos%":  (cnt_qf      / n_sims * 100).round(1),
        "Semis%":    (cnt_sf      / n_sims * 100).round(1),
        "Campeón%":  (cnt_campeon / n_sims * 100).round(1),
    })

    # Añadir grupo
    eq_to_grupo = {eq: g for g, eqs in grupos.items() for eq in eqs}
    df["Grupo"] = df["Selección"].map(eq_to_grupo)

    df = df.sort_values("Campeón%", ascending=False).reset_index(drop=True)
    logger.info("Monte Carlo completado.")
    return df


# ---------------------------------------------------------------------------
# 5. PROBABILIDADES INDIVIDUALES DE PARTIDO
# ---------------------------------------------------------------------------

def calcular_probabilidades_fase_grupos(
    partidos: list[dict],
    elos: dict[str, float],
) -> list[dict]:
    """
    Para cada partido del calendario, calcula P(Victoria1), P(Empate), P(Victoria2).
    Enriquece el dict del partido con los campos calculados y lo devuelve.
    """
    resultado = []
    for p in partidos:
        e1 = elos.get(p["equipo1"], 1500.0)
        e2 = elos.get(p["equipo2"], 1500.0)
        pa, pd_val, pb = probabilidades_partido(e1, e2)
        delta = e1 - e2
        favorito = p["equipo1"] if delta > 5 else (p["equipo2"] if delta < -5 else "Equilibrado")
        resultado.append({
            **p,
            "elo1":       round(e1, 0),
            "elo2":       round(e2, 0),
            "delta_elo":  round(delta, 0),
            "pct_vic1":   round(pa  * 100, 1),
            "pct_empate": round(pd_val * 100, 1),
            "pct_vic2":   round(pb  * 100, 1),
            "favorito":   favorito,
        })
    return resultado
