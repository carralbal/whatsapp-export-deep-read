---
name: whatsapp-export-deep-read
description: 'Lee al 100% un export de WhatsApp (el .zip o la carpeta con _chat.txt y adjuntos) y produce un unico .md exhaustivo con TODO procesado: mensajes de texto integros, audios y notas de voz transcriptos, videos vistos y transcriptos, PDF, Word, Excel, CSV y demas documentos leidos, imagenes analizadas visualmente, links relevados, mas sintesis, datos duros, inconsistencias y puntos abiertos. Usala SIEMPRE que se suba o mencione un export, backup, chat exportado o historial de WhatsApp (grupo o individual) y se pida leerlo, procesarlo, transcribirlo, resumirlo, analizarlo, extraer el conocimiento, pasarlo a un md, entender todo lo que paso ahi, o armar una base de conocimiento, minuta o informe a partir de el. Vale aunque el pedido venga casual (mira este chat y contame todo, transcribi los audios de este grupo) y aunque no se nombre la palabra export. NO la uses para chats pegados como texto plano sin adjuntos, ni para exports de Slack, Telegram o email.'
---

# WhatsApp Export → Documento de conocimiento total

El objetivo es que **ningún byte del export quede sin leer**. Un export típico
mezcla texto, notas de voz, fotos, planos, PDF, planillas y videos, y el 70% del
conocimiento real suele estar en los adjuntos, no en el texto. Un resumen que
solo lee `_chat.txt` es un resumen que perdió lo importante.

El entregable es **un solo archivo .md** que sirve como base de conocimiento
permanente del proyecto o de la conversación.

---

## Flujo de trabajo

Seguir este orden. Cada etapa alimenta a la siguiente.

1. Descomprimir e inventariar
2. Leer `_chat.txt` completo
3. Transcribir audios
4. Procesar videos
5. Leer documentos (PDF, Office, CSV, texto)
6. Analizar imágenes
7. Relevar links
8. Escribir el documento
9. Entregar

No empezar a escribir el documento hasta terminar las etapas 1 a 7. Escribir
antes lleva a un documento que describe lo que se vio primero y trata el resto
de refilón.

---

## 1. Descomprimir e inventariar

`inventory.py` acepta el `.zip` directamente: lo descomprime al lado del
archivo, inventaria todo y parsea el chat a JSON.

```bash
python3 <skill>/scripts/inventory.py /ruta/al/export.zip
# o, si ya lo descomprimiste:
python3 <skill>/scripts/inventory.py /ruta/a/la/carpeta
```

Reconoce los dos formatos de export, iPhone y Android, y lo informa.

Cosas que importan acá:

- **Duplicados por MD5.** WhatsApp reenvía el mismo archivo con otro número de
  secuencia. Hay que detectarlos, procesarlos una sola vez y decirlo en el
  documento (quién reenvió qué a quién es información, no ruido).
- **Adjuntos mencionados que no están.** Es habitual que alguien diga "les paso
  los 2 PDF de la municipalidad" y esos PDF no estén en el export. Cada una de
  esas menciones es un hueco que va listado en el documento final.
- **Duración total de audio y cantidad de páginas de PDF**, para dimensionar el
  trabajo antes de empezar.

---

## 2. Leer `_chat.txt` completo

Leer el archivo entero, no una muestra. El formato es:

```
[DD/M/AA, HH:MM:SS] Remitente: mensaje
‎[DD/M/AA, HH:MM:SS] Remitente: ‎<adjunto: NNNNNNNN-TIPO-fecha.ext>
```

Detalles que cambian la interpretación:

- Los mensajes de sistema (cifrado, creación del grupo, "te añadió") llevan un
  carácter invisible U+200E al inicio. Sirven para fechar la creación del grupo
  y saber quién lo creó.
- `‎<Se editó este mensaje.>` marca mensajes editados: si hay dos versiones de
  una lista de pendientes, **la editada es la vigente** y la anterior es
  historia útil.
- Los mensajes largos traen saltos de línea internos; no cortarlos.
- Las tablas pegadas desde otra app llegan con tabulaciones. Reconstruirlas como
  tablas markdown en el documento, sin alterar ni un número.
- Los timestamps de los adjuntos en la línea del chat a veces difieren del
  nombre del archivo. Usar el del chat para la cronología.

---

## 3. Transcribir audios

No hay motor de reconocimiento de voz preinstalado y los CDN de modelos
habituales están bloqueados. La ruta que funciona es **sherpa-onnx desde PyPI +
modelo Whisper desde GitHub Releases**.

```bash
python <skill>/scripts/setup_asr.py        # instala sherpa-onnx y baja el modelo
```

Después:

```bash
python3 <skill>/scripts/transcribe.py <carpeta> --glob '*.opus'
```

### Reglas críticas de ejecución

- **Nunca correr la transcripción en background** (`&`, `nohup`). Los procesos en
  segundo plano se congelan o mueren entre llamadas de herramienta y se pierde
  todo el trabajo. Correr siempre en primer plano.
- **Partir en lotes** de aproximadamente 2 a 3 minutos de audio por llamada,
  para que cada lote termine dentro del límite de una ejecución. `transcribe.py`
  acepta una lista de archivos, así que se lo invoca varias veces.
- Verificar al final que la cantidad de transcripciones coincide con la cantidad
  de audios. Un audio sin transcribir invalida el documento.

### Calidad de la transcripción

El modelo `small` alcanza para español rioplatense, pero falla con nombres
propios, siglas y jerga. Corregir con criterio y **dejar constancia**:

- Normalizar puntuación y concordancias para que el texto se lea.
- Corregir errores evidentes y anotarlos: `ANMAT` (el motor dijo "ANTMAT"),
  `habilitación` ("visitación"), `inversión` ("inmersión").
- Cuando una frase quedó realmente irrecuperable, decirlo en vez de inventar:
  *"(fragmento distorsionado; el sentido es que…)"*.
- Nunca poner entre comillas como cita textual algo que el motor entregó
  dudoso sin marcarlo.

Cada transcripción va en el documento **en su posición cronológica dentro de la
línea de tiempo**, con emisor, duración y hora. Un anexo separado de audios rompe
la lectura.

---

## 4. Procesar videos

Un video son dos fuentes de información: la banda de audio y las imágenes.
Procesar las dos.

```bash
# audio del video → mismo pipeline de transcripción
ffmpeg -i video.mp4 -ar 16000 -ac 1 -vn wav/video.wav

# fotogramas clave para mirar (1 cada 3 s, más el primero)
ffmpeg -i video.mp4 -vf "fps=1/3" frames/video_%03d.jpg
```

Después mirar los fotogramas con la herramienta de visión y describir qué se ve:
si es una recorrida por una obra, describir el estado de la obra; si es una
pantalla, leer lo que dice. Para videos largos, mirar primero un muestreo y
densificar donde haya información.

En el documento, cada video lleva: duración, transcripción del audio y
descripción de lo que muestra.

---

## 5. Leer documentos

### PDF

```bash
pdfinfo doc.pdf; pdffonts doc.pdf
pdftotext -layout doc.pdf -        # si hay capa de texto
```

Si `pdffonts` viene vacío, o si es un plano, un deck, un escaneo o algo donde el
layout es el contenido, **rasterizar y mirar**:

```bash
pdftoppm -jpeg -r 100 doc.pdf png/doc
```

y abrir cada página con la herramienta de visión. En planos de arquitectura o
ingeniería hay que leer y transcribir: el rótulo completo (obra, estudio,
escala, formato, número de documento, revisiones), todas las cotas legibles,
los rótulos de locales y el amoblamiento dibujado. Cuando hay varias versiones
del mismo plano, **armar una tabla de diferencias** entre ellas: eso es lo que
la gente necesita para decidir.

### Excel, Word, CSV

Si hay skills de `xlsx` o `docx` disponibles en la sesión, leerlos antes de
tocar esos archivos. Para planillas, volcar **todas** las hojas, no solo la primera, y llevar al documento
los datos, no una descripción de los datos. Para Word, extraer el texto íntegro
más tablas y comentarios.

```bash
python3 -c "
import pandas as pd
x = pd.ExcelFile('archivo.xlsx')
for h in x.sheet_names:
    print('===', h); print(x.parse(h).to_markdown(index=False))
"
```

### Links a Google Sheets / Docs / Drive

No se pueden abrir sin autenticación. Registrarlos en el documento como fuentes
externas con quién los compartió y cuándo, y avisarlo en los huecos de
información. Si hay un conector de Drive disponible en la sesión, usarlo.

---

## 6. Analizar imágenes

Mirar **todas** las imágenes, una por una, con la herramienta de visión. No
alcanza con decir "foto de una recepción". Para cada una, extraer:

- Qué se ve, con el nivel de detalle que permita no tener que volver a abrirla.
- **Todo dato legible**: cotas, precios, nombres, fechas, textos de pantalla,
  etiquetas de productos, números de serie.
- Qué función cumple en la conversación (referencia estética, prueba de un pago,
  captura de un presupuesto, plano acotado).
- Si es una captura de otra app, transcribir lo que dice.

Cuando un dato de una imagen contradice o tensiona algo del texto, marcarlo. Ese
tipo de cruce es lo que hace valioso al documento.

---

## 7. Relevar links

Listar todas las URLs del chat con quién las mandó y para qué. Si hay búsqueda
web disponible y el link es normativo, técnico o de producto, abrirlo y
resumirlo. Si el contenido del link ya fue pegado en el chat, no hace falta.

---

## 8. Escribir el documento

Usar la estructura de `references/output-template.md`. Es la que se probó y
funciona. Resumen de las secciones:

```
0. Índice
1. Inventario del export (tabla con todos los archivos, duplicados, huecos)
2. Participantes (quién es quién, rol inferido, terceros mencionados)
3. Línea de tiempo completa  ← el corazón del documento
4..N. Anexos por documento (texto íntegro de cada PDF/planilla)
      Anexo de planos / imágenes
      Anexo de normativa, especificaciones o fuentes citadas
N+1. Síntesis de conocimiento consolidada
N+2. Datos duros en un solo lugar (tablas)
N+3. Puntos abiertos, inconsistencias y riesgos detectados
N+4. Nota metodológica
```

### Criterios de escritura

- **Literalidad en los datos, síntesis en el análisis.** Los números, cotas,
  montos, medidas y textos normativos se reproducen tal cual, incluso con sus
  erratas, marcadas con *(sic)*. El análisis va en su propia sección.
- **La línea de tiempo lleva todo**: cada mensaje con hora y emisor, cada audio
  transcripto en su lugar, cada adjunto señalado donde se envió. Un lector que
  solo lea esa sección tiene que poder reconstruir la conversación entera.
- **Marcar los silencios.** Un hueco de 45 días entre mensajes, con una reunión
  presencial adentro, es un dato: señalarlo con un aviso visible.
- **Separar lo dicho de lo inferido.** Lo que alguien dijo va como cita o
  transcripción; lo que se deduce va en la síntesis y se marca como deducción
  ("implicancia aritmética no discutida en el chat: …").
- **Hacer las cuentas que nadie hizo.** Si alguien dice "puedo poner 40.000 y
  quiero que sea el 30%", calcular el total implícito y compararlo con el número
  original. Ese tipo de cruce suele ser el hallazgo principal del documento.
- **La sección de puntos abiertos es obligatoria** y se divide en:
  inconsistencias internas de los documentos, riesgos técnicos o legales, vacíos
  de información, y qué está sólido. Si no hay nada que poner en "qué está
  sólido", probablemente falta leer algo.
- **Nota metodológica al final**: con qué se transcribió, qué se rasterizó, qué
  quedó fuera de alcance y por qué. Permite auditar el documento.

### Longitud

No hay techo. El documento del caso de referencia tenía 600 líneas para un chat
de 60 mensajes y 16 adjuntos. Es mejor que sobre a que el lector tenga que
volver al zip.

---

## 9. Entregar

Guardar el `.md` junto al export, con un nombre que identifique la
conversación, y entregarlo al usuario.

En la respuesta del chat, **no repetir el documento**. Decir en pocas líneas los
dos o tres hallazgos que nadie había escrito todavía en la conversación
analizada, y cerrar con un recuento de cobertura:

```
- Mensajes de texto leídos: X / X
- Audios transcriptos: X / X (MM:SS)
- Videos procesados: X / X
- Documentos leídos: X / X
- Imágenes analizadas: X / X
- Adjuntos mencionados pero ausentes del export: X
```

Ese recuento es la prueba de que se leyó el 100%. Si algo quedó sin procesar,
decirlo ahí en vez de omitirlo.

---

## Archivos del skill

- `scripts/inventory.py` — descomprime, inventaria, detecta duplicados por MD5,
  parsea `_chat.txt` a JSON y lista los adjuntos mencionados que faltan.
- `scripts/setup_asr.py` — instala sherpa-onnx y baja el modelo Whisper desde
  GitHub Releases. Todo corre local: el audio no sale de la máquina.
- `scripts/transcribe.py` — convierte a wav 16 kHz mono y transcribe en lotes.
- `references/output-template.md` — plantilla completa del documento de salida.
- `references/troubleshooting.md` — qué hacer cuando algo del pipeline falla.
