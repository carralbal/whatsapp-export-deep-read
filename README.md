# whatsapp-export-deep-read

Un skill para Claude que lee **todo** un export de WhatsApp —no solo el texto— y lo
convierte en un único archivo Markdown que sirve como memoria permanente del proyecto.

Transcribe los audios. Mira los videos. Lee los PDF, los Word, los Excel y los CSV.
Analiza las imágenes una por una. Releva los links. Y arma una línea de tiempo
completa con todo en su lugar.

La mayor parte de lo que se habló en un proyecto no está en el texto del chat: está
en las notas de voz que nadie volvió a escuchar y en los adjuntos. Un resumen que
solo lee `_chat.txt` es un resumen que perdió lo importante.

---

## Qué te devuelve

Un `.md` con esta estructura:

- Inventario del export: todos los archivos, duplicados detectados por MD5, y los
  adjuntos que alguien mencionó pero no están en el export
- Participantes y roles inferidos
- **Línea de tiempo completa**: cada mensaje con hora y emisor, cada audio
  transcripto en su posición cronológica, cada adjunto señalado donde se envió
- Anexos con el texto íntegro de cada documento
- Síntesis, datos duros en tablas, y puntos abiertos e inconsistencias
- Nota metodológica: con qué se transcribió y qué quedó fuera

Y un recuento de cobertura, que es la prueba de que se leyó el 100%:

```
- Mensajes de texto leídos: 412 / 412
- Audios transcriptos: 23 / 23 (41:17)
- Videos procesados: 4 / 4
- Documentos leídos: 11 / 11
- Imágenes analizadas: 68 / 68
- Adjuntos mencionados pero ausentes del export: 3
```

---

## Requisitos

- **Python 3.9 o más nuevo** y **ffmpeg**
- Un asistente que pueda **ejecutar scripts y leer archivos de una carpeta en tu
  máquina**: Claude Code, Cowork, o cualquier otro con esa capacidad. Pegando
  esto en un chat web no funciona: necesita correr los scripts.
- Opcional pero recomendado: `poppler-utils` para los PDF (`pdftotext`, `pdfinfo`,
  `pdftoppm`)
- ~1 GB de disco para el modelo de transcripción (`small`), o ~110 MB (`tiny`)

**Plataformas:** Windows, macOS y Linux. El instalador es Python puro: no
necesita bash ni WSL.

```bash
# macOS
brew install python ffmpeg poppler

# Debian / Ubuntu
sudo apt install python3 python3-pip ffmpeg poppler-utils

# Windows
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```

---

## Instalación

```bash
git clone https://github.com/carralbal/whatsapp-export-deep-read.git
cd whatsapp-export-deep-read
```

Primero, comprobá que tu entorno está listo. Este comando no instala nada: te
dice qué tenés, qué falta y cómo conseguirlo.

```bash
python scripts/setup_asr.py --check
```

Después, una sola vez, instalá el motor de transcripción:

```bash
python scripts/setup_asr.py          # modelo small, ~1 GB
python scripts/setup_asr.py tiny     # más liviano y rápido, menos preciso
```

Queda en `~/.whatsapp-deep-read/`. Para cambiar la ubicación: `ASR_HOME=/otra/ruta`.

*(En Windows el comando suele ser `python`; en macOS y Linux, `python3`.)*

### Con Claude

Copiá la carpeta a tus skills. El skill se activa solo cuando mencionás un
export de WhatsApp.

```bash
mkdir -p ~/.claude/skills
cp -r whatsapp-export-deep-read ~/.claude/skills/
```

En Cowork, dejá la carpeta en un directorio al que la sesión tenga acceso.

### Con otro asistente

Pegá el contenido de [`INSTRUCCIONES.md`](INSTRUCCIONES.md) como instrucción de
tu proyecto. Es el mismo método, sin el formato de skill de Claude.

---

## Uso

1. En WhatsApp: abrí el grupo → **Exportar chat** → **Incluir archivos**
2. Dejá el `.zip` en una carpeta
3. Pedile a tu asistente que lea ese export

Con Claude, el skill se activa solo cuando mencionás un export de WhatsApp.
Si querés correr las piezas a mano:

```bash
# inventario: acepta el .zip directo o una carpeta ya descomprimida
python scripts/inventory.py /ruta/al/export.zip

# transcripción (siempre en primer plano, nunca con & ni nohup)
python scripts/transcribe.py /ruta/a/la/carpeta --glob "*.opus"
python scripts/transcribe.py video.mp4
```

---

## Privacidad

**Todo corre en tu máquina.** El modelo de transcripción es local: el audio no se
sube a ningún servicio. Lo único que sale de tu computadora es lo que vos
después le pases al asistente.

Antes de exportar un grupo, tené presente una cosa: **la conversación también es de
los demás.** Si en el grupo hay clientes, proveedores o gente que no trabaja con
vos, avisales antes. Dos líneas alcanzan.

Y no subas a ninguna herramienta datos personales de terceros, credenciales ni
material bajo acuerdo de confidencialidad. Ante la duda, no.

---

## Formatos soportados

| | |
|---|---|
| Sistemas | Windows, macOS, Linux |
| Export de iPhone | `[10/3/26, 09:14:11] Nombre: texto` |
| Export de Android | `10/3/26, 09:14 - Nombre: texto` |
| Audio | `.opus` `.ogg` `.m4a` `.mp3` `.aac` `.wav` `.amr` |
| Video | `.mp4` `.3gp` `.mov` `.avi` `.mkv` `.webm` |
| Imagen | `.jpg` `.png` `.webp` `.heic` … |
| Documentos | `.pdf` `.docx` `.xlsx` `.csv` `.pptx` `.txt` … |

Detecta automáticamente cuál de los dos formatos de chat es.

---

## Límites conocidos

- **No hay export automático.** WhatsApp no tiene una API personal que permita leer
  tus grupos. La Groups API oficial exige cuenta de empresa verificada y topea en 8
  participantes; las librerías no oficiales violan los términos de servicio y ponen
  en riesgo el número. El export a mano son veinte segundos y no arriesga nada.
- La transcripción es automática y se equivoca: falla sobre todo con nombres
  propios, siglas y jerga. El método está escrito para corregir con criterio y
  **dejar constancia** de cada corrección, en vez de inventar. Aun así, revisá
  los nombres antes de usar el documento para algo que importe.
- El modelo `tiny` es rápido pero impreciso. Para español rioplatense usá
  `small`, que es el default.
- Los links a Google Drive, Docs y Sheets no se pueden abrir sin autenticación.
  Quedan registrados como fuentes externas.
- Los exports muy grandes (miles de mensajes, horas de audio) hay que procesarlos
  por lotes.

---

## Licencia

MIT. Usalo, cambialo, publicalo. Si te sirve, contame.

Hecho por [Keep Growing](https://keepgrowing.ar) — AI & Data, Buenos Aires.
