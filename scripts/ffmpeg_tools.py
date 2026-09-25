#!/usr/bin/env python3
"""
Encuentra ffmpeg y ffprobe, vengan de donde vengan.

Orden de busqueda:

1. El ffmpeg del sistema (brew, apt, winget). Es el mejor: trae ffprobe.
2. El que instala el paquete de Python `imageio-ffmpeg`. No necesita Homebrew
   ni permisos de administrador, y por eso es la salida para quien no quiere
   pelear con un gestor de paquetes. Trae ffmpeg pero NO trae ffprobe.

Por eso ningun script puede depender de ffprobe para funcionar: lo usa si esta
y se arregla sin el si no esta.
"""

from __future__ import annotations

import shutil


def ffmpeg() -> str | None:
    """Ruta a un ffmpeg utilizable, o None."""
    ruta = shutil.which("ffmpeg")
    if ruta:
        return ruta
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def ffprobe() -> str | None:
    """Ruta a ffprobe, o None. imageio-ffmpeg no lo trae."""
    return shutil.which("ffprobe")


def instrucciones() -> str:
    """Que decirle al usuario cuando no hay ffmpeg de ninguna de las dos formas."""
    import sys
    from pathlib import Path
    py = Path(sys.executable).name
    if sys.platform == "darwin":
        sistema = "  macOS:    brew install ffmpeg"
    elif sys.platform == "win32":
        sistema = ("  Windows:  winget install Gyan.FFmpeg\n"
                   "            (o bajalo de https://ffmpeg.org/download.html\n"
                   "             y agrega su carpeta bin al PATH)")
    else:
        sistema = "  Linux:    sudo apt install ffmpeg     # o el gestor de tu distro"
    return (
        "Falta ffmpeg, que es imprescindible para leer los audios.\n\n"
        "La forma mas simple, sin instalar nada a mano:\n"
        f"  {py} -m pip install imageio-ffmpeg\n\n"
        "O el ffmpeg del sistema, que ademas trae ffprobe y es mas completo:\n"
        + sistema
    )
