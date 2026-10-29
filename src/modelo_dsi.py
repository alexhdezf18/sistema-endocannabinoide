"""Modelo mínimo de la supresión de la inhibición inducida por despolarización (DSI).

Cadena que simula, de la neurona que recibe la señal a la que la manda:
  despolarización -> Ca2+ postsináptico -> DAGLα fabrica 2-AG -> el 2-AG viaja hacia atrás
  -> activa CB1 en la terminal inhibitoria -> baja la liberación de GABA (el IPSC se achica)
  MAGL (y en menor medida ABHD6/12) degrada el 2-AG; FAAH degrada la anandamida (AEA).

Unidades: tiempo en segundos, Ca2+ en µM; 2-AG y AEA en múltiplos de su Kd en CB1.
Es un modelo fenomenológico: pocas piezas, cada una con un papel que se puede poner a prueba.
"""
from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit


@dataclass(frozen=True)
class Parametros:
    # Calcio postsináptico
    ca_reposo: float = 0.05     # µM
    tau_ca: float = 2.0         # s, cuánto tarda en bajar el Ca2+ después del pulso
    j_ca: float = 2.0           # µM/s que entran mientras dura la despolarización
    k_ca: float = 2.0           # µM de Ca2+ para media actividad de DAGLα
    n_hill: float = 2.0         # cooperatividad del Ca2+ (Zachariou et al. 2013 usan 2)
    # 2-AG
    v_dagl: float = 1.5         # Kd/s, síntesis máxima por DAGLα
    p_basal: float = 0.002      # Kd/s, síntesis de fondo (también depende de DAGL)
    k_magl: float = 0.07        # 1/s, degradación por MAGL
    k_otras: float = 0.035      # 1/s, ABHD6, ABHD12 y difusión
    # Anandamida
    p_aea: float = 0.002        # Kd/s, síntesis tónica por NAPE-PLD (no depende del pulso)
    k_faah: float = 0.1         # 1/s, degradación por FAAH
    k_aea_otras: float = 0.02   # 1/s, lo que queda sin FAAH
    eficacia_aea: float = 0.5   # agonista parcial de CB1
    # CB1 y liberación
    s_max: float = 0.413        # supresión con CB1 al máximo (WIN 2 µM en Pan et al. 2011)
    f_cb1: float = 1.0          # fracción de CB1 funcional
    # Manipulaciones: fracción bloqueada (0 = intacto, 1 = bloqueo total)
    bloqueo_dagl: float = 0.0
    bloqueo_magl: float = 0.0
    bloqueo_faah: float = 0.0


def _tasas(p: Parametros):
    k_2ag = p.k_magl * (1 - p.bloqueo_magl) + p.k_otras
    k_aea = p.k_faah * (1 - p.bloqueo_faah) + p.k_aea_otras
    return k_2ag, k_aea


def estado_basal(p: Parametros) -> np.ndarray:
    """Ca2+, 2-AG y AEA en equilibrio antes del pulso."""
    k_2ag, k_aea = _tasas(p)
    return np.array([p.ca_reposo, p.p_basal * (1 - p.bloqueo_dagl) / k_2ag, p.p_aea / k_aea])


def _derivadas(t, y, p: Parametros, pulso: bool):
    ca, e, a = y
    k_2ag, k_aea = _tasas(p)
    dca = (p.ca_reposo - ca) / p.tau_ca + (p.j_ca if pulso else 0.0)
    act_dagl = ca**p.n_hill / (ca**p.n_hill + p.k_ca**p.n_hill)
    de = (1 - p.bloqueo_dagl) * (p.v_dagl * act_dagl + p.p_basal) - k_2ag * e
    da = p.p_aea - k_aea * a
    return [dca, de, da]


def supresion(e, a, p: Parametros):
    """Fracción de la liberación de GABA que se pierde; 2-AG y AEA compiten por CB1."""
    activacion = (e + p.eficacia_aea * a) / (1 + e + a)
    return p.s_max * p.f_cb1 * activacion


def simular(p: Parametros, duracion_pulso=5.0, t_final=90.0, dt=0.05):
    """Pulso de despolarización que empieza en t = 0. Regresa t, Ca2+, 2-AG, AEA e IPSC relativo."""
    y0 = estado_basal(p)
    tramos = [(0.0, duracion_pulso, True), (duracion_pulso, t_final, False)]
    ts, ys = [], []
    for t0, t1, pulso in tramos:
        malla = np.linspace(t0, t1, int(round((t1 - t0) / dt)) + 1)
        sol = solve_ivp(_derivadas, (t0, t1), y0, t_eval=malla, args=(p, pulso),
                        method="LSODA", rtol=1e-8, atol=1e-10)
        ts.append(sol.t[:-1] if t1 < t_final else sol.t)
        ys.append(sol.y[:, :-1] if t1 < t_final else sol.y)
        y0 = sol.y[:, -1]
    t = np.concatenate(ts)
    ca, e, a = np.concatenate(ys, axis=1)
    base = 1 - supresion(*estado_basal(p)[1:], p)
    ipsc = (1 - supresion(e, a, p)) / base  # relativo a los IPSC de antes del pulso
    return {"t": t, "ca": ca, "2ag": e, "aea": a, "ipsc": ipsc}


def medir_dsi(sim, duracion_pulso=5.0, cada=4.0, retraso=1.0):
    """Mide la DSI como en el experimento: un IPSC cada 4 s, el primero 1 s después del pulso.

    magnitud = % de caída del primer IPSC; tau = constante de recuperación (ajuste exponencial).
    """
    t_ipsc = np.arange(duracion_pulso + retraso, sim["t"][-1], cada)
    ipsc = np.interp(t_ipsc, sim["t"], sim["ipsc"])
    magnitud = 100 * (1 - ipsc[0])
    if magnitud < 1:  # sin DSI no hay recuperación que ajustar
        return {"magnitud": magnitud, "tau": np.nan, "t_ipsc": t_ipsc, "ipsc": ipsc}
    x = t_ipsc - t_ipsc[0]
    exp = lambda x, m, tau: 1 - m * np.exp(-x / tau)
    try:
        (m, tau), _ = curve_fit(exp, x, ipsc, p0=(1 - ipsc[0], 10.0), bounds=([0, 0.1], [2, 500]), max_nfev=10_000)
    except RuntimeError:  # el ajuste no convergió: se reporta como faltante
        tau = np.nan
    return {"magnitud": magnitud, "tau": tau, "t_ipsc": t_ipsc, "ipsc": ipsc}


# Condiciones experimentales como cambios a los parámetros calibrados
def condiciones(p: Parametros, f_cb1_ko: float):
    return {
        "Control": p,
        "Antagonista de CB1": replace(p, f_cb1=0.0),
        "Sin DAGLα": replace(p, bloqueo_dagl=1.0),
        "MAGL bloqueada (agudo)": replace(p, bloqueo_magl=1.0),
        "Sin MAGL (crónico)": replace(p, bloqueo_magl=1.0, f_cb1=f_cb1_ko),
        "FAAH bloqueada": replace(p, bloqueo_faah=1.0),
    }