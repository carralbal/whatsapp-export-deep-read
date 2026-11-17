# Instrucciones para cualquier asistente

Este archivo es el mismo método que el `SKILL.md`, pero escrito para pegarse
como instrucción en un asistente que **no** carga skills de Claude: ChatGPT,
Gemini, Copilot, o el que uses.

**Cómo usarlo:** pegá todo lo que está debajo de la línea en las instrucciones
de tu proyecto o en el primer mensaje de la conversación, y después pasale la
carpeta del export.

**Requisito:** el asistente tiene que poder ejecutar los scripts **en tu
computadora** y leer los archivos de una carpeta. Si tu asistente solo lee
archivos que le subís uno por uno, corré los scripts vos a mano (ver
`README.md`) y pasale el `.md` resultante.

**Sin internet no hay transcripción, corra donde corra.** Si al arrancar los
scripts aparece un error de red —`Name or service not known`, `host not in
allowlist`, un 403 de pip—, **frenar y decirlo**, no seguir sin los audios.

**Y conviene hacerlo en la computadora de la persona.** Desde el celular el
asistente trabaja en una máquina prestada que se borra al terminar: hay que
bajar el motor de 1 GB cada vez, y el audio del grupo viaja hasta esa máquina
ajena en lugar de quedarse en la propia. No es que no pueda funcionar —con
internet funciona—: es que el audio deja de ser privado, y eso lo decide la
persona, no el asistente.

---

## Objetivo

Leer un export de WhatsApp al 100% y producir **dos archivos Markdown** —un resumen
y un documento completo— que sirvan como memoria permanente de esa conversación.

La regla que ordena todo: **ningún byte del export queda sin leer.** La mayor
parte de lo que se habló no está en el texto del chat, está en las notas de voz
que nadie volvió a escuchar y en los adjuntos. Un resumen que solo lee
`_chat.txt` es un resumen que perdió lo importante.

## Orden de trabajo

Cada etapa alimenta a la siguiente. No saltear ninguna.

**0. Mirar si el export está entero.** El inventario avisa dos cosas antes de
procesar nada, y las dos son pérdidas silenciosas:

- **Export sin los archivos.** Corta solo. No insistir: pedirle a la persona
  que vuelva a exportar incluyendo los adjuntos.
- **Historial recortado.** Si es un grupo y el export no trae el aviso de
  creación ni uno de que sumaron a la persona después, puede faltar
  conversación vieja. Pasa al exportar desde la aplicación de escritorio con el
  chat sin cargar entero. **Decírselo** y ofrecer rehacerlo desde el teléfono,
  que siempre trae todo. Si se sigue igual, el documento lo declara en la
  sección de cobertura.

**1. Inventariar.** Correr `python scripts/inventory.py <ruta al .zip o a la
carpeta>`. Devuelve cantidad de mensajes, formato del export (iPhone o Android),
participantes, archivos por tipo, duración total de audio y video, duplicados
por MD5, huecos de conversación y —importante— los adjuntos que alguien mencionó
pero que no están en el export. Ese inventario es la lista de tareas.

**2. Leer el chat entero.** `_chat.txt` completo, no un muestreo. Registrar
quién habla, cuándo, y qué se decide.

**3. Transcribir todos los audios.** `python scripts/transcribe.py <carpeta>`.
Siempre en primer plano, nunca en segundo plano: si el proceso queda colgado
hay que verlo. Transcribir el 100%, no una muestra.

Sin `--glob` toma todos los audios **y los videos**, y saltea lo que no es ni
una cosa ni la otra. Si se lo limita con `--glob "*.opus"` quedan afuera los
videos y los audios reenviados (`.m4a`, `.mp3`).

Partir en lotes de 2 a 3 minutos de audio por llamada. El script acepta una
lista de archivos y **saltea lo que ya transcribió**, así que se lo puede
invocar muchas veces contra el mismo JSON de salida.

Dos cosas que el motor hace y hay que mirar: a veces **repite una palabra
decenas de veces** ante silencio o ruido —el script recorta esas rachas y las
marca; si aparece una marca así, no es algo que alguien dijo—, y un archivo
**sin pista de audio** (un GIF, un video mudo) no es un hueco: hay que mirarlo
como imagen.

**4. Procesar los videos.** El audio del video va por el mismo camino de
transcripción. Además, extraer fotogramas (uno cada 3 segundos más el primero)
y mirarlos.

**No escribir `ffmpeg` a secas**: si el instalador lo resolvió con el paquete
de pip, no queda ningún `ffmpeg` en el PATH. Pedirle la ruta al propio
proyecto:

```bash
FF=$(python scripts/ffmpeg_tools.py)
"$FF" -i video.mp4 -vf "fps=1/3" frames/video_%03d.jpg
```

**5. Leer los documentos.** PDF, Word, Excel, CSV, presentaciones: el texto
íntegro, no el resumen. Si un PDF es escaneado, convertirlo a imágenes y leerlo
visualmente.

**Ojo con las planillas.** Un `.xlsx` guarda la fórmula y, aparte, el último
valor que Excel calculó. Una planilla armada por un script, o mandada sin
abrirse, no tiene ese valor: pandas y openpyxl devuelven vacío en cada celda
calculada, y en un presupuesto eso es **toda la columna del dinero**. Leerla
con `data_only=True` y con `data_only=False` y comparar: si lo primero viene
vacío y lo segundo trae `=B5*C5`, hay que hacer la cuenta a mano y decirlo.

**6. Analizar las imágenes una por una.** Describir qué se ve y qué aporta a la
conversación. Las capturas de pantalla suelen contener información que no está
en ninguna otra parte.

**7. Relevar los links.** Los que se puedan abrir, abrirlos. Los que requieran
autenticación (Drive, Docs, Sheets) quedan registrados como fuentes externas.

**8. Escribir los dos documentos.**

**9. Verificar lo que se escribió, antes de entregar.** Las etapas 1 a 7 las
hacen scripts probados; la 8 la escribe el asistente, y ahí entran al documento
datos que **no estaban en el export**: porcentajes, totales, plazos,
diferencias de fechas.

- **Recalcular cada cuenta propia ejecutando código**, nunca de memoria, con el
  valor que afirma el documento al lado del real. La trampa más común es el
  porcentaje: si en la misma tabla hay una alícuota —un IVA, un recargo—, es
  fácil escribir esa cifra en lugar del aumento real.
- **Verificar que cada cita entrecomillada exista literal** en alguna fuente,
  normalizando espacios y saltos de línea.
- **Cotejar los conteos** contra el inventario: mensajes, transcripciones,
  imágenes.
- **Chequear que el resumen no haya perdido** un dato que solo vivía en una
  imagen o en un audio. Es el peor lugar donde perderlo.
- **Dejar escrito que se verificó**, incluido lo que se corrigió.

Un número inventado con cara de hallazgo es peor que una omisión: el lector no
tiene cómo detectarlo.

## Qué tiene que tener el documento

- **Inventario del export**: archivos, duplicados, adjuntos ausentes
- **Participantes** y el rol que se infiere de cada uno
- **Línea de tiempo completa**: cada mensaje con hora y emisor, cada audio
  transcripto en su posición cronológica, cada adjunto señalado donde se envió
- **Anexos** con el texto íntegro de cada documento
- **Síntesis**, datos duros en tablas, puntos abiertos e inconsistencias
- **Nota metodológica**: con qué se transcribió y qué quedó fuera
- **Recuento de cobertura**, que es la prueba de que se leyó todo:

```
- Mensajes de texto leídos: 412 / 412
- Audios transcriptos: 23 / 23 (41:17)
- Videos procesados: 4 / 4
- Documentos leídos: 11 / 11
- Imágenes analizadas: 68 / 68
- Adjuntos mencionados pero ausentes del export: 3
```

## Cómo escribir

**No inventar.** Si la transcripción quedó dudosa, marcarlo. Si un nombre propio
o una sigla salieron mal, corregir con criterio y **dejar constancia de la
corrección**, en vez de presentar la conjetura como dato.

**No resumir de más.** El documento es una memoria, no un resumen ejecutivo. Si
alguien mandó un audio de ocho minutos con seis definiciones, van las seis.

**Separar el dato de la interpretación.** Lo que se dijo va en la línea de
tiempo. Lo que vos deducís va en la síntesis, marcado como inferencia.

**Fechar todo.** Cada afirmación tiene que poder rastrearse a un mensaje con
fecha y emisor.

---

## Si se vuelve a exportar el mismo grupo

Es el caso normal: el grupo sigue hablando y se exporta de nuevo a la semana.
**No hay que retranscribir lo ya hecho.**

Descomprimir el export nuevo **encima de la misma carpeta de trabajo** y volver
a correr los scripts. `transcribe.py` saltea lo que ya está en su JSON de
salida, y los nombres de archivo de WhatsApp son estables entre exports. Si en
cambio se descomprime en una carpeta nueva, no encuentra el JSON viejo y vuelve
a transcribir todo.

El inventario se rehace entero —es barato— y **los dos documentos se reescriben
de cero**: si el anterior tenía correcciones a mano, hay que volver a
aplicarlas.
