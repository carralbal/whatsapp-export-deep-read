# Qué hacer cuando algo del pipeline falla

## Transcripción

**El proceso desaparece a mitad de camino y el JSON quedó incompleto.**
Pasa cuando se lanzó con `&` o `nohup`: los procesos en segundo plano se
congelan entre llamadas de herramienta y terminan muertos. Correr en primer
plano. Si el lote es grande, partirlo: `transcribe.py` saltea lo ya transcripto
y va fusionando en el mismo JSON, así que se lo puede invocar varias veces sin
perder nada.

**La descarga del modelo devuelve 403.**
El proxy bloquea `huggingface.co` y `openaipublic.azureedge.net`. Están
permitidos `github.com`, `release-assets.githubusercontent.com` y `pypi.org`.
Por eso el único camino es sherpa-onnx + assets de GitHub Releases. Si aun así
falla, probar con el modelo `base` (más chico) o verificar el proxy con:

```bash
curl -s -D - -o /dev/null https://github.com | grep -i x-deny-reason
```

**La transcripción sale muy mala.**
Escalar de `small` a `medium`: mejora bastante con nombres propios y siglas, a
costa de unas tres veces más tiempo de cómputo. Vale la pena cuando hay pocos
audios y mucha jerga técnica. Antes de escalar, chequear que el audio no esté
saturado o con dos personas hablando encima; en ese caso ningún modelo lo va a
resolver y conviene decirlo en la nota metodológica.

**El audio está en un formato que ffmpeg no abre.**
Los `.opus` de WhatsApp a veces vienen sin contenedor válido. Probar:

```bash
ffmpeg -f ogg -i entrada.opus -ar 16000 -ac 1 salida.wav
```

## PDF

**`pdftotext` devuelve vacío o basura.**
Mirar `pdffonts`: si la tabla está vacía, el PDF es un escaneo o un raster.
Rasterizar con `pdftoppm -jpeg -r 150` y leer las páginas con visión. Si hay
muchas páginas de texto escaneado, usar OCR (`pytesseract`, hay que instalarlo).

**El PDF es un plano y el texto extraído son números sueltos sin contexto.**
Es lo esperable: en un plano CAD las cotas son objetos de texto dispersos.
Rasterizar siempre y leer visualmente. A 100 DPI un A2 queda legible; si las
cotas no se leen, subir a 150 o 200 DPI y recortar por sectores con
`pdftoppm -x -y -W -H`.

**El PDF pesa mucho y la rasterización tarda.**
Bajar el DPI o rasterizar solo las páginas que importan con `-f` y `-l`.

## Documentos de Office

**El `.xlsx` no abre con pandas.**
Puede necesitar `openpyxl` (`pip install openpyxl --break-system-packages`). Si
es un `.xls` viejo, hace falta `xlrd`. Si es un `.numbers` o un `.ods`,
convertir con `libreoffice --headless --convert-to xlsx` si está disponible.

**El documento es un link a Google Sheets / Docs.**
No se puede abrir sin autenticación. Si hay un conector de Drive en la sesión,
usarlo. Si no, registrar el link como fuente externa pendiente y listarlo en los
vacíos de información.

## Export

**El zip no tiene `_chat.txt`.**
Algunos exports usan el nombre del chat como nombre del archivo, o `chat.txt`.
`inventory.py` busca cualquier `.txt` que contenga "chat". Si tampoco aparece,
puede ser un backup de base de datos (`msgstore.db.crypt14`), que no es un
export y no se puede leer sin la clave del teléfono: avisarlo y pedir el export
correcto ("Exportar chat" desde la app).

**El export vino "sin archivos adjuntos".**
Se nota porque `_chat.txt` dice `<Multimedia omitido>` en vez de
`<adjunto: ...>`. En ese caso solo se puede procesar el texto: decirlo de frente
en el documento y sugerir volver a exportar con la opción "Incluir archivos".

**Hay cientos de adjuntos.**
Priorizar por valor de información: documentos y audios primero, después
imágenes con texto (capturas, planos, presupuestos), y al final las fotos
sociales. Las fotos repetidas o decorativas se pueden agrupar en una sola
entrada, dejando constancia de que se las miró.

## Volumen

**El chat tiene miles de mensajes.**
La línea de tiempo íntegra deja de ser útil. Cambiar a: línea de tiempo íntegra
para los últimos meses o para los hilos de decisión, y bloques resumidos con
citas textuales de los picos para el resto. Decirlo explícitamente en la nota
metodológica para que el lector sepa qué está leyendo.

---

## El inventario devuelve 0 mensajes pero sí encuentra los archivos

Es el sintoma clasico de un `_chat.txt` con caracteres invisibles que la regex
no contempla. WhatsApp mete varios:

| Caracter | Donde aparece |
|---|---|
| `U+200E` / `U+200F` | al principio de linea y antes de cada adjunto |
| `U+202F` (espacio fino) | entre la hora y el `p. m.` en locales en espanol |
| `U+00A0` (espacio duro) | ocasional, segun version |
| `\r\n` | saltos de linea de Windows en algunos exports |

Un export de iPhone en espanol se ve asi en crudo:

```
[15/5/26, 12:47:29<U+202F>p.<U+202F>m.] Nombre: texto
```

`inventory.py` normaliza todo eso en `normalizar()` antes de parsear. Si
aparece un formato nuevo, el diagnostico es mirar los bytes, no el texto:

```bash
head -c 200 _chat.txt | xxd | head -12
```

Ahi se ven los caracteres invisibles que en pantalla parecen un espacio comun.

---

## Windows

El instalador y los scripts son Python puro y estan escritos para funcionar en
Windows, pero **nadie lo verifico todavia en Windows real**. Si lo corres ahi y
algo falla, abri un issue: es informacion util.

Lo que conviene tener en cuenta:

**Usa `python`, no `python3`.** En Windows el comando suele ser `python`.

**ffmpeg tiene que estar en el PATH.** `winget install Gyan.FFmpeg` lo resuelve.
Si lo bajaste a mano, agrega su carpeta `bin` al PATH y abri una terminal nueva.

**Rutas largas.** Windows corta las rutas a 260 caracteres por defecto. Un
export de WhatsApp tiene nombres de archivo largos, y si ademas lo descomprimis
dentro de una carpeta anidada podes pasarte. Si aparecen errores de "ruta
demasiado larga", descomprimi en algo corto como `C:\wa\` o habilita rutas
largas en Windows.

**Los comandos del README que usan `mkdir -p` y `cp -r` son de macOS y Linux.**
En PowerShell el equivalente es:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills"
Copy-Item -Recurse whatsapp-export-deep-read "$HOME\.claude\skills\"
```

**`CREAR_REPO.sh` es un script de bash** y no corre en Windows sin WSL o Git
Bash. Solo hace falta para publicar el repo, no para usar el skill.
