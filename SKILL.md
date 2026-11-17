---
name: whatsapp-export-deep-read
description: 'Lee al 100% un export de WhatsApp (el .zip o la carpeta con _chat.txt y adjuntos) y produce dos .md: un resumen ejecutivo y un documento completo con TODO procesado: mensajes de texto integros, audios y notas de voz transcriptos, videos vistos y transcriptos, PDF, Word, Excel, CSV y demas documentos leidos, imagenes analizadas visualmente, links relevados, mas sintesis, datos duros, inconsistencias y puntos abiertos. Usala SIEMPRE que se suba o mencione un export, backup, chat exportado o historial de WhatsApp (grupo o individual) y se pida leerlo, procesarlo, transcribirlo, resumirlo, analizarlo, extraer el conocimiento, pasarlo a un md, entender todo lo que paso ahi, o armar una base de conocimiento, minuta o informe a partir de el. Vale aunque el pedido venga casual (mira este chat y contame todo, transcribi los audios de este grupo) y aunque no se nombre la palabra export. NO la uses para chats pegados como texto plano sin adjuntos, ni para exports de Slack, Telegram o email.'
---

# WhatsApp Export → Documento de conocimiento total

El objetivo es que **ningún byte del export quede sin leer**. Un export típico
mezcla texto, notas de voz, fotos, planos, PDF, planillas y videos, y el 70% del
conocimiento real suele estar en los adjuntos, no en el texto. Un resumen que
solo lee `_chat.txt` es un resumen que perdió lo importante.

El entregable son **dos archivos .md**: un resumen de dos páginas con lo que la
persona quería saber, y un documento completo, mensaje por mensaje, que sirve
como base de conocimiento permanente del proyecto o de la conversación.

---

## Antes que nada: tres condiciones para poder empezar

Estas tres cosas se verifican **antes** de procesar nada. Si alguna falla, hay
que **frenar y decirlo**, no seguir y entregar un documento incompleto que
parece completo. Un documento así es peor que no entregar nada: el usuario no
tiene forma de darse cuenta de lo que falta.

**1. ¿El export trae los archivos?**
`inventory.py` corta solo con código 2 si detecta un export hecho sin adjuntos.
Si eso pasa, **no insistir, no usar `--solo-texto` por cuenta propia**: hay que
pedirle a la persona que vuelva a exportar incluyendo los archivos, y explicarle
cómo. El `--solo-texto` existe solo para cuando la persona, ya avisada, dice
explícitamente que quiere seguir igual.

**1 bis. ¿El export trae el historial completo?**
Hay una segunda forma de perder información en silencio, distinta de los
adjuntos: **exportar desde la aplicación de escritorio con el chat sin cargar
entero**. Sale un export que parece normal y al que le falta conversación
vieja, sin que nada avise.

El inventario lo marca en `reporte.historial`. Si el estado es
`posiblemente_incompleto` —un grupo sin aviso de creación y sin uno de que
sumaron a la persona después—, **decírselo antes de procesar**:

> Este export arranca el <fecha> y no trae el aviso de creación del grupo, así
> que puede faltarte conversación anterior. Suele pasar al exportar desde la
> aplicación de escritorio. Si el grupo es más viejo que eso, conviene volver a
> exportarlo desde el teléfono, que trae el historial completo. ¿Seguimos con
> este o lo rehacés?

Si la persona decide seguir, **el documento lo declara en la cobertura**: no se
puede prometer que se leyó todo cuando falta el principio.

En un chat de dos personas no hay aviso de creación y el estado es
`no_se_puede_saber`: ahí no hay nada que decir.

**2. ¿Hay salida a internet, y de quién es la máquina?**

Son **dos preguntas distintas** y conviene no confundirlas. El motor se baja de
PyPI y de GitHub, así que sin internet no hay transcripción, corra donde corra.
Y hay entornos en la nube **con** internet, donde el motor se instala y
transcribe perfecto: lo que cambia ahí no es si funciona, es de quién es la
computadora por la que pasa el audio.

Si `pip` falla con 403, "host not in allowlist" o "Name or service not known",
el diagnóstico correcto es **"este entorno no tiene salida a internet"**, no
"estás en un servidor". Frenar y decírselo con estas palabras:

> Desde acá no puedo bajar el motor que transcribe los audios: este entorno no
> tiene salida a internet.
>
> **Si los archivos están en tu computadora**, ese es el mejor lugar para
> hacerlo: abrí la aplicación de escritorio de Claude, entrá en Cowork, dale
> acceso a la carpeta del export y pedímelo de nuevo desde ahí. Si te deja
> elegir dónde correr la tarea, elegí **en tu computadora**. Así el audio no
> sale de tu máquina.
>
> **Si estás en el celular**, no hay una app de escritorio que abrir: desde el
> teléfono yo trabajo en una computadora prestada que se borra al terminar. Eso
> significa bajar el motor de 1 GB en cada sesión, y que tus audios viajen
> hasta esa computadora ajena en lugar de quedarse en la tuya. Si el grupo
> tiene cosas de clientes, conviene hacerlo desde una computadora.

**Dos reglas al dar ese mensaje.**

**Nombrar el caso del teléfono.** Decir solo "abrí la aplicación de escritorio"
a alguien que está en el celular es pedirle algo que desde ahí no existe, sin
avisarle que necesita cambiar de aparato.

**No decir que la nube no puede.** Puede, cuando tiene internet. Lo que cambia
es de quién es la máquina por la que pasa el audio, y eso se dice como lo que
es —una decisión de la persona sobre sus datos— y no como una limitación
técnica inventada.

No ofrecer procesar "todo lo demás igual" como si fuera una alternativa
razonable. Sin los audios, el resultado es un volcado del chat: exactamente lo
que este skill existe para reemplazar.

**3. ¿Están los scripts?**
Si hay `SKILL.md` pero falta la carpeta `scripts/`, la instalación quedó
incompleta —pasa cuando se guarda el skill desde una tarjeta de "guardar skill",
que copia solo este archivo. Decirlo y pedir la carpeta completa del repositorio
en vez de intentar el proceso a mano: sin `transcribe.py` no hay transcripción.

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
9. **Verificar lo que se escribió**
10. Entregar

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
- **Un `.zip` adentro del export.** Pasa cuando alguien reenvía al grupo otro
  chat exportado. El inventario lo lista como `otro`. No se procesa solo:
  decidir con la persona si entra —es un chat completo, con sus propios
  adjuntos— y, si entra, correrle el skill aparte. Lo que no corresponde es
  ignorarlo en silencio: listarlo siempre en la sección de cobertura.

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
python3 <skill>/scripts/transcribe.py <carpeta>
```

Sin `--glob`, toma todos los audios y videos de la carpeta y saltea lo que no
sea ni una cosa ni la otra. Con `--glob '*.opus'` se limita a las notas de voz,
pero entonces **los videos y los audios reenviados (`.m4a`, `.mp3`) quedan sin
transcribir**, que es justo lo que el documento promete no dejar afuera.

### Volver a correrlo sobre un export nuevo del mismo chat

Es el caso normal: el grupo sigue hablando y la persona exporta de nuevo a la
semana. **No hay que retranscribir lo que ya se transcribió.**

`transcribe.py` guarda cada resultado en el JSON de salida y **saltea todo lo
que ya esté ahí**. Y los nombres de archivo de WhatsApp son estables entre
exports: en una prueba contra dos exports reales del mismo grupo, separados por
cinco semanas, **los 46 archivos del viejo aparecían con el nombre idéntico en
el nuevo**, sin un solo renombrado.

Para que eso sirva hay que trabajar siempre en la misma carpeta:

```bash
# descomprimir el export nuevo ENCIMA de la carpeta de trabajo de siempre
unzip -o "export-nuevo.zip" -d <carpeta-de-trabajo>
python3 <skill>/scripts/inventory.py <carpeta-de-trabajo>
python3 <skill>/scripts/transcribe.py <carpeta-de-trabajo>   # solo lo nuevo
```

Si en cambio se descomprime en una carpeta nueva, no encuentra el JSON viejo y
**vuelve a transcribir todo**. En un grupo con mucho audio eso puede ser
media hora de cómputo tirada.

Lo que **no** es incremental y hay que asumir en cada corrida:

- El inventario se rehace entero. Es barato: 20.000 mensajes en 0,3 s.
- Las imágenes y los videos se vuelven a mirar.
- **Los dos documentos se reescriben de cero.** Si el anterior tenía
  correcciones hechas a mano, hay que volver a aplicarlas. Conviene guardar el
  anterior antes de sobrescribirlo y, al escribir el nuevo, marcar en la línea
  de tiempo desde dónde empieza lo que no estaba en la corrida pasada.

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
- Corregir errores evidentes y anotarlos. El patrón típico: una sigla que sale
  con una letra de más, y palabras que el motor cambia por otras parecidas
  —`habilitación` por "visitación", `inversión` por "inmersión"—, que es peor
  porque la frase sigue teniendo sentido.
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

**No escribir `ffmpeg` a secas.** Cuando el instalador resolvió ffmpeg con el
paquete de pip —el caso de cualquier máquina sin Homebrew— no queda ningún
`ffmpeg` en el PATH y el comando falla. Pedirle la ruta al propio skill:

```bash
FF=$(python3 <skill>/scripts/ffmpeg_tools.py)

# audio del video → mismo pipeline de transcripción
"$FF" -i video.mp4 -ar 16000 -ac 1 -vn wav/video.wav

# fotogramas clave para mirar (1 cada 3 s, más el primero)
"$FF" -i video.mp4 -vf "fps=1/3" frames/video_%03d.jpg
```

La banda de audio ya extraída se transcribe con el mismo script; `transcribe.py`
también acepta el `.mp4` directamente y le saca el audio solo.

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

#### Las celdas con fórmula vuelven vacías, y eso vacía la columna del dinero

Un `.xlsx` guarda la fórmula y, aparte, el último valor que Excel calculó. Una
planilla que se armó con un script, o que se mandó sin abrirse, **no tiene ese
valor guardado**: pandas y openpyxl devuelven `NaN` o `None` en cada celda
calculada.

En una planilla de presupuesto eso significa que **los subtotales y el total
—es decir, todo lo que importa— vuelven en blanco**, sin ningún aviso. El
documento sale sin un solo número y nada indica que falte algo.

Hay que **mirar siempre las dos versiones** y comparar:

```bash
python3 - <<'PY'
from openpyxl import load_workbook
for modo, etq in ((True, "valor guardado"), (False, "formula")):
    ws = load_workbook("archivo.xlsx", data_only=modo).active
    print("==", etq)
    for fila in ws.iter_rows(values_only=True):
        print("  ", fila)
PY
```

Si con `data_only=True` las celdas vienen vacías y con `data_only=False`
aparece algo como `=B5*C5`, **la planilla no trae los resultados y hay que
calcularlos**: leer las fórmulas, reproducir la cuenta y dejar escrito en la
nota metodológica que esos números se recalcularon y no se copiaron. Después
pasan por la verificación de la etapa 9 como cualquier cuenta propia.

Lo mismo vale para una planilla que llega **con** valores guardados: si un
total no coincide con la suma de sus componentes, el valor guardado quedó
viejo. Decirlo, no elegir uno en silencio.

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

## 8. Escribir los documentos

**Son dos archivos, no uno.** `references/output-template.md` trae las dos
plantillas.

| Archivo | Qué es | Extensión |
|---|---|---|
| `<nombre> — resumen.md` | Lo que la persona quería saber | Dos páginas |
| `<nombre> — completo.md` | Todo el respaldo, mensaje por mensaje | Sin techo |

Quien pide esto quiere **entender la conversación**, no recorrerla. Un archivo
de seiscientas líneas entrega la materia prima de entender, no el entender. El
completo existe porque es la prueba de que se leyó el 100% y porque es donde se
busca el detalle — pero **el entregable es el corto**.

Escribir primero el completo, porque el resumen se destila de él. Entregar los
dos y decir en una línea cuál abrir primero.

El resumen lleva: cobertura, qué pasó (5 a 10 viñetas con fecha), decisiones
tomadas, pendientes con responsable, datos duros y puntos abiertos. Si no entra
en dos páginas, lo que sobra va al completo.

Estructura del completo:

```
0. Cobertura (qué se leyó y qué no)    ← primero, siempre
1. Lo que hay que saber                ← la síntesis, arriba
      decisiones tomadas · pendientes con responsable · datos duros
2. Índice
3. Inventario del export (tabla con todos los archivos, duplicados, huecos)
4. Participantes (quién es quién, rol inferido, terceros mencionados)
5. Línea de tiempo completa  ← el respaldo, mensaje por mensaje
6..N. Anexos por documento (texto íntegro de cada PDF/planilla)
      Anexo de planos / imágenes
      Anexo de normativa, especificaciones o fuentes citadas
N+1. Síntesis extendida
N+2. Datos duros en un solo lugar (tablas)
N+3. Puntos abiertos, inconsistencias y riesgos detectados
N+4. Nota metodológica
```

**El orden importa y no es negociable.** La síntesis va arriba porque quien abre
el documento quiere entender la conversación, no recorrerla. Si lo primero que
encuentra es el chat día por día, cierra el archivo antes de llegar a lo que
vale — y concluye, con razón, que la herramienta no agregó nada.

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
- **Hacer las cuentas que nadie hizo.** Si alguien dice un aporte y qué
  porcentaje quiere que represente, calcular el total implícito y compararlo
  con el número que se venía manejando. Ese tipo de cruce suele ser el hallazgo principal del documento.
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

## 9. Verificar lo que se escribió

Las etapas 1 a 7 las hacen scripts probados. La etapa 8 la escribe el modelo, y
ahí entran al documento datos que **no estaban en el export**: porcentajes,
totales, plazos, diferencias de fechas. Son el aporte principal del documento y
son lo único que nadie verificó.

Un número inventado con cara de hallazgo es peor que una omisión: el lector no
tiene cómo detectarlo, y si lo descubre después deja de confiar en todo lo
demás. Esta etapa no es opcional.

### 9.1 Recalcular todas las cuentas propias

Hacer una lista de **cada cuenta que el documento afirma** y recalcularla
**ejecutando código**, nunca de memoria. Una por una, con el valor que dice el
documento al lado del valor real.

```bash
python3 - <<'PY'
from datetime import date
def v(etq, dice, real):
    print(("OK   " if dice == real else "ERROR"), etq, "| dice", dice, "| real", real)
v("IVA 21% de 10.000", 2100, round(10000*0.21))
v("14.200 es X% mas que 10.000", 21, round((14200-10000)/10000*100))
v("vencimiento 5/8 + 30 dias", "2026-09-04", str(date(2026,8,5)+__import__("datetime").timedelta(days=30)))
PY
```

Entran en la lista: sumas y totales, **porcentajes de variación**, promedios,
conversiones, cantidades de días entre dos fechas, vencimientos, antigüedades y
cualquier "X veces más".

**La trampa más común es el porcentaje.** Si en la misma tabla hay una alícuota
—IVA 21 %, un recargo, un descuento—, es fácil escribir esa cifra en lugar del
aumento real. El patrón, con números de ejemplo: el documento dice que un total
de 14.200 es *"un 21 % más"* que uno anterior de 10.000. Es **42 %**; el 21 era
la alícuota de IVA que estaba tres renglones más arriba.

Si una cuenta da distinto, **corregir el documento**, no la cuenta.

### 9.2 Verificar que cada cita textual exista

Toda frase entrecomillada como cita tiene que aparecer **literal** en alguna
fuente: el `_chat.txt`, una transcripción, el texto de un documento o lo leído
en una imagen. Buscarlas normalizando espacios y saltos de línea, que es donde
fallan las comparaciones ingenuas.

Si una cita se normalizó —una tilde que el original no tenía, puntuación
agregada para que se lea— **decirlo en la nota metodológica**. Si una elisión
junta dos tramos separados, que el `…` esté.

### 9.3 Cotejar los conteos

- Mensajes en la línea de tiempo **contra** el total del inventario.
- Mensajes por participante **contra** el inventario.
- Transcripciones **contra** cantidad de audios.
- Imágenes descriptas **contra** imágenes del export.

Si alguno no cierra, el documento no está terminado.

### 9.4 Chequear que el resumen no haya perdido lo que importa

Cada dato duro de la tabla del completo tiene que poder buscarse en el resumen
o estar deliberadamente afuera. Un dato que solo vivía en una imagen o en un
audio y que se perdió al destilar es el peor lugar donde perderlo: es
exactamente lo que nadie más iba a encontrar.

### 9.5 Decir que se verificó

En la nota metodológica, una línea con qué se verificó y qué se corrigió. Si
una cuenta salió mal y se arregló, **dejarlo escrito**. Un documento que
muestra sus correcciones es más confiable que uno que aparenta no haberlas
necesitado.

---

## 10. Entregar

Guardar **los dos `.md`** junto al export, con un nombre que identifique la
conversación, y entregarle los dos al usuario diciendo cuál abrir primero:

> Te dejo dos archivos. Abrí **`<nombre> — resumen.md`**: son dos páginas con
> lo que se habló, las decisiones y los pendientes. El otro, `<nombre> —
> completo.md`, tiene todo el respaldo mensaje por mensaje, por si querés ir al
> detalle de algo.

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

Ese recuento es la prueba de que se leyó el 100%, y por eso va **también al
principio del documento**, no solo en el chat. Es lo primero que necesita ver
alguien que abre el `.md`: qué se leyó y qué no.

Si algo quedó sin procesar, decirlo ahí en vez de omitirlo. Y si la cobertura de
audios quedó en cero habiendo audios en el export, eso no es una línea más del
recuento: es un **fracaso del procesamiento** y hay que encabezar la respuesta
con eso, explicando por qué pasó y cómo se arregla. Entregar un documento sin
audios como si fuera el producto terminado es el peor resultado posible.

---

## Archivos del skill

- `scripts/inventory.py` — descomprime, inventaria, detecta duplicados por MD5,
  parsea `_chat.txt` a JSON y lista los adjuntos mencionados que faltan.
- `scripts/setup_asr.py` — instala sherpa-onnx y baja el modelo Whisper desde
  GitHub Releases. Todo corre local: el audio no sale de la máquina.
- `scripts/transcribe.py` — convierte a wav 16 kHz mono y transcribe en lotes.
- `references/output-template.md` — plantilla completa del documento de salida.
- `references/troubleshooting.md` — qué hacer cuando algo del pipeline falla.
