#!/usr/bin/env bash
# Gera o pacote .deb (Ubuntu/Debian) a partir de dist/JandAIa (saída do PyInstaller).
# Uso:   installer/linux/build_deb.sh [versão]
# Dica:  gere o pacote numa máquina com glibc antiga (Ubuntu 22.04) para que ele
#        funcione também em sistemas mais antigos.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
VERSAO="${1:-$(tr -d '[:space:]' < "$RAIZ/VERSION")}"
DEBVER="${VERSAO#v}"; DEBVER="${DEBVER//-/\~}"          # 1.0.0-rc1 -> 1.0.0~rc1
ARQ="$(dpkg --print-architecture)"
NOME="jandaia_${DEBVER}_${ARQ}"
SAIDA="$RAIZ/dist_installer"
PKG="$SAIDA/$NOME"
MANTENEDOR="${MAINTAINER:-Statlab Produtos Educacionais <statlab@users.noreply.github.com>}"

[ -x "$RAIZ/dist/JandAIa/JandAIa" ] || { echo "Rode antes o PyInstaller (dist/JandAIa não encontrado)."; exit 1; }

rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/jandaia" "$PKG/usr/bin" \
         "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/256x256/apps"

cp -a "$RAIZ/dist/JandAIa/." "$PKG/opt/jandaia/"
ln -s /opt/jandaia/JandAIa "$PKG/usr/bin/jandaia"
install -m 644 "$RAIZ/assets/jandaia.png" "$PKG/usr/share/icons/hicolor/256x256/apps/jandaia.png"

cat > "$PKG/usr/share/applications/jandaia.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=JandAIa
GenericName=Gerador de avaliações
Comment=Gerador de provas e gabaritos com IA
Exec=jandaia
Icon=jandaia
Terminal=false
Categories=Education;
StartupNotify=true
Actions=Configurar;

[Desktop Action Configurar]
Name=Configurar chave da Groq
Exec=jandaia --configurar
DESKTOP

TAMANHO="$(du -sk "$PKG/opt" | cut -f1)"
cat > "$PKG/DEBIAN/control" <<CONTROL
Package: jandaia
Version: $DEBVER
Section: education
Priority: optional
Architecture: $ARQ
Maintainer: $MANTENEDOR
Installed-Size: $TAMANHO
Depends: libc6 (>= 2.35), libx11-6, libxft2, libxss1, libfontconfig1
Homepage: https://github.com/ProdutosEduacionaisStatlab/JandAIa
Description: Gerador de avaliações com IA
 O JandAIa gera provas e gabaritos de qualquer disciplina com apoio de IA
 generativa. Roda no próprio computador e abre no navegador; só a geração
 das questões usa a internet (API da Groq, com a chave do próprio usuário).
 .
 Os dados do usuário ficam em ~/.local/share/JandAIa e não são removidos
 ao desinstalar o pacote.
CONTROL

find "$PKG" -type d -exec chmod 755 {} +
dpkg-deb --root-owner-group --build "$PKG" "$SAIDA/$NOME.deb" >/dev/null
rm -rf "$PKG"
echo "Gerado: $SAIDA/$NOME.deb"
