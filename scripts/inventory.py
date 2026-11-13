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
import shutil
import unicodedata
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ffmpeg_tools  # noqa: E402
from collections import Counter, defaultdict
from datetime import datetime

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
# Los mensajes de sistema (cifrado, "Fulano creo el grupo", "te anadio")
# tienen fecha pero NO remitente. Sin una regex propia no matchean, y el
# "elif messages" de parse_chat los pegaba al mensaje anterior, inflandolo
# con texto que no es suyo. Ahora se guardan aparte: el SKILL.md los pide
# para fechar la creacion del grupo y saber quien lo creo.
SYS_RE_IOS = re.compile(
    r"^\u200e?\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([apAP]\.?\s*[mM]\.?)?\s*\]\s\u200e?(.*)$"
)
SYS_RE_ANDROID = re.compile(
    r"^\u200e?(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([apAP]\.?\s*[mM]\.?)?\s*[-\u2013]\s(.*)$"
)

URL_RE = re.compile(r"https?://[^\s]+")

# Avisos del sistema que SI traen remitente.
#
# "Se elimino este mensaje" NO entra aca a proposito: no es un aviso sobre el
# grupo, es el hueco que dejo un mensaje que alguien mando y despues borro.
# Que una persona haya escrito algo a tal hora y lo haya retirado es
# informacion de la conversacion, y se pierde si se lo saca del conteo.
SYS_FRASES = re.compile(
    r"(cifrad[oa]s de extremo a extremo|end-to-end encrypted"
    r"|cre[oó] este grupo|creaste este grupo|created this group"
    # con tilde a proposito: "X anadio a Y" es el aviso del sistema, en
    # tercera persona. "te agrego a este grupo", sin tilde, es una persona
    # escribiendo en primera. Sin esa distincion, el mensaje de alguien se
    # clasifica como aviso y desaparece del conteo y de la linea de tiempo.
    r"|a[ñn]adió a |agregó a | added |te a[ñn]adió|te agregó"
    r"|sali[oó] del grupo| left$|se uni[oó] usando|joined using"
    r"|cambi[oó] el nombre del grupo|cambi[oó] el asunto|changed the subject"
    r"|cambi[oó] la imagen|changed this group's icon"
    r"|ahora es administrador|is now an admin"
    r"|cambi[oó] su n[uú]mero|changed their phone number)",
    re.IGNORECASE)


def es_de_sistema(body: str) -> bool:
    """Un aviso del sistema, aunque la linea traiga remitente.

    No se puede usar la marca invisible U+200E como senal: `normalizar()` ya
    la saco cuando esto corre. Queda la frase, y para no confundir un aviso
    con alguien que escribe "Juan salio del grupo" en una charla, se exige
    ademas que sea corto: los avisos de WhatsApp son de una linea.
    """
    t = (body or "").replace("‎", "").strip()
    if not t or len(t) > 220:
        return False
    if t.startswith("<adjunto:") or t.startswith("<attached:"):
        return False
    return bool(SYS_FRASES.search(t))

# La falla mas comun y la mas silenciosa: exportar SIN los archivos.
# WhatsApp no deja el nombre del adjunto sino una marca de omision, distinta
# segun el sistema y el idioma:
#   Android: <Multimedia omitido>        iOS: audio omitido / imagen omitida
#   ingles:  <Media omitted>                  audio omitted / image omitted
# Un export asi se procesa igual y devuelve un documento que PARECE completo,
# pero sin una sola nota de voz. Por eso hay que DETENERSE, no avisar al pasar.
OMITIDO_RE = re.compile(
    r"^\s*<?\s*(?:multimedia|media|audio|imagen|image|v[íi]deo|video|sticker|gif|"
    r"documento|document|archivo|file|foto|photo|contacto|contact|ubicaci[óo]n)"
    r"\s*(?:omitid[oa]s?|omitted)\s*>?\s*$", re.I)


def contar_omitidos(messages) -> int:
    """Cuantos mensajes son una marca de 'archivo omitido'.

    Se mira LINEA POR LINEA, no el texto entero: si el mensaje quedo
    multilinea, un OMITIDO_RE anclado con ^...$ contra todo el texto no
    matchea y la puerta de 'export sin archivos' no se dispara nunca.
    Es justo la falla que esa puerta existe para evitar."""
    n = 0
    for m in messages:
        texto = m.get("text", "") or ""
        if any(OMITIDO_RE.match(l) for l in texto.split("\n")):
            n += 1
    return n


def frase_omitidos(n: int) -> str:
    """Singular y plural. Este cartel es lo mas visible del proyecto:
    un 'Se encontraron 1 mensajes' arruina la impresion de todo lo demas."""
    if n == 1:
        return 'Se encontro 1 mensaje que dice "omitido"'
    return f'Se encontraron {n} mensajes que dicen "omitido"'


AVISO_SIN_ARCHIVOS = """
===============================================================================
  ESTE EXPORT NO TRAE LOS ARCHIVOS. NO SE PUEDE SEGUIR.
===============================================================================

  {frase}.
  No hay ningun archivo de audio, imagen o documento en la carpeta: el chat
  se exporto SIN los adjuntos, esta el texto y nada mas.

  Procesar esto daria un documento que parece completo y no tiene una sola
  nota de voz. Justo lo que este skill existe para evitar.

  QUE HACER: volver a exportar el chat.

    En WhatsApp, abri el grupo y busca "Exportar chat".
    Te va a preguntar si incluis los archivos. Deci que SI.
    Segun la version el boton dice "Adjuntar archivos", "Incluir archivos"
    o "Con multimedia".

  COMO SABER SI SALIO BIEN: el archivo nuevo tiene que pesar bastante mas.
  Un export sin archivos pesa unos pocos kilobytes; uno con los archivos
  pesa megas, y a veces cientos.

  Si de verdad solo tenes el texto y queres seguir igual, agrega --solo-texto.
  El documento saldra sin audios, sin imagenes y sin documentos, y hay que
  decirlo en la nota metodologica.
===============================================================================
"""


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_duration(path):
    """Duracion en segundos, si hay con que medirla.

    Prueba ffprobe (lo trae el ffmpeg del sistema) y, si no esta, lee la
    duracion del stderr de ffmpeg, que tambien sirve el ffmpeg que instala pip.
    Si no hay ninguno de los dos, devuelve None y el inventario sigue sin la
    duracion: es un dato lindo, no un requisito."""
    probe = ffmpeg_tools.ffprobe()
    if probe:
        try:
            out = subprocess.run(
                [probe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", path],
                capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="replace")
            return round(float(out.stdout.strip()), 1)
        except Exception:
            pass

    exe = ffmpeg_tools.ffmpeg()
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-i", path], capture_output=True, text=True,
                             timeout=60, encoding="utf-8", errors="replace")
        m = re.search(r"Duration:\s*(\d+):(\d{2}):(\d{2}(?:\.\d+)?)", out.stderr)
        if m:
            h, mi, se = int(m.group(1)), int(m.group(2)), float(m.group(3))
            return round(h * 3600 + mi * 60 + se, 1)
    except Exception:
        pass
    return None


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True,
                             text=True, timeout=60,
                             encoding="utf-8", errors="replace")
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


def _lineas_de_mensaje(path):
    """Cuantas lineas del archivo parecen un mensaje de WhatsApp."""
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            raw = normalizar(f.read())
    except Exception:
        return 0
    ls = raw.split("\n")[:400]
    return max(sum(1 for l in ls if MSG_RE_IOS.match(l)),
               sum(1 for l in ls if MSG_RE_ANDROID.match(l)))


def find_chat_file(folder):
    """El chat del export, con desempate.

    Antes se devolvia el primero que os.listdir escupiera, sin ordenar. Si en
    la carpeta habia otro .txt con "chat" en el nombre -un adjunto que alguien
    mando por el grupo, o un archivo de una corrida anterior- podia ganarle a
    _chat.txt y el inventario salia con CERO mensajes y sin un solo error."""
    exacto, candidatos = None, []
    for name in sorted(os.listdir(folder)):
        low = name.lower()
        if not low.endswith(".txt"):
            continue
        p = os.path.join(folder, name)
        if not os.path.isfile(p):
            continue
        if low == "_chat.txt":
            exacto = p
        elif "chat" in low:
            candidatos.append(p)
    if exacto:
        return exacto
    if not candidatos:
        return None
    # gana el que mas lineas de mensaje real tenga
    return max(candidatos, key=_lineas_de_mensaje)


def _attachments(text):
    text = normalizar(text)
    found = [a.strip() for a in ATTACH_RE.findall(text)]
    for line in text.split("\n"):
        m = ATTACH_RE_ANDROID.match(line.strip())
        if m:
            found.append(m.group(1).strip())
    return found


def detect_format(raw):
    """Devuelve ('ios'|'android', regex_mensaje, regex_sistema)."""
    raw = normalizar(raw)
    lines = raw.split("\n")[:400]
    n_ios = sum(1 for l in lines if MSG_RE_IOS.match(l))
    n_and = sum(1 for l in lines if MSG_RE_ANDROID.match(l))
    if n_and > n_ios:
        return "android", MSG_RE_ANDROID, SYS_RE_ANDROID
    return "ios", MSG_RE_IOS, SYS_RE_IOS


def detectar_orden(lines, MSG_RE):
    """dia/mes o mes/dia. Un telefono en locale de EE.UU. escribe 5/20/26.

    Sin esto, datetime(2026, 20, 5) tira ValueError, el ts queda en None y el
    documento sale con la linea de tiempo entera sin fechas, en silencio."""
    primeros, segundos = [], []
    for l in lines[:400]:
        m = MSG_RE.match(l)
        if m:
            primeros.append(int(m.group(1)))
            segundos.append(int(m.group(2)))
    if not primeros:
        return "DMY"
    # Un componente mayor que 12 no puede ser un mes: es el dia.
    if max(segundos) > 12 and max(primeros) <= 12:
        return "MDY"          # 5/20/26 -> mes/dia
    return "DMY"              # el caso normal, y el desempate si hay dudas


def _fecha(d, mo, y, hh, mm, ss, ampm, orden):
    """Arma el timestamp respetando el orden dia/mes del export."""
    y = int(y)
    y += 2000 if y < 100 else 0
    a, b = int(d), int(mo)
    if orden == "MDY":
        a, b = b, a          # venia mes/dia
    hh = int(hh)
    if ampm:
        x = ampm.lower().replace(".", "").replace(" ", "")
        if x.startswith("p") and hh < 12:
            hh += 12
        elif x.startswith("a") and hh == 12:
            hh = 0
    try:
        return datetime(y, b, a, hh, int(mm), int(ss or 0))
    except ValueError:
        return None


CREACION = re.compile(r"(cre[oó] este grupo|creaste este grupo|created this group"
                      r"|cre[oó] el grupo)", re.IGNORECASE)
TE_SUMARON = re.compile(r"(te a[ñn]adió|te agregó|added you|te sum[oó]"
                        r"|se uni[oó] usando|joined using)", re.IGNORECASE)


def estado_del_historial(sistema, senders):
    """Dice si el export parece traer la conversacion desde el principio.

    Hay una forma silenciosa de perder informacion que no tiene nada que ver
    con los adjuntos: exportar desde la aplicacion de escritorio cuando el
    chat no esta cargado entero. Sale un export que parece normal pero al que
    le falta historial viejo, y nada avisa.

    La senal es simple. Un grupo empieza con el aviso de que alguien lo creo.
    Si ese aviso no esta, caben dos explicaciones: te sumaron despues —y
    entonces hay un aviso que lo dice— o el export quedo cortado.

    En un chat de dos personas no hay aviso de creacion, asi que no se puede
    decir nada: ahi se calla.
    """
    textos = [s["texto"] for s in sistema]
    for s in sistema:
        if CREACION.search(s["texto"]):
            return {"estado": "completo", "desde": s["ts"],
                    "motivo": "el export trae la creacion del grupo"}
    for s in sistema:
        if TE_SUMARON.search(s["texto"]):
            return {"estado": "te_sumaron_despues", "desde": s["ts"],
                    "motivo": "te sumaron al grupo despues de creado"}
    if len(senders) < 3:
        return {"estado": "no_se_puede_saber", "desde": None,
                "motivo": "chat de dos personas: no hay aviso de creacion"}
    return {"estado": "posiblemente_incompleto", "desde": None,
            "motivo": "grupo sin aviso de creacion ni de que te sumaran"}


def nombre_real(info) -> str:
    """Recupera el nombre de una entrada del zip.

    WhatsApp guarda los nombres en UTF-8 pero NO prende la bandera que lo
    declara (bit 0x800). Ante esa ausencia, zipfile cumple el estandar y los
    lee como CP437, la tabla de MS-DOS. Resultado: "presentacion.pdf" con
    tilde sale del zip como "presentacio╠un.pdf".

    Eso rompe dos cosas a la vez: los archivos quedan en el disco con el
    nombre arruinado, y el chat —que los nombra bien— los reporta como
    ausentes: el documento final anuncia huecos que no existen.

    Se reinterpretan los bytes como UTF-8. Si no lo son, el nombre se deja
    como vino: un zip hecho de verdad en CP437 sigue funcionando.
    """
    nombre = info.filename
    if info.flag_bits & 0x800:
        return nombre
    try:
        return nombre.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return nombre


def _extraer(z, destino):
    """Descomprime arreglando los nombres y sin dejar escapar rutas."""
    destino = os.path.abspath(destino)
    for info in z.infolist():
        nombre = nombre_real(info)
        # nada de rutas absolutas ni de ".." que se escapen del destino
        partes = [p for p in nombre.replace("\\", "/").split("/")
                  if p not in ("", ".", "..")]
        if not partes:
            continue
        ruta = os.path.join(destino, *partes)
        if not os.path.abspath(ruta).startswith(destino + os.sep):
            continue
        if info.is_dir():
            os.makedirs(ruta, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with z.open(info) as origen, open(ruta, "wb") as f:
            shutil.copyfileobj(origen, f)


def parse_chat(path):
    # utf-8-sig: si el .txt paso por Notepad o Excel queda con BOM, y sin
    # esto el primer mensaje no matchea y se pierde sin aviso.
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        raw = f.read().replace("\r\n", "\n").replace("\r", "\n")

    fmt, MSG_RE, SYS_RE = detect_format(raw)
    lineas = normalizar(raw).split("\n")
    orden = detectar_orden(lineas, MSG_RE)

    messages, sistema = [], []
    for line in lineas:
        m = MSG_RE.match(line)
        if m:
            d, mo, y, hh, mm, ss, ampm, sender, body = m.groups()
            ts = _fecha(d, mo, y, hh, mm, ss, ampm, orden)
            if es_de_sistema(body):
                # Algunos exports ponen remitente en los avisos del sistema:
                # el nombre del grupo en los de cifrado y creacion, o la
                # persona en los de "X anadio a Y". Sin esto, el grupo entra
                # a la lista de participantes como si fuera una persona, y el
                # SKILL.md se queda sin los avisos que pide para fechar la
                # creacion.
                sistema.append({"ts": ts.isoformat() if ts else None,
                                "texto": body.replace("‎", "").strip(),
                                "atribuido_a": sender.strip()})
                continue
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
            continue
        ms = SYS_RE.match(line)
        if ms:
            d, mo, y, hh, mm, ss, ampm, body = ms.groups()
            ts = _fecha(d, mo, y, hh, mm, ss, ampm, orden)
            sistema.append({"ts": ts.isoformat() if ts else None,
                            "texto": body.strip()})
            continue
        if messages:
            # continuacion de un mensaje multilinea
            messages[-1]["text"] += "\n" + line
            messages[-1]["attachments"] += _attachments(line)
            messages[-1]["urls"] += URL_RE.findall(line)
    sin_fecha = sum(1 for m in messages if m["_dt"] is None)
    return messages, fmt, sistema, orden, sin_fecha


def main():
    ap = argparse.ArgumentParser(
        description="Inventaria un export de WhatsApp (.zip o carpeta).")
    ap.add_argument("entrada", help="ruta al .zip exportado o a la carpeta ya descomprimida")
    ap.add_argument("--json", default=None)
    ap.add_argument("--solo-texto", action="store_true",
                    help="seguir aunque el export no traiga los archivos")
    args = ap.parse_args()

    entrada = os.path.abspath(args.entrada)
    if not os.path.exists(entrada):
        print(f"ERROR: no existe {entrada}", file=sys.stderr)
        return 1

    if os.path.isfile(entrada) and entrada.lower().endswith(".zip"):
        folder = os.path.splitext(entrada)[0]
        os.makedirs(folder, exist_ok=True)
        try:
            with zipfile.ZipFile(entrada) as z:
                _extraer(z, folder)
        except zipfile.BadZipFile:
            print(f"ERROR: {os.path.basename(entrada)} no es un .zip valido.\n"
                  "  Puede haberse cortado la descarga o la transferencia.\n"
                  "  Volve a bajar el export del telefono.", file=sys.stderr)
            return 1
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
    if chat_path:
        messages, fmt, sistema, orden, sin_fecha = parse_chat(chat_path)
    else:
        messages, fmt, sistema, orden, sin_fecha = [], None, [], None, 0

    if orden == "MDY":
        print("AVISO: el export viene en formato mes/dia (telefono en locale de\n"
              "  EE.UU.). Se interpreto asi para armar las fechas.", file=sys.stderr)
    if sin_fecha:
        print(f"AVISO: {sin_fecha} de {len(messages)} mensajes quedaron SIN FECHA\n"
              "  porque no se pudo interpretar el timestamp. La linea de tiempo\n"
              "  va a estar incompleta: hay que decirlo en la nota metodologica.",
              file=sys.stderr)
    if chat_path and not messages:
        print("AVISO: se encontro el .txt del chat pero no se pudo parsear ni un\n"
              "  mensaje. Puede ser un formato de export no contemplado. NO se\n"
              "  puede armar el documento con esto.", file=sys.stderr)

    # --- la puerta: un export sin archivos no se procesa ---
    omitidos = contar_omitidos(messages)
    # Ojo: el propio _chat.txt cuenta como "documento". Si no se lo excluye,
    # la lista nunca queda vacia y esta puerta no se dispara jamas.
    chat_name = os.path.basename(chat_path) if chat_path else None
    con_contenido = [f for f in files
                     if f["kind"] in ("audio", "video", "imagen", "documento")
                     and f["name"] != chat_name]
    if omitidos and not con_contenido and not args.solo_texto:
        print(AVISO_SIN_ARCHIVOS.format(frase=frase_omitidos(omitidos)),
              file=sys.stderr)
        return 2
    if omitidos and con_contenido:
        uno = omitidos == 1
        print(f"\nAVISO: hay {omitidos} adjunto{'' if uno else 's'} "
              f"marcado{'' if uno else 's'} como omitido{'' if uno else 's'} y "
              f"{len(con_contenido)} archivo{'' if len(con_contenido) == 1 else 's'} "
              f"presente{'' if len(con_contenido) == 1 else 's'}.\n"
              "  El export trajo los archivos, pero algunos ya no estaban en el\n"
              "  telefono cuando se exporto. Esos no se pueden recuperar: van\n"
              "  al documento como huecos declarados, no se omiten en silencio.",
              file=sys.stderr)

    present = {f["name"] for f in files}
    mentioned = []
    for m in messages:
        mentioned += m["attachments"]
    # Comparar normalizando: macOS guarda los acentos descompuestos (NFD) en
    # los nombres de archivo y WhatsApp los escribe compuestos (NFC) adentro
    # del chat. Sin esto, "presentación.pdf" existe en el disco y el informe
    # lo declara ausente igual.
    presente_norm = {unicodedata.normalize("NFC", p) for p in present}
    missing = sorted({a for a in mentioned
                      if unicodedata.normalize("NFC", a) not in presente_norm})

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
            "adjuntos_omitidos_por_el_export": omitidos,
        },
        "rango": {
            "desde": dts[0].isoformat() if dts else None,
            "hasta": dts[-1].isoformat() if dts else None,
        },
        "orden_fecha": orden,
        "mensajes_sin_fecha": sin_fecha,
        "participantes": senders.most_common(),
        "mensajes_de_sistema": sistema,
        "historial": estado_del_historial(sistema, senders),
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
    print(f"Chat: {report['chat_file']}  ({t['mensajes']} mensajes, formato {fmt}"
          f"{', fechas mes/dia' if orden == 'MDY' else ''})")
    if sistema:
        print(f"Mensajes de sistema: {len(sistema)}  "
              f"(el primero: {sistema[0]['texto'][:60]!r})")
    print(f"Rango: {report['rango']['desde']} -> {report['rango']['hasta']}")
    hist = report.get("historial")
    if hist and hist["estado"] == "posiblemente_incompleto":
        print("\nAVISO: puede faltar historial al principio.")
        print("  El export no trae el aviso de creacion del grupo ni uno que")
        print("  diga que te sumaron despues, asi que el chat deberia empezar")
        print(f"  en su primer mensaje y empieza en {report['rango']['desde'][:10]}.")
        print("  Exportando desde la aplicacion de escritorio esto pasa cuando")
        print("  el chat no estaba cargado entero. El export desde el telefono")
        print("  trae el historial completo.")
        print("  Si sabes que el grupo es mas viejo, volve a exportar desde el")
        print("  telefono. Si no, seguir: el documento lo deja declarado.\n")
    elif hist and hist["estado"] == "te_sumaron_despues":
        print(f"  (te sumaron al grupo el {hist['desde'][:10]}: lo anterior "
              f"no esta en tu WhatsApp)")
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
