# Instrucciones para cualquier asistente

Este archivo es el mismo método que el `SKILL.md`, pero escrito para pegarse
como instrucción en un asistente que **no** carga skills de Claude: ChatGPT,
Gemini, Copilot, o el que uses.

**Cómo usarlo:** pegá todo lo que está debajo de la línea en las instrucciones
de tu proyecto o en el primer mensaje de la conversación, y después pasale la
carpeta del export.

**Requisito:** el asistente tiene que poder ejecutar los scripts en tu máquina
y leer los archivos de una carpeta. Si tu asistente solo lee archivos que le
subís uno por uno, corré los scripts vos a mano (ver `README.md`) y pasale el
`.md` resultante.

---

## Objetivo

Leer un export de WhatsApp al 100% y producir **un solo archivo Markdown** que
sirva como memoria permanente de esa conversación.

La regla que ordena todo: **ningún byte del export queda sin leer.** La mayor
parte de lo que se habló no está en el texto del chat, está en las notas de voz
que nadie volvió a escuchar y en los adjuntos. Un resumen que solo lee
`_chat.txt` es un resumen que perdió lo importante.

## Orden de trabajo

Cada etapa alimenta a la siguiente. No saltear ninguna.

**1. Inventariar.** Correr `python scripts/inventory.py <ruta al .zip o a la
carpeta>`. Devuelve cantidad de mensajes, formato del export (iPhone o Android),
participantes, archivos por tipo, duración total de audio y video, duplicados
por MD5, huecos de conversación y —importante— los adjuntos que alguien mencionó
pero que no están en el export. Ese inventario es la lista de tareas.

**2. Leer el chat entero.** `_chat.txt` completo, no un muestreo. Registrar
quién habla, cuándo, y qué se decide.

**3. Transcribir todos los audios.** `python scripts/transcribe.py <carpeta>
--glob "*.opus"`. Siempre en primer plano, nunca en segundo plano: si el proceso
queda colgado hay que verlo. Transcribir el 100%, no una muestra.

**4. Procesar los videos.** El audio del video va por el mismo camino de
transcripción. Además, extraer fotogramas (uno cada 3 segundos más el primero)
y mirarlos.

**5. Leer los documentos.** PDF, Word, Excel, CSV, presentaciones: el texto
íntegro, no el resumen. Si un PDF es escaneado, convertirlo a imágenes y leerlo
visualmente.

**6. Analizar las imágenes una por una.** Describir qué se ve y qué aporta a la
conversación. Las capturas de pantalla suelen contener información que no está
en ninguna otra parte.

**7. Relevar los links.** Los que se puedan abrir, abrirlos. Los que requieran
autenticación (Drive, Docs, Sheets) quedan registrados como fuentes externas.

**8. Escribir el documento.**

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
