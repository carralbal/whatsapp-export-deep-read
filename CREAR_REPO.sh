#!/usr/bin/env bash
# Crea el repo publico y sube SOLO los archivos de este skill.
#
# Requiere: gh (GitHub CLI) autenticado -> https://cli.github.com
#
# Este script se niega a correr si la carpeta tiene algo que no sea del skill.
# Es a proposito: un `git add -A` en la carpeta equivocada sube a un repo
# PUBLICO todo lo que haya alrededor.

set -euo pipefail

ESPERADOS=(
  SKILL.md README.md INSTRUCCIONES.md LICENSE CREAR_REPO.sh .gitignore
  scripts/inventory.py scripts/transcribe.py scripts/setup_asr.py
  references/output-template.md references/troubleshooting.md
)

echo "==> Carpeta: $(pwd)"
echo

# ---------- 1. estan todos los archivos del skill? ----------
faltan=()
for f in "${ESPERADOS[@]}"; do
  [ -e "$f" ] || faltan+=("$f")
done
if [ ${#faltan[@]} -gt 0 ]; then
  echo "ERROR: esta no parece la carpeta del skill. Faltan:" >&2
  printf '  - %s\n' "${faltan[@]}" >&2
  echo >&2
  echo "Descomprimi el zip en una carpeta vacia y corre este script desde adentro." >&2
  exit 1
fi

# ---------- 2. hay algo que NO sea del skill? ----------
sobran=()
while IFS= read -r f; do
  f="${f#./}"
  case "$f" in
    .git/*|*/__pycache__/*|*.pyc|.DS_Store|*/.DS_Store) continue ;;
  esac
  esta=0
  for e in "${ESPERADOS[@]}"; do [ "$f" = "$e" ] && { esta=1; break; }; done
  [ $esta -eq 0 ] && sobran+=("$f")
done < <(find . -type f)

if [ ${#sobran[@]} -gt 0 ]; then
  echo "ERROR: hay archivos que NO son del skill y se subirian a un repo PUBLICO:" >&2
  printf '  - %s\n' "${sobran[@]}" >&2
  echo >&2
  echo "Corre esto en una carpeta limpia:" >&2
  echo "  mkdir -p ~/kg-repo && cd ~/kg-repo" >&2
  echo "  unzip -o ~/Downloads/whatsapp-export-deep-read.zip" >&2
  echo "  cd whatsapp-export-deep-read && bash CREAR_REPO.sh" >&2
  exit 1
fi

# ---------- 3. mostrar y confirmar ----------
echo "Se van a subir estos ${#ESPERADOS[@]} archivos, y nada mas:"
printf '  %s\n' "${ESPERADOS[@]}"
echo
echo "El repo va a quedar PUBLICO en tu cuenta de GitHub."
read -r -p "Escribi SI para continuar: " ok
[ "$ok" = "SI" ] || { echo "Cancelado."; exit 1; }

# ---------- 4. crear y subir ----------
git init -q 2>/dev/null || true
git add -- "${ESPERADOS[@]}"

echo
echo "==> Esto es lo que git va a commitear:"
git status --short
echo

git commit -qm "whatsapp-export-deep-read: primera version publica" || true
git branch -M main
gh repo create whatsapp-export-deep-read --public --source=. --push \
  --description "Lee un export de WhatsApp completo: transcribe los audios, mira los videos, lee los PDF y las imagenes, y lo deja todo en un solo archivo."

echo
echo "Listo: https://github.com/$(gh api user -q .login)/whatsapp-export-deep-read"
