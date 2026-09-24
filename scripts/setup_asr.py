#!/usr/bin/env python3
"""
Instala el motor de transcripcion offline (sherpa-onnx + modelo Whisper ONNX).

Todo corre en tu maquina: el audio no sale de ahi.

Funciona en Windows, macOS y Linux. No necesita bash.

Uso:
    python setup_asr.py                 # modelo small (recomendado, ~1 GB)
    python setup_asr.py tiny            # mas rapido y liviano, menos preciso
    python setup_asr.py --check         # solo diagnostica, no instala

Donde queda el modelo:
    <ASR_HOME>/sherpa-onnx-whisper-<modelo>
    Por defecto ASR_HOME = ~/.whatsapp-deep-read
"""

from __future__ import annotations  # anotaciones perezosas: corre en Python 3.8+

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

MODELOS = ("tiny", "base", "small", "medium")
URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
       "sherpa-onnx-whisper-{m}.tar.bz2")

ES = sys.platform == "win32"


if sys.version_info < (3, 8):
    sys.exit("ERROR: este script necesita Python 3.8 o mas nuevo.\n"
             "Tenes " + sys.version.split()[0] + " en " + sys.executable + ".\n"
             "  macOS:    brew install python\n"
             "  Windows:  winget install Python.Python.3.12\n"
             "  Linux:    sudo apt install python3")


def home() -> Path:
    return Path(os.environ.get("ASR_HOME") or (Path.home() / ".whatsapp-deep-read"))


def say(msg=""):
    print(msg, flush=True)


def err(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- dependencias

def instrucciones_ffmpeg() -> str:
    if sys.platform == "darwin":
        return "  macOS:    brew install ffmpeg"
    if sys.platform == "win32":
        return ("  Windows:  winget install Gyan.FFmpeg\n"
                "            (o descargalo de https://ffmpeg.org/download.html\n"
                "             y agrega la carpeta bin al PATH)")
    return "  Linux:    sudo apt install ffmpeg     # o el gestor de tu distro"


def buscar_ffmpeg():
    """ffmpeg del sistema, o el que trae el paquete imageio-ffmpeg si esta."""
    ruta = shutil.which("ffmpeg")
    if ruta:
        return ruta
    try:
        import imageio_ffmpeg  # noqa: PLC0415
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def pip_install(paquete: str) -> bool:
    """pip install tolerante: reintenta con --break-system-packages si hace falta."""
    base = [sys.executable, "-m", "pip", "install", "-q", paquete]
    for extra in ([], ["--break-system-packages"]):
        try:
            subprocess.run(base + extra, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return False


def asegurar_paquete(modulo: str, paquete: str) -> bool:
    try:
        __import__(modulo)
        return True
    except ImportError:
        pass
    say(f"==> Instalando {paquete}")
    if not pip_install(paquete):
        return False
    try:
        __import__(modulo)
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------- descarga

def descargar(url: str, destino: Path):
    """Descarga con barra de progreso. Si la salida esta redirigida a un archivo
    o a un log, imprime un hito cada 10% en vez de repintar la linea."""
    tty = sys.stdout.isatty()
    ultimo = [-1]

    def progreso(bloques, tam_bloque, total):
        if total <= 0:
            return
        hechos = min(bloques * tam_bloque, total)
        pct = hechos * 100 // total
        mb, mb_total = hechos / 1048576, total / 1048576
        if tty:
            print(f"\r    {pct:3d}%  {mb:7.1f} / {mb_total:.1f} MB",
                  end="", flush=True)
        elif pct // 10 > ultimo[0]:
            ultimo[0] = pct // 10
            print(f"    {pct:3d}%  {mb:7.1f} / {mb_total:.1f} MB", flush=True)

    urllib.request.urlretrieve(url, destino, reporthook=progreso)
    if tty:
        print()


def extraer_seguro(tar_path: Path, destino: Path):
    """Extrae sin permitir rutas que se escapen del destino."""
    destino = destino.resolve()
    with tarfile.open(tar_path, "r:bz2") as tf:
        for m in tf.getmembers():
            objetivo = (destino / m.name).resolve()
            if not str(objetivo).startswith(str(destino)):
                raise RuntimeError(f"Entrada peligrosa en el tar: {m.name}")
            if m.issym() or m.islnk():
                raise RuntimeError(f"Enlace no permitido en el tar: {m.name}")
        try:
            tf.extractall(destino, filter="data")     # Python 3.12+
        except TypeError:
            tf.extractall(destino)                    # Python 3.9 - 3.11


# ---------------------------------------------------------------- diagnostico

def diagnostico() -> bool:
    ok = True
    say("Diagnostico del entorno")
    say(f"  Python        {sys.version.split()[0]}  ({sys.executable})")
    say(f"  Sistema       {sys.platform}")

    if sys.version_info < (3, 9):
        err("  ERROR: hace falta Python 3.9 o mas nuevo.")
        ok = False

    ff = buscar_ffmpeg()
    if ff:
        say(f"  ffmpeg        {ff}")
    else:
        err("  ffmpeg        AUSENTE")
        err(instrucciones_ffmpeg())
        err("  Alternativa sin instalar nada a mano:")
        err(f"    {Path(sys.executable).name} -m pip install imageio-ffmpeg")
        ok = False

    try:
        import sherpa_onnx
        say(f"  sherpa-onnx   {getattr(sherpa_onnx, '__version__', 'instalado')}")
    except ImportError:
        say("  sherpa-onnx   no instalado (lo instala este script)")

    h = home()
    say(f"  ASR_HOME      {h}")
    if h.exists():
        modelos = sorted(p.name.replace("sherpa-onnx-whisper-", "")
                         for p in h.glob("sherpa-onnx-whisper-*") if p.is_dir())
        say(f"  Modelos       {', '.join(modelos) if modelos else 'ninguno'}")
    else:
        say("  Modelos       ninguno")
    return ok


# ---------------------------------------------------------------- principal

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Instala el motor de transcripcion offline.")
    ap.add_argument("modelo", nargs="?", default="small", choices=MODELOS,
                    help="tamano del modelo Whisper (default: small)")
    ap.add_argument("--check", action="store_true",
                    help="solo diagnostica el entorno, no instala nada")
    args = ap.parse_args()

    if args.check:
        return 0 if diagnostico() else 1

    # --- dependencias ---
    if sys.version_info < (3, 9):
        err("ERROR: hace falta Python 3.9 o mas nuevo.")
        return 1

    if buscar_ffmpeg() is None:
        err("ERROR: falta ffmpeg y es imprescindible para leer los audios.")
        err(instrucciones_ffmpeg())
        err("")
        err("O, sin instalar nada a mano:")
        err(f"  {Path(sys.executable).name} -m pip install imageio-ffmpeg")
        return 1

    for modulo, paquete in (("numpy", "numpy"), ("sherpa_onnx", "sherpa-onnx")):
        if not asegurar_paquete(modulo, paquete):
            err(f"ERROR: no se pudo instalar {paquete}.")
            err("Proba con un entorno virtual:")
            err(f"  {Path(sys.executable).name} -m venv {home() / 'venv'}")
            if ES:
                err(f"  {home() / 'venv' / 'Scripts' / 'activate'}")
            else:
                err(f"  source {home() / 'venv' / 'bin' / 'activate'}")
            err("  pip install sherpa-onnx numpy")
            err("  # y volve a correr este script con ese entorno activado")
            return 1

    # --- modelo ---
    destino = home()
    carpeta = destino / f"sherpa-onnx-whisper-{args.modelo}"
    destino.mkdir(parents=True, exist_ok=True)

    requeridos = [f"{args.modelo}-encoder.int8.onnx",
                  f"{args.modelo}-decoder.int8.onnx",
                  f"{args.modelo}-tokens.txt"]

    if carpeta.is_dir() and all((carpeta / f).exists() for f in requeridos):
        say(f"==> El modelo {args.modelo} ya esta descargado")
    else:
        url = URL.format(m=args.modelo)
        say(f"==> Descargando whisper-{args.modelo} (puede tardar varios minutos)")
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = Path(tmp) / f"whisper-{args.modelo}.tar.bz2"
            try:
                descargar(url, tar_path)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                err(f"ERROR: no se pudo descargar el modelo.\n  {url}\n  {e}")
                err(f"Bajalo a mano, descomprimilo dentro de {destino} y volve a correr.")
                return 1
            say("==> Descomprimiendo")
            try:
                extraer_seguro(tar_path, destino)
            except Exception as e:
                err(f"ERROR al descomprimir: {e}")
                return 1

    faltan = [f for f in requeridos if not (carpeta / f).exists()]
    if faltan:
        err(f"ERROR: la descarga quedo incompleta. Faltan en {carpeta}:")
        for f in faltan:
            err(f"  - {f}")
        return 1

    say("")
    say(f"==> Listo. Modelo en {carpeta}")
    say("    Para transcribir:")
    say(f"      {Path(sys.executable).name} scripts/transcribe.py <carpeta> "
        f"--model {args.modelo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
