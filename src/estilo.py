"""Colores y estilo compartidos por las figuras del proyecto.

Azul, naranja y aqua son los tres primeros colores de una paleta validada para
daltonismo; en una misma gráfica no uses más de esos tres para distinguir grupos.
"""
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

FONDO = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRIS = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"

AZUL = "#2a78d6"
NARANJA = "#eb6834"
AQUA = "#1baf7a"

# Magnitud (densidad de receptor): un solo tono, de claro a oscuro.
SECUENCIAL = LinearSegmentedColormap.from_list(
    "azules", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)
# Valores con signo (z-scores, residuos): azul y rojo con gris neutro en el cero.
DIVERGENTE = LinearSegmentedColormap.from_list(
    "azul_gris_rojo",
    ["#104281", "#3987e5", "#b7d3f6", "#f0efec", "#f5b4b3", "#e34948", "#9e2120"],
)
AZUL_OSCURO, ROJO_OSCURO = "#1c5cab", "#c23a39"


def aplicar_estilo() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": FONDO,
            "axes.facecolor": FONDO,
            "savefig.facecolor": FONDO,
            "axes.edgecolor": EJE,
            "axes.linewidth": 0.8,
            "axes.labelcolor": TINTA_2,
            "axes.titlecolor": TINTA,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": GRIS,
            "ytick.color": GRIS,
            "xtick.labelcolor": TINTA_2,
            "ytick.labelcolor": TINTA_2,
            "text.color": TINTA,
            "font.size": 10,
            "legend.frameon": False,
            "lines.linewidth": 2,
            "lines.solid_capstyle": "round",
            "grid.color": REJILLA,
            "grid.linewidth": 0.8,
            "grid.linestyle": "-",
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        }
    )