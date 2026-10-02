"""Descarga los 5 archivos del proyecto a data/raw/ y verifica que llegaron completos.

Uso (desde la raíz del repo):
    uv run python scripts/descargar_datos.py
"""
import hashlib
import shutil
import ssl
import urllib.error
import urllib.request
from pathlib import Path

DESTINO = Path("data/raw")

# Cada URL apunta a un commit fijo: si el repo original cambia, tú sigues bajando lo mismo.
HANSEN = "https://raw.githubusercontent.com/netneurolab/hansen_receptors/f8b41da92a733f99368c1f39d4959731aa1316c1/data/PET_nifti_images"
ENIGMA = "https://raw.githubusercontent.com/saratheriver/enigma-extra/8c9df6e0c37c66830360ad553807326035e180ed/ahba"
ABAGEN = "https://raw.githubusercontent.com/rmarkello/abagen/dc4a007e4e902e51f97251390c8d1bbf7e58c6d3/abagen/data"

ARCHIVOS = {
    "CB1_omar_hc77_normandin.nii.gz": f"{HANSEN}/CB1_omar_hc77_normandin.nii.gz",
    "CB1_FMPEPd2_hc22_laurikainen.nii": f"{HANSEN}/CB1_FMPEPd2_hc22_laurikainen.nii",
    "allgenes_stable_r-1.csv": f"{ENIGMA}/allgenes_stable_r-1.csv",
    "atlas-desikankilliany.nii.gz": f"{ABAGEN}/atlas-desikankilliany.nii.gz",
    "atlas-desikankilliany.csv": f"{ABAGEN}/atlas-desikankilliany.csv",
}

SHA256 = {
    "CB1_omar_hc77_normandin.nii.gz": "6074b066eb3c223826064fe7cdbf1a4dcdec6810a3e569713267dca7c4865903",
    "CB1_FMPEPd2_hc22_laurikainen.nii": "6688599a37f4a18b3fd03230b556a90cd88dbd2d6743510c56dcdf123dbfc271",
    "allgenes_stable_r-1.csv": "52e61f0c9bdf18b2ed94eee363d7ff5295ff9c2933e1b63999637ce237b1b160",
    "atlas-desikankilliany.nii.gz": "0a28c93f5967f0892810219e68edb32abcaa9fd796a217096512fb0724c20d8a",
    "atlas-desikankilliany.csv": "d061418326874d62e9c8589e6741b1cdd282887afafe56670b921b424b9cd16b",
}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def bajar(url: str, destino: Path) -> None:
    """Baja con los certificados del sistema; si fallan (pasa en algunos Mac), usa los de certifi."""
    parcial = destino.with_name(destino.name + ".parcial")
    try:
        contexto = ssl.create_default_context()
        with urllib.request.urlopen(url, context=contexto) as r, open(parcial, "wb") as f:
            shutil.copyfileobj(r, f)
    except urllib.error.URLError as error:
        if not isinstance(error.reason, ssl.SSLCertVerificationError):
            raise
        import certifi  # viene instalado con jupyterlab

        contexto = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=contexto) as r, open(parcial, "wb") as f:
            shutil.copyfileobj(r, f)
    parcial.rename(destino)  # solo queda con su nombre final si se bajó completo


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, url in ARCHIVOS.items():
        archivo = DESTINO / nombre
        if not archivo.exists():
            print(f"Bajando {nombre} ...")
            bajar(url, archivo)
        esperado = SHA256.get(nombre)
        real = sha256(archivo)
        estado = "OK" if esperado in (None, real) else "NO COINCIDE: bórralo y vuelve a correr"
        print(f"{nombre:36s} {archivo.stat().st_size / 1e6:6.1f} MB  {estado}")


if __name__ == "__main__":
    main()