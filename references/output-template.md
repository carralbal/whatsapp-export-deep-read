# Plantillas de los documentos de salida

**Son dos archivos, no uno.** Esto no es un detalle de formato: es la diferencia
entre entregar la materia prima y entregar el entendimiento.

| Archivo | Qué es | Extensión |
|---|---|---|
| `<nombre> — resumen.md` | Lo que la persona quería saber | Dos páginas |
| `<nombre> — completo.md` | Todo el respaldo, mensaje por mensaje | Sin techo |

**Por qué dos.** Un usuario real lo pidió con estas palabras: *"que hagas las dos
cosas, uno por separado con toda la info y uno más resumido"*. Había recibido un
documento largo, esperaba un resumen ejecutivo, y no encontró el valor aunque
estuviera adentro. Quien abre esto quiere **entender la conversación**; un
archivo de seiscientas líneas entrega la materia prima de entender, no el
entender. El largo sigue existiendo porque es la prueba de que se leyó el 100% y
porque es donde se va a buscar el detalle cuando haga falta — pero el entregable
es el corto.

Entregar los dos y decir en una línea cuál abrir primero.

---

# 1. El resumen — `<nombre> — resumen.md`

Dos páginas. Si no entra en dos páginas, está mal hecho: lo que sobra va al
completo.

```markdown
# <Nombre del chat> — Resumen

> Del export de WhatsApp de **"<nombre exacto>"**, DD/MM/AAAA → DD/MM/AAAA.
> El detalle completo está en `<nombre> — completo.md`.

## Cobertura
Las seis líneas del recuento, tal cual aparecen abajo. Van primero también acá:
si falta algo, la persona tiene que saberlo antes de leer una conclusión.

## Lo que pasó
Cinco a diez viñetas. Lo que un recién llegado necesita para poder opinar.
No "se habló de presupuesto": **cuál** es el número, **quién** lo dijo, **cuándo**,
y si quedó cerrado o abierto. Fecha entre paréntesis en cada punto.

## Decisiones tomadas
Tabla: Qué se decidió | Quién | Cuándo | Objeciones

## Pendientes
Tabla: Qué falta | Quién lo tiene | Desde cuándo | Estado
Si nadie quedó a cargo de algo, decirlo: eso es un hallazgo, no un hueco.

## Datos duros
Tabla con los números, montos, fechas, medidas y nombres propios que importan.

## Puntos abiertos
Lo que no se decidió, lo que quedó contradictorio, lo que nadie contestó.

## Dónde está el detalle
Una línea: qué hay en el completo y cómo buscarlo.
```

---

# 2. El completo — `<nombre> — completo.md`

Copiar esta estructura y llenarla. Las secciones marcadas como obligatorias van
siempre, aunque queden cortas. Las que dicen "según corresponda" se agregan solo
si el export tiene ese tipo de material.

```markdown
# <Nombre del chat o proyecto> — Base de conocimiento completa

> Documento generado a partir del export de WhatsApp de **"<nombre exacto del chat>"**.
> Cubre el 100% del contenido: mensajes de texto, transcripción de los N audios,
> N videos, texto íntegro de los PDF y planillas, y análisis de las N imágenes.
> Fecha del export: DD/MM/AAAA HH:MM. Ventana cubierta: **DD/MM/AAAA → DD/MM/AAAA**.

## 0. Cobertura                    [obligatoria — va primero, siempre]

El recuento, antes que nada. Quien abre el documento tiene que saber en dos
segundos qué se leyó y qué no, sin buscarlo:

    - Mensajes de texto leídos: X / X
    - Audios transcriptos: X / X (MM:SS)
    - Videos procesados: X / X
    - Documentos leídos: X / X
    - Imágenes analizadas: X / X
    - Adjuntos mencionados pero ausentes del export: X

Si alguna línea no está completa, decir en una frase por qué. Si los audios
quedaron en cero habiendo audios, **eso va arriba de todo y en negrita**: el
documento está incompleto y quien lo lea tiene que enterarse antes de leerlo,
no después.

## 1. Lo que hay que saber           [obligatoria — la síntesis, arriba]

El mismo contenido del resumen, repetido acá. La repetición es a propósito: los
dos archivos circulan por separado y cada uno tiene que servir solo.

Si lo primero que encuentra quien abre esto es el chat día por día, cierra el
archivo antes de llegar a lo que vale.

## 2. Índice
<lista de secciones>

## 3. Inventario del export        [obligatoria]
Tabla: # | Archivo | Tipo y peso/duración/páginas | Fecha | Emisor | Contenido en una línea
Debajo: duplicados detectados por MD5, y adjuntos mencionados en el chat que no
vinieron en el export.

## 4. Participantes                [obligatoria]
Tabla: Nombre en el chat | Rol inferido | Notas
Incluir también a los terceros que se mencionan y no están en el grupo
(contadores, proveedores, familiares, clientes), porque aparecen en las
decisiones aunque no escriban.

## 5. Línea de tiempo completa     [obligatoria — el respaldo, mensaje por mensaje]
Subtítulo por día o por bloque temático, con una etiqueta de qué pasó ese día.
Dentro de cada bloque, cada mensaje con su hora exacta y su emisor:

    **HH:MM:SS — Nombre:** "texto literal del mensaje"

Los mensajes largos o documentos pegados van como bloque de cita, respetando
tablas y numeración.

Los audios van en su posición cronológica:

    **HH:MM:SS — 🎙️ Nombre (audio, NN,N s) — transcripción:**
    > "texto transcripto"
    >
    > *(nota sobre correcciones de la transcripción, si hizo falta)*

Los adjuntos van señalados donde se enviaron, con un puntero al anexo:

    **HH:MM:SS — 📄 Nombre** envía `archivo.pdf` (ver Anexo A)

Marcar los silencios largos con un aviso visible:

    > ⚠️ **Hueco de NN días en la conversación (DD/MM → DD/MM).**
    > En ese período hubo al menos una reunión que no está documentada acá.

Señalar los mensajes editados y mostrar ambas versiones cuando la diferencia
importa (listas de pendientes, montos, fechas).

## 6..N. Anexos                    [según corresponda]

### Anexo A — <nombre del documento> (texto íntegro)
Transcripción completa del PDF o documento, respetando tablas, numeración y
erratas del original, marcadas con *(sic)*. Encabezado con metadatos: quién lo
generó, con qué herramienta, cuándo.

### Anexo B — Planos / archivos técnicos
Tabla con los datos del rótulo (obra, estudio, escala, formato, revisiones,
leyenda legal). Después, una entrada por página describiendo qué muestra, con
todas las cotas y rótulos legibles. Si hay varias versiones del mismo plano,
cerrar con una **tabla de diferencias** y una lectura de qué implica elegir cada
una.

### Anexo C — Imágenes
Una entrada por imagen: nombre de archivo, emisor, fecha, descripción detallada,
todo dato legible extraído, y qué función cumple en la conversación. Cerrar con
una observación transversal si las imágenes comparten un patrón.

### Anexo D — Normativa, especificaciones o fuentes citadas
Texto íntegro de lo que se haya pegado en el chat o extraído de links, más una
tabla de todas las normas, estándares o fuentes mencionadas con dónde aparecen
y qué exigen.

### Anexo E — Videos
Por cada video: duración, transcripción del audio, y descripción de lo que se ve
a lo largo del metraje.

## N+1. Síntesis extendida                     [obligatoria]
Lo de la sección 1 pero desarrollado, ahora que el lector ya recorrió la
evidencia. No repetir las viñetas: desarrollarlas.

Subsecciones típicas:
- Qué es el proyecto / de qué trata la conversación
- Los ejes en juego
- Estado real de cada eje, con las tensiones que nadie escribió
- Lo que se sabe hoy sobre el tema central

Acá sí se interpreta, se conecta y se deduce. Marcar explícitamente lo deducido:
"implicancia aritmética no discutida en el chat: …".

## N+2. Datos duros en un solo lugar           [obligatoria si hay números]
Todas las tablas de cifras, medidas, superficies, precios, plazos y estados,
reunidas para no tener que buscarlas en la línea de tiempo. Es la versión
completa de lo que la sección 1 resume.
Incluir una tabla de pendientes con # | Pendiente | Responsable | Estado.

## N+3. Puntos abiertos, inconsistencias y riesgos detectados   [obligatoria]
Cuatro bloques:
1. Inconsistencias internas de los documentos (errores de rótulo, números que no
   cierran, versiones desactualizadas)
2. Riesgos técnicos, legales o de ejecución
3. Vacíos de información (qué falta, qué no se decidió, qué no se adjuntó)
4. Qué está sólido

Si el bloque 4 queda vacío, probablemente falta leer algo.

## N+4. Nota metodológica                      [obligatoria]
Con qué se transcribieron los audios y qué correcciones se aplicaron; cómo se
leyeron los PDF (texto o rasterizado); qué imágenes se inspeccionaron; qué quedó
fuera de alcance y por qué.

Listar las correcciones recurrentes. Errores tipicos del motor de transcripcion,
verificados contra audio real en español rioplatense:

| El motor escribe | Casi siempre es |
|---|---|
| idea | **IA** |
| Mercules, Mercoles | miercoles |
| nombres propios deformados | revisarlos uno por uno contra el chat |
| siglas del rubro | reconstruirlas desde el contexto |

El caso de **IA -> idea** es el mas frecuente en conversaciones sobre
tecnologia, y el mas facil de pasar por alto porque la frase sigue teniendo
sentido gramatical. Revisarlo siempre.
```

---

## Ejemplo de entrada de línea de tiempo bien hecha

```markdown
### 08/06/2026 — El número concreto: USD 40.000

**13:21:00 — 🎙️ Pachu (audio, 84,3 s) — transcripción:**
> "Hola chicos, ¿cómo andan? (…) lo estuvimos viendo con Diego y pudimos resolver
> **que vamos a poder aportar hasta 40.000 dólares**. Lo que estoy trabajando es
> en que **esos 40.000 dólares representen el 30%** (…)"
>
> *(transcripción automática; "ANMAT" figura como "ANTMAT" y la frase final llegó
> distorsionada, el sentido es que el trámite de importación puede valer la pena.)*

*Este audio es el origen del criterio central del proyecto.*
```

Lo que hace buena a esa entrada: hora exacta, emisor, duración, texto
transcripto con lo relevante en negrita, nota honesta sobre los límites de la
transcripción, y una línea que explica por qué ese mensaje importa.
