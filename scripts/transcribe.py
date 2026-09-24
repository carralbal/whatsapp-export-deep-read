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

import argparse
import glob as globmod
import json
import os
import shutil
import subprocess
import sys
import wave

import numpy as np

CHUNK_SECONDS = 25   # Whisper trabaja en ventanas de 30 s; 25 deja margen
SR = 16000


def to_wav(src, workdir):
    if shutil.which("ffmpeg") is None:
        raise SystemExit("Falta ffmpeg. macOS: brew install ffmpeg | "
                         "Debian/Ubuntu: sudo apt install ffmpeg")
    os.makedirs(workdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(workdir, base + ".wav")
    if not os.path.exists(dst):
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
             "-vn", "-ar", str(SR), "-ac", "1", dst],
            check=True)
    return dst


def read_wave(path):
    with wave.open(path) as w:
        data = w.readframes(w.getnframes())
    return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0


def duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path], capture_output=True, text=True)
        return round(float(out.stdout.strip()), 1)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="es")
    ap.add_argument("--out", default="transcripciones.json")
    ap.add_argument("--model-dir", default=None)
    args = ap.parse_args()

    import sherpa_onnx  # importar despues de parsear, para que --help sea rapido

    paths = []
    for item in args.inputs:
        if os.path.isdir(item):
            paths += sorted(globmod.glob(os.path.join(item, args.glob or "*")))
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
        encoder=f"{mdir}/{args.model}-encoder.int8.onnx",
        decoder=f"{mdir}/{args.model}-decoder.int8.onnx",
        tokens=f"{mdir}/{args.model}-tokens.txt",
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

    for src in paths:
        name = os.path.basename(src)
        if name in results:
            print(f"### {name} (ya transcripto, se saltea)")
            continue
        wav = to_wav(src, workdir)
        samples = read_wave(wav)
        parts = []
        step = CHUNK_SECONDS * SR
        for i in range(0, len(samples), step):
            seg = samples[i:i + step]
            if len(seg) < SR // 10:
                continue
            s = rec.create_stream()
            s.accept_waveform(SR, seg)
            rec.decode_stream(s)
            parts.append(s.result.text.strip())
        text = " ".join(p for p in parts if p)
        results[name] = {"duracion_s": duration(src), "texto": text}
        print(f"### {name}  ({results[name]['duracion_s']} s)")
        print(text)
        print(flush=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"--- {len(results)} transcripciones acumuladas en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
