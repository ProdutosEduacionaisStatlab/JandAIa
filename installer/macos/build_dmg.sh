#!/usr/bin/env bash
# Gera o .dmg (macOS) a partir de dist/JandAIa.app (saída do PyInstaller).
# Uso:  installer/macos/build_dmg.sh [versão]
#
# Assinatura (opcional, recomendada para distribuir): defina APPLE_SIGN_IDENTITY com o nome do
# certificado "Developer ID Application: ..." e o app é assinado com ele. Sem isso, o app recebe
# apenas uma assinatura "ad-hoc" (suficiente para rodar, mas o macOS exibirá um aviso na 1ª abertura).
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
VERSAO="${1:-$(tr -d '[:space:]' < "$RAIZ/VERSION")}"
APP="$RAIZ/dist/JandAIa.app"
SAIDA="$RAIZ/dist_installer"
ARQ="$(uname -m)"                      # arm64 (Apple Silicon) ou x86_64 (Intel)
DMG="$SAIDA/JandAIa-${VERSAO}-macOS-${ARQ}.dmg"

[ -d "$APP" ] || { echo "Rode antes o PyInstaller (dist/JandAIa.app não encontrado)."; exit 1; }
mkdir -p "$SAIDA"

PREPARO="$(mktemp -d)"
trap 'rm -rf "$PREPARO"' EXIT
cp -R "$APP" "$PREPARO/"
ln -s /Applications "$PREPARO/Applications"

if [ -n "${APPLE_SIGN_IDENTITY:-}" ]; then
  codesign --force --deep --options runtime --timestamp --sign "$APPLE_SIGN_IDENTITY" "$PREPARO/JandAIa.app"
else
  codesign --force --deep --sign - "$PREPARO/JandAIa.app"
fi

rm -f "$DMG"
hdiutil create -volname "JandAIa" -srcfolder "$PREPARO" -ov -format UDZO "$DMG"
echo "Gerado: $DMG"
