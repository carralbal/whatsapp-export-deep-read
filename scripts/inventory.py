#!/usr/bin/env python3
"""
Inventario de un export de WhatsApp ya descomprimido.

Uso:
    python3 inventory.py /ruta/al/export.zip   [--json salida.json]
    python3 inventory.py /ruta/a/la/carpeta    [--json salida.json]

Si le pasas el .zip lo descomprime solo, al lado del archivo.

Produce:
  - inventario de archivos con tipo, tamano, MD5 y duplicados
  - duracion total de audio y video (si hay ffprobe)
  - paginas por PDF (si hay pdfinfo)
  - parseo de _chat.txt: participantes, rango de fechas, mensajes, adjuntos
  - adjuntos mencionados en el chat que NO estan en la carpeta
  - huecos de conversacion mayores a 14 dias
"""

from __future__ import annotations  # anotaciones perezosas: corre en Python 3.8+

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime

AUDIO_EXT = {".opus", ".ogg", ".m4a", ".mp3", ".aac", ".wav", ".amr"}
VIDEO_EXT = {".mp4", ".3gp", ".mov", ".avi", ".mkv", ".webm"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".bmp"}
DOC_EXT = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".pptx",
           ".txt", ".rtf", ".odt", ".ods"}

# iOS:      [26/5/26, 20:49:27] Remitente: texto
# Android:  26/5/26, 20:49 - Remitente: texto

# WhatsApp mete caracteres invisibles que rompen cualquier regex ingenua:
#   U+200E / U+200F  marcas de direccion, al principio de linea y de adjunto
#   U+202F           espacio fino, entre la hora y "p. m." en locales en espanol
#   U+00A0           espacio duro
# Sin normalizar esto, un export de iPhone en espanol devuelve CERO mensajes.
INVISIBLES = str.maketrans({
    "\u200e": "", "\u200f": "",
    "\u202f": " ", "\u00a0": " ", "\u2009": " ", "\u2007": " ",
})


def normalizar(texto: str) -> str:
    return texto.translate(INVISIBLES).replace("\r\n", "\n").replace("\r", "\n")


MSG_RE_IOS = re.compile(
    r"^\u200e?\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([apAP]\.?\s*[mM]\.?)?\s*\]\s\u200e?([^:]+?):\s?(.*)$"
)
MSG_RE_ANDROID = re.compile(
    r"^\u200e?(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([apAP]\.?\s*[mM]\.?)?\s*[-\u2013]\s([^:]+?):\s?(.*)$"
)

# iOS: <adjunto: NOMBRE>   Android: NOMBRE (archivo adjunto)
ATTACH_RE = re.compile(r"<(?:adjunto|attached|archivo adjunto):\s*([^>]+)>")
ATTACH_RE_ANDROID = re.compile(
    r"^\u200e?([\w\-. ()]+\.[A-Za-z0-9]{2,5})\s*\((?:archivo adjunto|file attached)\)"
)
URL_RE = re.compile(r"https?://[^\s]+")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=60)
        return round(float(out.stdout.strip()), 1)
    except Exception:
        return None


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True,
                             text=True, timeout=60)
        for line in out.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[-1])
    except Exception:
        pass
    return None


def kind(ext):
    ext = ext.lower()
    if ext in AUDIO_EXT:
        return "audio"
    if ext in VIDEO_EXT:
        return "video"
    if ext in IMAGE_EXT:
        return "imagen"
    if ext in DOC_EXT:
        return "documento"
    return "otro"


def find_chat_file(folder):
    for name in os.listdir(folder):
        low = name.lower()
        if low == "_chat.txt" or (low.endswith(".txt") and "chat" in low):
            return os.path.join(folder, name)
    return None


def _attachments(text):
    text = normalizar(text)
    found = ATTACH_RE.findall(text)
    for line in text.split("\n"):
        m = ATTACH_RE_ANDROID.match(line.strip())
        if m:
            found.append(m.group(1).strip())
    return found


def detect_format(raw):
    """Devuelve ('ios'|'android', regex). Gana el que matchee mas lineas."""
    raw = normalizar(raw)
    lines = raw.split("\n")[:400]
    n_ios = sum(1 for l in lines if MSG_RE_IOS.match(l))
    n_and = sum(1 for l in lines if MSG_RE_ANDROID.match(l))
    if n_and > n_ios:
        return "android", MSG_RE_ANDROID
    return "ios", MSG_RE_IOS


def parse_chat(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read().replace("\r\n", "\n").replace("\r", "\n")

    fmt, MSG_RE = detect_format(raw)
    messages = []
    for line in normalizar(raw).split("\n"):
        m = MSG_RE.match(line)
        if m:
            d, mo, y, hh, mm, ss, ampm, sender, body = m.groups()
            y = int(y)
            y += 2000 if y < 100 else 0
            hh = int(hh)
            if ampm:
                a = ampm.lower().replace(".", "").replace(" ", "")
                if a.startswith("p") and hh < 12:
                    hh += 12
                elif a.startswith("a") and hh == 12:
                    hh = 0
            try:
                ts = datetime(y, int(mo), int(d), hh, int(mm),
                              int(ss or 0))
            except ValueError:
                ts = None
            messages.append({
                "ts": ts.isoformat() if ts else None,
                "_dt": ts,
                "sender": sender.strip(),
                "text": body,
                "attachments": _attachments(body),
                "urls": URL_RE.findall(body),
                "edited": "Se editó este mensaje" in body
                          or "This message was edited" in body,
            })
        elif messages:
            # continuacion de un mensaje multilinea
            messages[-1]["text"] += "\n" + line
            messages[-1]["attachments"] += _attachments(line)
            messages[-1]["urls"] += URL_RE.findall(line)
    return messages, fmt


def main():
    ap = argparse.ArgumentParser(
        description="Inventaria un export de WhatsApp (.zip o carpeta).")
    ap.add_argument("entrada", help="ruta al .zip exportado o a la carpeta ya descomprimida")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    entrada = os.path.abspath(args.entrada)
    if not os.path.exists(entrada):
        print(f"ERROR: no existe {entrada}", file=sys.stderr)
        return 1

    if os.path.isfile(entrada) and entrada.lower().endswith(".zip"):
        folder = os.path.splitext(entrada)[0]
        os.makedirs(folder, exist_ok=True)
        with zipfile.ZipFile(entrada) as z:
            z.extractall(folder)
        print(f"Descomprimido en {folder}")
        # exports que traen todo dentro de una subcarpeta unica
        hijos = [h for h in os.listdir(folder) if not h.startswith(".")]
        if len(hijos) == 1 and os.path.isdir(os.path.join(folder, hijos[0])):
            folder = os.path.join(folder, hijos[0])
    elif os.path.isdir(entrada):
        folder = entrada
    else:
        print(f"ERROR: {entrada} no es un .zip ni una carpeta", file=sys.stderr)
        return 1

    GENERADOS = {"inventario.json", "transcripciones.json"}
    files = []
    by_hash = defaultdict(list)
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if not os.path.isfile(p) or name in GENERADOS or name.startswith("."):
            continue
        ext = os.path.splitext(name)[1]
        h = md5(p)
        by_hash[h].append(name)
        rec = {"name": name, "ext": ext.lower(), "kind": kind(ext),
               "size": os.path.getsize(p), "md5": h}
        if rec["kind"] in ("audio", "video"):
            rec["duration_s"] = probe_duration(p)
        if ext.lower() == ".pdf":
            rec["pages"] = pdf_pages(p)
        files.append(rec)

    for rec in files:
        dups = by_hash[rec["md5"]]
        rec["duplicate_of"] = [d for d in dups if d != rec["name"]] or None

    if not files:
        print("AVISO: la carpeta no tiene archivos.", file=sys.stderr)
    chat_path = find_chat_file(folder)
    if chat_path is None:
        print("AVISO: no se encontro el .txt del chat en la carpeta.",
              file=sys.stderr)
    messages, fmt = parse_chat(chat_path) if chat_path else ([], None)

    present = {f["name"] for f in files}
    mentioned = []
    for m in messages:
        mentioned += m["attachments"]
    missing = sorted({a for a in mentioned if a not in present})

    dts = [m["_dt"] for m in messages if m["_dt"]]
    gaps = []
    for a, b in zip(dts, dts[1:]):
        days = (b - a).days
        if days >= 14:
            gaps.append({"desde": a.isoformat(), "hasta": b.isoformat(),
                         "dias": days})

    senders = Counter(m["sender"] for m in messages)
    audio_total = sum(f.get("duration_s") or 0
                      for f in files if f["kind"] == "audio")
    video_total = sum(f.get("duration_s") or 0
                      for f in files if f["kind"] == "video")

    report = {
        "carpeta": folder,
        "chat_file": os.path.basename(chat_path) if chat_path else None,
        "formato_export": fmt,
        "totales": {
            "archivos": len(files),
            "mensajes": len(messages),
            "por_tipo": dict(Counter(f["kind"] for f in files)),
            "audio_segundos": round(audio_total, 1),
            "video_segundos": round(video_total, 1),
            "paginas_pdf": sum(f.get("pages") or 0 for f in files),
            "grupos_duplicados": sum(1 for v in by_hash.values() if len(v) > 1),
        },
        "rango": {
            "desde": dts[0].isoformat() if dts else None,
            "hasta": dts[-1].isoformat() if dts else None,
        },
        "participantes": senders.most_common(),
        "huecos_mayores_14_dias": gaps,
        "adjuntos_mencionados_ausentes": missing,
        "urls": sorted({u for m in messages for u in m["urls"]}),
        "archivos": files,
    }

    for m in messages:
        m.pop("_dt", None)

    out_json = args.json or os.path.join(folder, "inventario.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"reporte": report, "mensajes": messages}, f,
                  ensure_ascii=False, indent=1)

    t = report["totales"]
    print(f"Carpeta: {folder}")
    print(f"Chat: {report['chat_file']}  ({t['mensajes']} mensajes, formato {fmt})")
    print(f"Rango: {report['rango']['desde']} -> {report['rango']['hasta']}")
    print(f"Archivos: {t['archivos']}  {t['por_tipo']}")
    print(f"Audio: {t['audio_segundos']} s   Video: {t['video_segundos']} s"
          f"   Paginas PDF: {t['paginas_pdf']}")
    print(f"Grupos de duplicados: {t['grupos_duplicados']}")
    print("\nParticipantes:")
    for s, n in report["participantes"]:
        print(f"  {n:4d}  {s}")
    if gaps:
        print("\nHuecos de conversacion (>=14 dias):")
        for g in gaps:
            print(f"  {g['dias']:3d} dias: {g['desde']} -> {g['hasta']}")
    if missing:
        print("\nAdjuntos mencionados que NO estan en el export:")
        for a in missing:
            print(f"  - {a}")
    dupes = {h: v for h, v in by_hash.items() if len(v) > 1}
    if dupes:
        print("\nDuplicados (mismo MD5):")
        for h, v in dupes.items():
            print(f"  {h[:8]}: {', '.join(v)}")
    print(f"\nDetalle completo en {out_json}")


if __name__ == "__main__":
    sys.exit(main())
