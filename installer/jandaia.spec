# -*- mode: python ; coding: utf-8 -*-
# Receita do PyInstaller para o JandAIa. Uso (na raiz do projeto):
#   python manage.py collectstatic --noinput
#   pyinstaller installer/jandaia.spec --noconfirm --clean
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

RAIZ = Path(SPECPATH).parent
VERSAO = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
EH_WIN = sys.platform == "win32"
EH_MAC = sys.platform == "darwin"

if not (RAIZ / "staticfiles").exists():
    raise SystemExit("Pasta 'staticfiles' não encontrada. Rode antes: python manage.py collectstatic --noinput")

datas = [
    (str(RAIZ / "gerador" / "templates"), "gerador/templates"),
    (str(RAIZ / "staticfiles"), "staticfiles"),
    (str(RAIZ / "VERSION"), "."),
    (str(RAIZ / "assets" / "jandaia.png"), "assets"),
]
# Cursos, tópicos e questões que acompanham o programa (opcional).
# Gere com: python manage.py dumpdata gerador --indent 2 --output dados_iniciais.json
if (RAIZ / "dados_iniciais.json").exists():
    datas.append((str(RAIZ / "dados_iniciais.json"), "."))

binaries = []
hiddenimports = (
    collect_submodules("gerador")
    + collect_submodules("jandaia")
    + collect_submodules("whitenoise")   # citado só por texto em MIDDLEWARE
    + ["waitress", "dotenv", "PyPDF2", "certifi"]
)

# Pacotes com templates/estáticos/traduções que a análise automática não enxerga.
for pacote in ("import_export",):
    d, b, h = collect_all(pacote)
    datas += d
    binaries += b
    hiddenimports += h
for pacote in ("django", "certifi", "tzdata"):
    datas += collect_data_files(pacote)

a = Analysis(
    [str(RAIZ / "launcher.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "IPython", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)

# Nunca levar bancos de dados para o pacote (o do usuário fica em %LOCALAPPDATA%\JandAIa).
a.datas = [d for d in a.datas
           if not str(d[0]).lower().endswith((".sqlite3", ".sqlite", ".db"))
           and not str(d[1]).lower().endswith((".sqlite3", ".sqlite", ".db"))]

pyz = PYZ(a.pure)

versao_exe = None
if EH_WIN:
    # Propriedades do .exe (aba "Detalhes"). Se algo falhar aqui, o build continua sem elas.
    try:
        from PyInstaller.utils.win32.versioninfo import (
            FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
        )
        numeros = (VERSAO.split("-")[0].split(".") + ["0", "0", "0", "0"])[:4]
        tupla = tuple(int(n) if n.isdigit() else 0 for n in numeros)
        versao_exe = VSVersionInfo(
            ffi=FixedFileInfo(filevers=tupla, prodvers=tupla, mask=0x3F, flags=0x0,
                              OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
            kids=[
                StringFileInfo([StringTable("041604B0", [
                    StringStruct("CompanyName", "Statlab - Produtos Educacionais"),
                    StringStruct("FileDescription", "JandAIa - Gerador de Avaliações com IA"),
                    StringStruct("FileVersion", VERSAO),
                    StringStruct("InternalName", "JandAIa"),
                    StringStruct("OriginalFilename", "JandAIa.exe"),
                    StringStruct("ProductName", "JandAIa"),
                    StringStruct("ProductVersion", VERSAO),
                ])]),
                VarFileInfo([VarStruct("Translation", [0x0416, 1200])]),
            ],
        )
    except Exception as erro:
        print(f"AVISO: não foi possível gerar as propriedades do .exe: {erro}")

icone = None
if EH_WIN:
    icone = str(RAIZ / "assets" / "jandaia.ico")
elif EH_MAC:
    icone = str(RAIZ / "assets" / "jandaia.icns")

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JandAIa",
    console=False,      # programa com janela; mensagens vão para o arquivo de log
    icon=icone,
    version=versao_exe,
    upx=False,          # UPX costuma disparar falsos positivos de antivírus
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="JandAIa")

if EH_MAC:
    app = BUNDLE(
        coll,
        name="JandAIa.app",
        icon=str(RAIZ / "assets" / "jandaia.icns"),
        bundle_identifier="br.edu.statlab.jandaia",
        version=VERSAO,
        info_plist={"CFBundleDisplayName": "JandAIa", "NSHighResolutionCapable": True},
    )
