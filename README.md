# whatsapp-export-deep-read

Lee **todo** un export de WhatsApp —no solo el texto— y lo convierte en un único
archivo Markdown que sirve como memoria permanente de esa conversación.

Transcribe los audios. Mira los videos. Lee los PDF, los Word, los Excel y los CSV.
Analiza las imágenes una por una. Releva los links. Y arma una línea de tiempo
completa con todo en su lugar.

La mayor parte de lo que se habló no está en el texto del chat: está en las notas
de voz que nadie volvió a escuchar y en los adjuntos. Un resumen que solo lee
`_chat.txt` es un resumen que perdió lo importante.

**No es solo para Claude.** Son dos cosas: unos scripts que hacen el trabajo
pesado —transcribir, inventariar, leer documentos— y un método que le dice al
asistente cómo usarlos. Los scripts son Python y corren en cualquier lado. El
método viene en dos envases: [`SKILL.md`](SKILL.md) si usás Claude, e
[`INSTRUCCIONES.md`](INSTRUCCIONES.md) para pegar en cualquier otro asistente.

Lo único que hace falta es un asistente que pueda **ejecutar cosas en tu
máquina**. No hace falta que sepas programar ni que abras una terminal: vos le
pedís, él lo corre.

---

## Qué te devuelve

**Dos archivos.**

**`<grupo> — resumen.md`** es el que vas a leer: dos páginas con lo que se
habló, las decisiones tomadas, los pendientes con nombre y apellido, los datos
duros y lo que quedó abierto. Cada punto con su fecha, para poder ir a buscarlo.

**`<grupo> — completo.md`** es el respaldo:

- Inventario del export: todos los archivos, duplicados detectados por MD5, y los
  adjuntos que alguien mencionó pero no están en el export
- Participantes y roles inferidos
- **Línea de tiempo completa**: cada mensaje con hora y emisor, cada audio
  transcripto en su posición cronológica, cada adjunto señalado donde se envió
- Anexos con el texto íntegro de cada documento
- Síntesis extendida, datos duros en tablas, y puntos abiertos e inconsistencias
- Nota metodológica: con qué se transcribió y qué quedó fuera

Son dos porque lo que querés es **entender la conversación**, y un archivo de
seiscientas líneas te da la materia prima de entender, no el entender. El largo
existe porque es la prueba de que se leyó todo y porque ahí vas a buscar el
detalle cuando lo necesites.

Los dos empiezan con el recuento de cobertura, que es esa prueba:

```
- Mensajes de texto leídos: 412 / 412
- Audios transcriptos: 23 / 23 (41:17)
- Videos procesados: 4 / 4
- Documentos leídos: 11 / 11
- Imágenes analizadas: 68 / 68
- Adjuntos mencionados pero ausentes del export: 3
```

---

## Instalación

### Si no programás

Tres pasos. No hace falta terminal.

**1. Bajá el proyecto.** Arriba en esta página: botón verde **Code** →
**Download ZIP**. Descomprimí el archivo donde quieras.

**2. Instalá la aplicación de escritorio de Claude**, desde
[claude.ai/download](https://claude.ai/download). Abrila, entrá en **Cowork** y
dale acceso a esa carpeta.

> **El Claude del navegador no sirve para esto**, y es el error más común.
> Alguien que probó esto lo hizo desde claude.ai en el navegador, sin saber que
> existía otra cosa; cuando le preguntaron si había usado Cowork contestó *"ni
> idea, ¿dónde me fijo?"*. Es una pregunta razonable, así que: **Cowork es un
> modo de la aplicación de escritorio**, la que se baja de ese link, y es la
> única que puede tocar archivos de tu disco.
>
> Lo confuso es que el Claude del navegador **igual ejecuta comandos** y te
> devuelve un documento con buena pinta. Pero corre en un servidor, no en tu
> computadora: ahí el motor de transcripción no se puede instalar y **los audios
> no se transcriben**. Lo que te devuelve es el texto del chat ordenado, que es
> justo lo que este proyecto existe para superar.
>
> La regla simple: **los archivos tienen que estar en tu disco y Claude tiene
> que estar corriendo en tu máquina.**

**3. Pedíselo:**

> Instalá el skill de esta carpeta: corré `scripts/setup_asr.py`.

El asistente hace el resto. Tarda unos minutos porque baja el modelo de
transcripción (1 GB). Si te falta ffmpeg, **lo instala solo**: no necesitás
Homebrew, ni winget, ni permisos de administrador.

Cuando termine, pedile que lea tu export:

> Leé este export de WhatsApp: `/ruta/al/export.zip`

Te devuelve los dos archivos. Empezá por el que dice **resumen**.

### Si preferís hacerlo a mano

```bash
git clone https://github.com/carralbal/whatsapp-export-deep-read.git
cd whatsapp-export-deep-read

python scripts/setup_asr.py --check    # diagnostica, no instala nada
python scripts/setup_asr.py            # modelo small, ~1 GB
python scripts/setup_asr.py tiny       # más liviano y rápido, menos preciso
```

El modelo queda en `~/.whatsapp-deep-read/`. Para moverlo: `ASR_HOME=/otra/ruta`.

*(En Windows el comando suele ser `python`; en macOS y Linux, `python3`.)*

### Para que Claude lo active solo

Copiá la carpeta a tus skills y se activa cada vez que menciones un export:

```bash
mkdir -p ~/.claude/skills
cp -r whatsapp-export-deep-read ~/.claude/skills/
```

En Cowork alcanza con dejar la carpeta donde la sesión tenga acceso.

### Con ChatGPT Work *(probablemente no alcance)*

Los scripts son Python puro y no dependen de Claude en absoluto: el único
componente específico de Claude es el `SKILL.md`, que se reemplaza por
[`INSTRUCCIONES.md`](INSTRUCCIONES.md). Así que en principio cualquier asistente
con acceso a tu disco debería poder usarlos.

El problema con ChatGPT Work es otro. Según el centro de ayuda de OpenAI, Work
**accede a carpetas locales**, pero **ejecutar programas en tu máquina es tarea
de Codex, no de Work**. Y acá hace falta ejecutar: sin correr `setup_asr.py` y
`transcribe.py` no hay transcripción.

Si eso es así, en ChatGPT Work vas a poder leer el texto, los documentos y las
imágenes, pero **ningún audio**. Que es justamente la parte por la que este
proyecto existe.

> **No lo probamos.** La distinción Work / Codex sale de la documentación, no de
> haberlo corrido, y la propia gente de OpenAI tiene un issue abierto sobre lo
> confuso que es el tema. Si lo intentás, contá qué pasó cuando le pediste
> correr `scripts/setup_asr.py`: si lo corrió o si se negó. Con eso alcanza para
> saberlo y lo documentamos acá.

### Con cualquier otro asistente

Si puede leer archivos de tu máquina, pedile lo mismo del punto 3: que lea
[`INSTRUCCIONES.md`](INSTRUCCIONES.md) y lo siga.

Si no puede —un chat web común— pegá el contenido de ese archivo como
instrucción de tu proyecto y subile el export a mano. Funciona con el texto,
las imágenes y los documentos; **los audios y los videos quedan afuera**, porque
ningún asistente escucha un `.opus` sin el motor local.

---

## Requisitos

- **Python 3.8 o más nuevo.** macOS y la mayoría de los Linux ya lo traen. En
  Windows: `winget install Python.Python.3.12`
- **Un asistente que pueda ejecutar scripts y leer archivos de tu máquina**:
  Claude Cowork, Claude Code, o cualquier otro con esa capacidad. Pegando esto
  en un chat web no funciona, porque ese chat no ve tu disco.
- **~1 GB de disco** para el modelo de transcripción, o ~110 MB con `tiny`.

**ffmpeg no está en esta lista a propósito**: el instalador lo resuelve solo si
falta. Si igual preferís el del sistema —es más completo, trae `ffprobe`—:
`brew install ffmpeg` en macOS, `sudo apt install ffmpeg` en Linux.

**Opcional:** `poppler-utils` (`brew install poppler`) mejora la lectura de PDF.
Sin él el inventario no cuenta páginas, pero todo lo demás funciona.

**Plataformas:** macOS y Linux, verificados. Windows debería funcionar —todo es
Python puro, no necesita bash ni WSL— pero **todavía no lo probó nadie en
Windows real**. Si sos el primero, hay notas en
[`references/troubleshooting.md`](references/troubleshooting.md) y se agradece
el reporte.

---

## Uso

**1. Exportá el grupo con los archivos.** En WhatsApp: abrí el grupo → buscá
**Exportar chat**. Te va a preguntar si incluís los archivos: **decí que sí.**
Según la versión el botón dice *Adjuntar archivos*, *Incluir archivos* o *Con
multimedia*.

> Este es el paso donde más gente se equivoca, y no avisa. Si no te preguntó
> nada, o si el archivo que te quedó pesa unos pocos kilobytes, exportaste **sin
> los archivos**: está el texto y nada más. Un export con los adjuntos pesa
> megas, a veces cientos. Volvé a hacerlo.
>
> Si igual se te pasa, el inventario lo detecta y frena antes de procesar.

**2. Dejá el `.zip` en una carpeta** a la que tu asistente tenga acceso.

**3. Pedile que lo lea**, desde la aplicación de escritorio corriendo en tu
computadora.

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

## Preguntas frecuentes

### ¿Tengo que usar la terminal?

No. Bajás el ZIP, lo descomprimís, y le decís a Claude Cowork
*"instalá el skill de esta carpeta"*. El asistente corre todo, incluido ffmpeg
si te falta. Después le pedís *"leé este export de WhatsApp"* y listo.

Los comandos de este README son la vía manual, no la única.

Lo que hace falta no es una terminal: es **un asistente que pueda ejecutar
cosas en tu máquina**.

### ¿Funciona con ChatGPT?

Depende de cuál.

**ChatGPT web o celular: no.** No puede leer archivos de tu disco. Tendrías que
subir el export entero, que choca con el límite de tamaño por archivo y además
manda toda la conversación del grupo a sus servidores — justo lo que este skill
evita.

**ChatGPT Work en la app de escritorio: probablemente no alcance.** Accede a
carpetas locales con tu permiso, pero ejecutar programas en tu máquina es tarea
de Codex, no de Work — y acá hace falta ejecutar. Sin eso tendrías el texto y
los documentos, pero ningún audio. **No está verificado**: si lo probás, contá
qué pasó cuando le pediste correr `scripts/setup_asr.py`.

**Cualquier asistente, sin instalar nada: parcialmente.** Pegá
[`INSTRUCCIONES.md`](INSTRUCCIONES.md) como instrucción de tu proyecto. Funciona
con el texto, las imágenes y los documentos. Los audios y los videos quedan
afuera, porque ningún asistente escucha un `.opus` por su cuenta.

### ¿Los audios salen bien en español rioplatense?

Bien, no perfecto. Habla espontánea con muletillas sale legible de punta a
punta. Falla con nombres propios, siglas y jerga — y el error más frecuente en
conversaciones sobre tecnología es **"IA" transcripto como "idea"**, difícil de
notar porque la frase sigue teniendo sentido.

Por eso el método separa transcribir de interpretar: el motor transcribe, el
asistente corrige con el contexto y **deja constancia de cada corrección**.

### ¿De verdad no sube nada a ningún lado?

El modelo de transcripción corre en tu máquina: **el audio no sale de ahí.** Lo
que sí viaja es el texto que el asistente lee, que queda en el historial de tu
conversación — igual que con cualquier archivo que le pases. Eso vale tanto para
Claude como para ChatGPT.

---

## Licencia

MIT. Usalo, cambialo, publicalo. Si te sirve, contame.

Hecho por [Keep Growing](https://keepgrowing.ar) — AI & Data, Buenos Aires.
