#!/usr/bin/env python3
"""
Transcribe audios (y bandas de audio de video) a texto, offline.

Uso:
    python3 transcribe.py archivo1.opus archivo2.opus ...
    python3 transcribe.py /ruta/carpeta --glob "*.opus"
    python3 transcribe.py video.mp4            # extrae el audio solo

Opciones:
    --model small|base|medium|tiny   (default: small)
    --lang es                        (default: es)
    --out transcripciones.json       (default: ./transcripciones.json, se fusiona)

Todo corre local: el audio no sale de tu maquina.

IMPORTANTE: correr SIEMPRE en primer plano, nunca con & ni nohup. Los procesos
en segundo plano se congelan entre llamadas de herramienta y se pierde el
trabajo. Si hay mucho audio, invocar este script varias veces con lotes de
2 a 3 minutos cada uno; los resultados se van fusionando en el mismo JSON.
"""

from __future__ import annotations  # anotaciones perezosas: corre en Python 3.8+

import argparse
import glob as globmod
import json
import os
import shutil
import subprocess
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ffmpeg_tools  # noqa: E402

import numpy as np

def _salida_utf8():
    """Evita que un emoji en un nombre tumbe la corrida en Windows.

    Windows no usa UTF-8 para la salida estandar: usa la pagina de codigos
    del sistema, que en espanol es cp1252. Mientras la salida va a una
    consola de verdad, Python la escribe en Unicode y no pasa nada; pero en
    cuanto se redirige a un archivo o a una tuberia —que es exactamente como
    la corre un agente— vuelve a cp1252, y ahi un nombre como "Fer 🛠️"
    revienta con UnicodeEncodeError y un traceback.

    Un grupo de WhatsApp sin un solo emoji en los nombres es la excepcion,
    asi que esto no es un caso raro: es el caso normal en Windows.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass          # Python < 3.7 o un flujo que no se puede reconfigurar


_salida_utf8()


CHUNK_SECONDS = 25     # Whisper trabaja en ventanas de 30 s; 25 deja margen
OVERLAP_SECONDS = 2    # solape entre bloques, para no cortar palabras
SR = 16000

# Extensiones que tiene sentido mandarle a ffmpeg. Todo lo demas que haya en la
# carpeta del export —el _chat.txt, el inventario.json, las fotos, los PDF— no
# es audio ni video y NO debe reportarse como "archivo ilegible": decir que el
# _chat.txt no se pudo leer es una alarma falsa sobre el archivo mas importante
# del export, y ademas ensucia el documento final con huecos inventados.
MEDIA = (".opus", ".ogg", ".oga", ".m4a", ".mp3", ".aac", ".wav", ".amr",
         ".flac", ".wma", ".caf", ".aiff", ".aif", ".3gp", ".3gpp",
         ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg")


def es_media(nombre: str) -> bool:
    return os.path.splitext(nombre)[1].lower() in MEDIA


def to_wav(src, workdir):
    """Devuelve (ruta_wav, motivo). Si no hay wav, motivo dice por que.

    Distinguir el motivo importa: un GIF no tiene pista de audio y esta
    perfectamente sano, pero decir de el "archivo vacio o truncado" es una
    acusacion falsa que ademas mete un hueco inventado en el documento. En un
    grupo de WhatsApp los GIF son moneda corriente.
    """
    exe = ffmpeg_tools.ffmpeg()
    if exe is None:
        raise SystemExit(ffmpeg_tools.instrucciones())
    os.makedirs(workdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(workdir, base + ".wav")
    if not os.path.exists(dst):
        # Sin check=True a proposito: un adjunto truncado o de cero bytes es
        # moneda corriente (WhatsApp solo exporta lo que sigue descargado en
        # el telefono). Con check=True, UN archivo roto mataba toda la corrida
        # con un traceback y se perdia todo lo transcripto hasta ahi.
        r = subprocess.run(
            [exe, "-y", "-loglevel", "error", "-i", src,
             "-vn", "-ar", str(SR), "-ac", "1", dst],
            capture_output=True)
        if r.returncode != 0 or not os.path.exists(dst) \
                or os.path.getsize(dst) == 0:
            err = (r.stderr or b"").decode("utf-8", "replace").lower()
            if "does not contain any stream" in err or \
                    "output file #0 does not contain" in err or \
                    "no audio" in err:
                return None, "sin_audio"
            # ffmpeg abrio el archivo y leyo su cabecera? entonces el archivo
            # esta sano y lo unico que falta es la pista de audio.
            if r.returncode == 0 or "invalid data" not in err:
                sano = subprocess.run(
                    [exe, "-v", "error", "-i", src, "-f", "null", "-"],
                    capture_output=True)
                if sano.returncode == 0:
                    return None, "sin_audio"
            return None, "roto"
    return dst, None


def unir(partes):
    """Pega los bloques quitando lo que se repite por el solape.

    Los bloques se solapan 2 s para no cortar palabras, asi que el final de
    uno y el principio del siguiente dicen lo mismo. Sin esto, cada borde
    deja una frase repetida en la transcripcion.

    El motor no transcribe dos veces igual el mismo audio: en el borde dice
    "los adjuntos los lee entero" de un lado y "los adjuntos los lee enteros"
    del otro. Comparar palabra por palabra exige una coincidencia perfecta que
    casi nunca ocurre, y entonces no corta nada y la frase queda duplicada. Por
    eso la comparacion es por parecido y no por igualdad, con un umbral mas
    exigente cuanto mas corto es el tramo: con dos palabras, coincidir no
    prueba nada.
    """
    import difflib

    def norm(w):
        return "".join(c for c in w.lower() if c.isalnum())

    def igualitas(x, y):
        """Dos palabras que el motor escribio distinto pero son la misma."""
        if x == y:
            return True
        return difflib.SequenceMatcher(None, x, y).ratio() >= 0.7

    def parecido(a, b):
        """Compara posicion por posicion, no por subsecuencia comun.

        Un tramo corrido dos palabras comparte casi las mismas palabras y por
        subsecuencia puntua alto, asi que el corte se comia texto bueno.
        Posicion por posicion, el desalineo se nota: el solape verdadero
        alinea en su largo exacto y el corrido se desploma."""
        return sum(igualitas(x, y) for x, y in zip(a, b)) / float(len(a))

    acc = []
    for parte in partes:
        pal = parte.split()
        if not pal:
            continue
        if acc:
            # El solape es de 2 s: en habla rapida son unas 10 palabras. El
            # tope de 20 evita que un parecido casual se coma texto real.
            maximo = min(len(acc), len(pal), 20)
            corte, mejor = 0, 0.0
            # Se evaluan TODOS los largos y gana el que mejor alinea, no el
            # primero que pasa: el tramo corrido tambien supera el umbral, y
            # si se corta ahi desaparecen las palabras que lo desplazaban.
            for k in range(2, maximo + 1):
                a = [norm(w) for w in acc[-k:]]
                b = [norm(w) for w in pal[:k]]
                if a == b:
                    puntaje = 1.0
                elif k < 3:
                    continue          # con dos palabras, parecerse no prueba nada
                else:
                    puntaje = parecido(a, b)
                umbral = 0.75 if k >= 5 else 0.99
                if puntaje >= umbral and puntaje >= mejor:
                    corte, mejor = k, puntaje
            pal = pal[corte:]
        acc += pal
    return recortar_bucles(" ".join(acc))


def recortar_bucles(texto, minimo=5):
    """Corta las rachas donde el motor repite una palabra en loop.

    Whisper se traba: ante silencio, ruido de fondo o el final del audio,
    entrega la misma palabra decenas de veces seguidas.

    Eso no es algo que alguien dijo: es texto inventado por el motor. Dejarlo
    pasar pone en boca de una persona lo que nunca dijo, y lo pone entre
    comillas en el documento. Se recorta a dos y se marca, para que el que lee
    sepa que ahi hubo un tramo que el motor no pudo resolver.
    """
    pal = texto.split()
    if not pal:
        return texto
    out, i = [], 0
    while i < len(pal):
        j = i
        while j + 1 < len(pal) and norm_pal(pal[j + 1]) == norm_pal(pal[i]) \
                and norm_pal(pal[i]):
            j += 1
        racha = j - i + 1
        if racha >= minimo:
            out += [pal[i], pal[i],
                    f"[el motor repitio esta palabra {racha} veces seguidas; "
                    f"tramo no resuelto]"]
        else:
            out += pal[i:j + 1]
        i = j + 1
    return " ".join(out)


def norm_pal(w):
    return "".join(c for c in w.lower() if c.isalnum())


def read_wave(path):
    with wave.open(path) as w:
        data = w.readframes(w.getnframes())
    return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0


def duration(path):
    """Duracion en segundos leida del wav ya convertido.

    Antes esto llamaba a ffprobe, pero el ffmpeg que instala pip
    (imageio-ffmpeg) no trae ffprobe. El wav lo tenemos delante y el modulo
    wave de la biblioteca estandar alcanza: una dependencia menos."""
    try:
        with wave.open(path) as w:
            return round(w.getnframes() / float(w.getframerate()), 1)
    except Exception:
        return None


CON_VALOR = {"--glob", "--model", "--lang", "--out", "--model-dir"}


def ordenar_argumentos(argv):
    """Separa opciones de rutas y mete un `--` en el medio.

    WhatsApp exporta archivos cuyo nombre empieza con guion
    (`-0000010-AUDIO-2026-09-25.opus`). argparse los toma por opciones y la
    corrida muere con "the following arguments are required: inputs" antes de
    transcribir nada, y rompe justo el comando por lotes que documenta el
    SKILL.md.

    Pasar las rutas despues de `--` lo resuelve, pero no se le puede pedir a
    quien usa el skill que se acuerde: lo arregla el script.
    """
    opciones, rutas, i = [], [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            rutas += argv[i + 1:]
            break
        if a in ("-h", "--help"):
            opciones.append(a)
            i += 1
        elif a in CON_VALOR:
            opciones += argv[i:i + 2]
            i += 2
        elif a.startswith("--"):
            opciones.append(a)
            i += 1
        else:
            rutas.append(a)      # todo lo demas es una ruta, empiece como empiece
            i += 1
    return opciones + (["--"] + rutas if rutas else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="es")
    ap.add_argument("--out", default="transcripciones.json")
    ap.add_argument("--model-dir", default=None)
    args = ap.parse_args(ordenar_argumentos(sys.argv[1:]))

    import sherpa_onnx  # importar despues de parsear, para que --help sea rapido

    paths = []
    for item in args.inputs:
        if os.path.isdir(item):
            hallados = sorted(globmod.glob(os.path.join(item, args.glob or "*")))
            if not args.glob:
                # Sin --glob, barrer una carpeta de export traia el _chat.txt,
                # el inventario.json y cada foto, y todos terminaban marcados
                # como ilegibles. Se filtra por extension de audio y video.
                hallados = [p for p in hallados if es_media(p)]
            paths += hallados
        else:
            paths.append(item)
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        print("No se encontraron archivos de entrada.")
        return 1

    asr_home = os.environ.get("ASR_HOME") or os.path.join(
        os.path.expanduser("~"), ".whatsapp-deep-read")
    mdir = args.model_dir or os.path.join(
        asr_home, f"sherpa-onnx-whisper-{args.model}")
    if not os.path.isdir(mdir):
        print(f"Falta el modelo en {mdir}.", file=sys.stderr)
        print(f"Corre primero:  python scripts/setup_asr.py {args.model}",
              file=sys.stderr)
        return 1

    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        # os.path.join y no "/": en Windows la barra invertida es la que vale
        encoder=os.path.join(mdir, f"{args.model}-encoder.int8.onnx"),
        decoder=os.path.join(mdir, f"{args.model}-decoder.int8.onnx"),
        tokens=os.path.join(mdir, f"{args.model}-tokens.txt"),
        language=args.lang,
        task="transcribe",
        num_threads=os.cpu_count() or 4,
    )

    results = {}
    if os.path.exists(args.out):
        try:
            results = json.load(open(args.out, encoding="utf-8"))
        except Exception:
            results = {}

    workdir = os.path.join(os.path.dirname(os.path.abspath(paths[0])), "wav")

    def guardar():
        tmp = args.out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        os.replace(tmp, args.out)   # atomico: nunca deja un json a medias

    rotos, salteados, sin_audio = [], [], []
    for src in paths:
        name = os.path.basename(src)
        if name in results:
            print(f"### {name} (ya transcripto, se saltea)")
            continue
        if not es_media(name):
            # Segunda red: aunque llegue nombrado a mano, un archivo que no es
            # audio ni video se saltea. NUNCA se anota como hueco: el hueco
            # significa "habia algo que escuchar y no se pudo", y aca no lo hay.
            print(f"### {name}  no es audio ni video, se saltea\n", flush=True)
            salteados.append(name)
            continue
        wav, motivo = to_wav(src, workdir)
        if wav is None and motivo == "sin_audio":
            # Un GIF, o un video mudo. El archivo esta sano: no hay nada que
            # transcribir y NO es un hueco. Las imagenes las mira la etapa 6.
            sin_audio.append(name)
            results[name] = {"duracion_s": None, "texto": None,
                             "sin_audio": True,
                             "nota": "el archivo no tiene pista de audio "
                                     "(GIF o video mudo): no hay nada que "
                                     "transcribir. Las imagenes se miran aparte."}
            guardar()
            print(f"### {name}  sin pista de audio (GIF o video mudo).")
            print("    No es un hueco: hay que MIRARLO en la etapa de "
                  "imagenes.\n", flush=True)
            continue
        if wav is None:
            rotos.append(name)
            results[name] = {"duracion_s": None, "texto": None,
                             "error": "archivo ilegible (vacio o truncado)"}
            guardar()
            print(f"### {name}  NO SE PUDO LEER: archivo vacio o truncado.")
            print("    Va al documento como hueco declarado, no se omite.\n",
                  flush=True)
            continue
        samples = read_wave(wav)
        parts = []
        # Los bloques se solapan 2 s: cortar en seco cada 25 s se comia las
        # palabras que caian justo en el borde, y en un audio de ocho minutos
        # son casi veinte bordes.
        step = (CHUNK_SECONDS - OVERLAP_SECONDS) * SR
        ancho = CHUNK_SECONDS * SR
        for i in range(0, max(len(samples), 1), step):
            seg = samples[i:i + ancho]
            if len(seg) < SR // 10:
                continue
            s = rec.create_stream()
            s.accept_waveform(SR, seg)
            rec.decode_stream(s)
            parts.append(s.result.text.strip())
        text = unir([p for p in parts if p])
        # la duracion sale del wav convertido, no del original: asi no
        # hace falta ffprobe, que el ffmpeg de pip no trae
        results[name] = {"duracion_s": duration(wav), "texto": text}
        guardar()
        print(f"### {name}  ({results[name]['duracion_s']} s)")
        print(text)
        print(flush=True)

    guardar()
    buenas = sum(1 for v in results.values() if v.get("texto"))
    print(f"--- {buenas} transcripciones en {args.out}")
    if rotos:
        print(f"--- {len(rotos)} archivo{'' if len(rotos) == 1 else 's'} "
              f"ilegible{'' if len(rotos) == 1 else 's'}, anotado"
              f"{'' if len(rotos) == 1 else 's'} como hueco:")
        for r in rotos:
            print(f"      {r}")
    if sin_audio:
        print(f"--- {len(sin_audio)} archivo{'' if len(sin_audio) == 1 else 's'} "
              f"sin pista de audio (GIF o video mudo). NO son huecos: "
              f"hay que mirarlos:")
        for a in sin_audio:
            print(f"      {a}")
    if salteados:
        print(f"--- {len(salteados)} archivo{'' if len(salteados) == 1 else 's'} "
              f"que no {'es' if len(salteados) == 1 else 'son'} audio ni video, "
              f"salteado{'' if len(salteados) == 1 else 's'} (no son huecos):")
        for s in salteados:
            print(f"      {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
