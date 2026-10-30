"""Gera assets/jandaia.png, .ico e .icns a partir de uma imagem (para trocar o ícone provisório).

Uso:  python installer/gerar_icones.py caminho/do/logo.png
O logo deve ser quadrado, de preferência com 1024x1024 pixels e fundo transparente.
Requer:  pip install pillow
"""
import sys
from pathlib import Path

from PIL import Image

if len(sys.argv) != 2:
    raise SystemExit(__doc__)

origem = Image.open(sys.argv[1]).convert("RGBA")
if origem.width != origem.height:
    raise SystemExit("A imagem precisa ser quadrada.")

destino = Path(__file__).resolve().parent.parent / "assets"
destino.mkdir(exist_ok=True)
origem.resize((256, 256), Image.LANCZOS).save(destino / "jandaia.png")
origem.save(destino / "jandaia.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
origem.resize((1024, 1024), Image.LANCZOS).save(destino / "jandaia.icns")
print("Ícones atualizados em", destino)
