"""
JandAIa - ponto de entrada do programa instalado.

Faz o papel do "python manage.py runserver" do desenvolvimento, mas pensado para
o usuário final:

  * guarda banco, configurações e log na pasta de dados do usuário;
  * pede a chave da Groq (e a senha do administrador) na primeira execução;
  * cria/atualiza o banco, sobe o servidor local e abre o navegador;
  * mostra uma pequena janela para reabrir o navegador ou encerrar o programa.

Opções de linha de comando:
  --configurar      reabre a janela de configuração da chave da Groq
  --headless        sem janela (testes/servidor): lê GROQ_API_KEY e
                    JANDAIA_ADMIN_PASSWORD do ambiente
  --sem-navegador   não abre o navegador
  --porta N         porta preferida (padrão 8765)
  --autoteste [ARQ] verifica se o pacote está íntegro e sai (usado no CI)
"""
import argparse
import json
import os
import secrets
import socket
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

APP = "JandAIa"
PORTA_PADRAO = 8765
USUARIO_ADMIN = "admin"
URL_GROQ = "https://console.groq.com/keys"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def recurso(*partes):
    """Caminho de um arquivo empacotado (ou da pasta do projeto, em desenvolvimento)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*partes)


def versao():
    try:
        return recurso("VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"


def pasta_dados():
    """Pasta onde ficam banco, configuração e log (nunca a pasta do programa)."""
    sobreposta = os.environ.get("JANDAIA_DATA_DIR")
    if sobreposta:
        pasta = Path(sobreposta)
    elif sys.platform == "win32":
        pasta = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP
    elif sys.platform == "darwin":
        pasta = Path.home() / "Library" / "Application Support" / APP
    else:
        pasta = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def carregar_config(dados):
    arquivo = dados / "config.json"
    try:
        cfg = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    if not cfg.get("secret_key"):
        cfg["secret_key"] = secrets.token_urlsafe(50)
        salvar_config(dados, cfg)
    return cfg


def salvar_config(dados, cfg):
    arquivo = dados / "config.json"
    temporario = arquivo.with_suffix(".tmp")
    temporario.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(temporario, 0o600)  # só o usuário lê (no Windows é ignorado)
    except OSError:
        pass
    os.replace(temporario, arquivo)


def preparar_log(dados, manter_console):
    """Programa sem console (Windows/Mac): envia mensagens para o arquivo de log."""
    arquivo = dados / "jandaia.log"
    try:
        if arquivo.exists() and arquivo.stat().st_size > 2_000_000:
            arquivo.replace(dados / "jandaia.log.1")
        log = open(arquivo, "a", encoding="utf-8", buffering=1)
    except OSError:
        return
    if sys.stdout is None or sys.stderr is None or (getattr(sys, "frozen", False) and not manter_console):
        sys.stdout = sys.stderr = log


def mensagem(titulo, texto, erro=False):
    """Caixa de diálogo simples; sem interface gráfica, cai para o terminal."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        existente = tk._default_root
        raiz = existente or tk.Tk()
        if not existente:
            raiz.withdraw()
        (messagebox.showerror if erro else messagebox.showinfo)(titulo, texto, parent=raiz)
        if not existente:
            raiz.destroy()
    except Exception:
        print(f"{titulo}: {texto}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Janelas (tkinter)
# ---------------------------------------------------------------------------
def _icone(raiz):
    try:
        import tkinter as tk
        raiz._icone = tk.PhotoImage(file=str(recurso("assets", "jandaia.png")))
        raiz.iconphoto(True, raiz._icone)
    except Exception:
        pass


def _centralizar(raiz):
    raiz.update_idletasks()
    x = (raiz.winfo_screenwidth() - raiz.winfo_width()) // 2
    y = (raiz.winfo_screenheight() - raiz.winfo_height()) // 3
    raiz.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    raiz.lift()
    raiz.attributes("-topmost", True)
    raiz.after(300, lambda: raiz.attributes("-topmost", False))


def janela_configuracao(chave_atual="", pedir_senha=False):
    """Pede a chave da Groq (e, na primeira vez, a senha do administrador).

    Retorna (chave, senha_ou_None) ou None se o usuário cancelar.
    """
    import tkinter as tk
    from tkinter import messagebox, ttk

    resultado = {}
    existente = tk._default_root
    raiz = tk.Toplevel(existente) if existente else tk.Tk()
    raiz.title(f"{APP} - Configuração")
    raiz.resizable(False, False)
    _icone(raiz)

    quadro = ttk.Frame(raiz, padding=18)
    quadro.grid()

    linha = 0
    if pedir_senha:
        ttk.Label(quadro, text=f"Bem-vindo ao {APP}!", font=("TkDefaultFont", 13, "bold")).grid(
            row=linha, column=0, columnspan=2, sticky="w")
        linha += 1
        ttk.Label(quadro, text="Falta só configurar duas coisas para começar.").grid(
            row=linha, column=0, columnspan=2, sticky="w", pady=(0, 10))
        linha += 1

    ttk.Label(quadro, text="Chave de API da Groq", font=("TkDefaultFont", 10, "bold")).grid(
        row=linha, column=0, columnspan=2, sticky="w")
    linha += 1
    ttk.Label(quadro, justify="left",
              text="É gratuita: entre em console.groq.com, vá em API Keys e clique em\n"
                   "Create API Key. Copie a chave (começa com gsk_) e cole abaixo.").grid(
        row=linha, column=0, columnspan=2, sticky="w")
    linha += 1
    var_chave = tk.StringVar(value=chave_atual)
    campo_chave = ttk.Entry(quadro, textvariable=var_chave, width=54, show="•")
    campo_chave.grid(row=linha, column=0, columnspan=2, sticky="we", pady=(6, 2))
    linha += 1
    var_mostrar = tk.BooleanVar(value=False)
    ttk.Checkbutton(quadro, text="Mostrar chave", variable=var_mostrar,
                    command=lambda: campo_chave.config(show="" if var_mostrar.get() else "•")).grid(
        row=linha, column=0, sticky="w")
    ttk.Button(quadro, text="Abrir console.groq.com", command=lambda: webbrowser.open(URL_GROQ)).grid(
        row=linha, column=1, sticky="e")
    linha += 1

    var_senha = tk.StringVar()
    var_senha2 = tk.StringVar()
    if pedir_senha:
        ttk.Label(quadro, text=f"Senha do administrador (usuário: {USUARIO_ADMIN})",
                  font=("TkDefaultFont", 10, "bold")).grid(
            row=linha, column=0, columnspan=2, sticky="w", pady=(14, 0))
        linha += 1
        ttk.Label(quadro, text="Serve para cadastrar cursos, tópicos e questões. Mínimo de 8 caracteres.").grid(
            row=linha, column=0, columnspan=2, sticky="w")
        linha += 1
        ttk.Entry(quadro, textvariable=var_senha, width=30, show="•").grid(
            row=linha, column=0, sticky="w", pady=(6, 2))
        ttk.Label(quadro, text="senha").grid(row=linha, column=1, sticky="w")
        linha += 1
        ttk.Entry(quadro, textvariable=var_senha2, width=30, show="•").grid(
            row=linha, column=0, sticky="w", pady=2)
        ttk.Label(quadro, text="repita a senha").grid(row=linha, column=1, sticky="w")
        linha += 1

    def salvar(_evento=None):
        chave = var_chave.get().strip()
        if not chave:
            messagebox.showwarning(APP, "Cole a chave da Groq para continuar.", parent=raiz)
            return
        if not chave.startswith("gsk_") and not messagebox.askyesno(
                APP, "A chave não começa com \"gsk_\". Usar mesmo assim?", parent=raiz):
            return
        senha = None
        if pedir_senha:
            senha = var_senha.get()
            if len(senha) < 8:
                messagebox.showwarning(APP, "A senha precisa ter pelo menos 8 caracteres.", parent=raiz)
                return
            if senha != var_senha2.get():
                messagebox.showwarning(APP, "As senhas não são iguais.", parent=raiz)
                return
        resultado["valor"] = (chave, senha)
        raiz.destroy()

    botoes = ttk.Frame(quadro)
    botoes.grid(row=linha, column=0, columnspan=2, sticky="e", pady=(16, 0))
    ttk.Button(botoes, text="Cancelar", command=raiz.destroy).grid(row=0, column=0, padx=6)
    ttk.Button(botoes, text="Salvar e continuar", command=salvar).grid(row=0, column=1)
    raiz.bind("<Return>", salvar)

    campo_chave.focus_set()
    _centralizar(raiz)
    if existente:
        raiz.transient(existente)
        raiz.grab_set()
        raiz.wait_window(raiz)
    else:
        raiz.mainloop()
    return resultado.get("valor")


def janela_principal(estado, aoconfigurar):
    """Janela pequena que fica aberta enquanto o programa roda."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    raiz = tk.Tk()
    raiz.title(APP)
    raiz.resizable(False, False)
    _icone(raiz)

    quadro = ttk.Frame(raiz, padding=18)
    quadro.grid()
    ttk.Label(quadro, text=f"{APP} {versao()}", font=("TkDefaultFont", 14, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w")
    var_status = tk.StringVar(value="Iniciando... aguarde alguns segundos.")
    ttk.Label(quadro, textvariable=var_status).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 2))
    ttk.Label(quadro, foreground="gray",
              text="Feche esta janela para encerrar o programa.").grid(
        row=2, column=0, columnspan=3, sticky="w", pady=(0, 12))

    def abrir():
        if estado.get("url"):
            webbrowser.open(estado["url"])

    botao_abrir = ttk.Button(quadro, text="Abrir no navegador", command=abrir, state="disabled")
    botao_abrir.grid(row=3, column=0, padx=(0, 6))
    ttk.Button(quadro, text="Configurar chave da Groq", command=aoconfigurar).grid(row=3, column=1, padx=6)
    ttk.Button(quadro, text="Encerrar", command=raiz.destroy).grid(row=3, column=2, padx=(6, 0))

    aberto = {"navegador": False}

    def acompanhar():
        if estado.get("erro"):
            messagebox.showerror(APP, estado["erro"], parent=raiz)
            raiz.destroy()
            return
        if estado.get("url"):
            var_status.set(f"Em execução em {estado['url']}")
            botao_abrir.config(state="normal")
            if not aberto["navegador"] and not estado.get("sem_navegador"):
                aberto["navegador"] = True
                abrir()
        raiz.after(300, acompanhar)

    raiz.protocol("WM_DELETE_WINDOW", raiz.destroy)
    _centralizar(raiz)
    raiz.after(300, acompanhar)
    raiz.mainloop()


# ---------------------------------------------------------------------------
# Django + servidor
# ---------------------------------------------------------------------------
def configurar_ambiente(dados, cfg):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jandaia.settings")
    os.environ["JANDAIA_DATA_DIR"] = str(dados)
    os.environ["JANDAIA_DEBUG"] = "False"
    os.environ["GROQ_API_KEY"] = cfg["groq_api_key"]
    os.environ["SECRET_KEY"] = cfg["secret_key"]


def preparar_banco(primeira_vez, senha_admin):
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

    if primeira_vez:
        inicial = recurso("dados_iniciais.json")
        if inicial.exists():
            call_command("loaddata", str(inicial), verbosity=0)

    from django.contrib.auth import get_user_model
    usuarios = get_user_model()
    if senha_admin and not usuarios.objects.filter(is_superuser=True).exists():
        usuarios.objects.create_superuser(USUARIO_ADMIN, "", senha_admin)


def porta_livre(preferida):
    for candidata in (preferida, 0):
        sonda = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sonda.bind(("127.0.0.1", candidata))
            return sonda.getsockname()[1]
        except OSError:
            continue
        finally:
            sonda.close()
    raise RuntimeError("Não foi possível reservar uma porta local.")


def esperar_servidor(porta, limite=30):
    fim = time.time() + limite
    while time.time() < fim:
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def instancia_ativa(dados):
    """Se já existe um JandAIa rodando, devolve a porta dele."""
    try:
        porta = json.loads((dados / "instancia.json").read_text(encoding="utf-8"))["porta"]
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/", timeout=2) as resp:
            if resp.status == 200 and b"JandAIa" in resp.read():
                return porta
    except Exception:
        pass
    return None


def iniciar_servidor(dados, porta_preferida, primeira_vez, senha_admin, estado):
    """Roda em segundo plano: prepara o banco, sobe o servidor e avisa a janela."""
    try:
        preparar_banco(primeira_vez, senha_admin)
        from waitress import create_server
        from jandaia.wsgi import application

        porta = porta_livre(porta_preferida)
        servidor = create_server(application, host="127.0.0.1", port=porta,
                                 threads=4, channel_timeout=300)
        threading.Thread(target=servidor.run, daemon=True).start()
        if not esperar_servidor(porta):
            raise RuntimeError("O servidor local não respondeu a tempo.")
        (dados / "instancia.json").write_text(json.dumps({"porta": porta}), encoding="utf-8")
        estado["url"] = f"http://127.0.0.1:{porta}/"
    except Exception as erro:
        traceback.print_exc()
        estado["erro"] = (f"Não foi possível iniciar o {APP}.\n\n{erro}\n\n"
                          f"Detalhes no arquivo:\n{dados / 'jandaia.log'}")


# ---------------------------------------------------------------------------
# Autoteste (usado no CI para validar o pacote antes de publicar)
# ---------------------------------------------------------------------------
def autoteste(arquivo_saida=None):
    linhas = []
    falhou = []

    def registrar(texto):
        linhas.append(texto)
        print(texto)

    def verificar(nome, funcao):
        try:
            funcao()
            registrar(f"[ok]     {nome}")
        except Exception as erro:
            falhou.append(nome)
            registrar(f"[FALHA]  {nome}: {erro!r}")
    def sem_banco_no_pacote():
        if not getattr(sys, "frozen", False):
            return
        achados = [str(p) for p in recurso().rglob("*.sqlite3")]
        assert not achados, f"banco de dados dentro do pacote: {achados}"

    verificar("pacote sem banco de desenvolvimento", sem_banco_no_pacote)

    registrar(f"{APP} {versao()} - autoteste ({sys.platform})")
    temporaria = tempfile.mkdtemp(prefix="jandaia-teste-")
    configurar_ambiente(Path(temporaria), {"groq_api_key": "chave-de-teste", "secret_key": "teste"})

    def importar_bibliotecas():
        import PyPDF2, dotenv, import_export, openai, waitress, whitenoise  # noqa: F401
        # Monta o cliente da Groq: carrega a pilha HTTP/TLS e os certificados empacotados.
        openai.OpenAI(api_key="chave-de-teste", base_url="https://api.groq.com/openai/v1")

    def interface_grafica():
        import tkinter  # noqa: F401

    verificar("bibliotecas empacotadas", importar_bibliotecas)
    verificar("tkinter (janelas)", interface_grafica)
    verificar("banco de dados (migrate)", lambda: preparar_banco(False, "senha-de-teste-123"))

    if "banco de dados (migrate)" not in falhou:
        from django.test import Client
        cliente = Client()

        def pagina(url, esperado=200, contem=None):
            resp = cliente.get(url)
            assert resp.status_code == esperado, f"HTTP {resp.status_code} em {url}"
            if contem:
                assert contem in resp.content, f"texto '{contem.decode()}' não encontrado em {url}"

        verificar("página inicial", lambda: pagina("/", contem=b"JandAIa"))
        verificar("painel administrativo", lambda: pagina("/admin/login/"))
        verificar("arquivos estáticos (css)", lambda: pagina("/static/admin/css/base.css"))
        verificar("área restrita exige login", lambda: pagina("/admin-treinar/", esperado=302))

        def modelos():
            from gerador.models import Curso, EsqueletoQuestao, Topico
            for modelo in (Curso, Topico, EsqueletoQuestao):
                modelo.objects.count()

        verificar("modelos do banco", modelos)

    registrar("RESULTADO: " + ("TUDO CERTO" if not falhou else f"{len(falhou)} verificação(ões) falharam"))
    if arquivo_saida:
        Path(arquivo_saida).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return 1 if falhou else 0


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def principal(argv=None):
    parser = argparse.ArgumentParser(prog=APP, description=f"{APP} - gerador de avaliações com IA")
    parser.add_argument("--configurar", action="store_true", help="reabre a configuração da chave da Groq")
    parser.add_argument("--headless", action="store_true", help="sem janela (testes/servidor)")
    parser.add_argument("--sem-navegador", action="store_true", help="não abre o navegador")
    parser.add_argument("--porta", type=int, default=PORTA_PADRAO, help="porta preferida")
    parser.add_argument("--autoteste", nargs="?", const="", metavar="ARQUIVO",
                        help="verifica a integridade do pacote e sai")
    parser.add_argument("--versao", action="store_true", help="mostra a versão e sai")
    args = parser.parse_args(argv)

    if args.versao:
        print(f"{APP} {versao()}")
        return 0

    if args.autoteste is not None:
        os.environ["JANDAIA_DATA_DIR"] = tempfile.mkdtemp(prefix="jandaia-log-")

    dados = pasta_dados()
    preparar_log(dados, manter_console=args.headless or args.autoteste is not None)

    if args.autoteste is not None:
        return autoteste(args.autoteste or None)

    cfg = carregar_config(dados)
    porta_ativa = None if args.headless else instancia_ativa(dados)

    if porta_ativa and not args.configurar:
        if not args.sem_navegador:
            webbrowser.open(f"http://127.0.0.1:{porta_ativa}/")
        return 0

    primeira_vez = not (dados / "db.sqlite3").exists()
    senha_admin = None

    if args.headless:
        chave = os.environ.get("GROQ_API_KEY") or cfg.get("groq_api_key")
        if not chave:
            print("Defina GROQ_API_KEY no ambiente para usar --headless.", file=sys.stderr)
            return 2
        cfg["groq_api_key"] = chave
        senha_admin = os.environ.get("JANDAIA_ADMIN_PASSWORD")
    elif args.configurar or not cfg.get("groq_api_key") or primeira_vez:
        try:
            resposta = janela_configuracao(cfg.get("groq_api_key", ""), pedir_senha=primeira_vez)
        except Exception as erro:  # sem ambiente gráfico
            print(f"Não foi possível abrir a janela de configuração: {erro}", file=sys.stderr)
            return 2
        if resposta is None:
            return 1
        cfg["groq_api_key"], senha_admin = resposta
        salvar_config(dados, cfg)
        if porta_ativa:
            mensagem(APP, "Chave salva. Feche o programa e abra-o de novo para aplicar a mudança.")
            return 0

    configurar_ambiente(dados, cfg)
    estado = {"sem_navegador": args.sem_navegador}

    if args.headless:
        iniciar_servidor(dados, args.porta, primeira_vez, senha_admin, estado)
        if estado.get("erro"):
            print(estado["erro"], file=sys.stderr)
            return 1
        print(f"{APP} {versao()} em {estado['url']}  (Ctrl+C para encerrar)", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            (dados / "instancia.json").unlink(missing_ok=True)
        return 0

    def reconfigurar():
        resposta = janela_configuracao(cfg.get("groq_api_key", ""), pedir_senha=False)
        if resposta:
            cfg["groq_api_key"] = resposta[0]
            salvar_config(dados, cfg)
            mensagem(APP, "Chave salva. Feche o programa e abra-o de novo para aplicar a mudança.")

    threading.Thread(target=iniciar_servidor, daemon=True,
                     args=(dados, args.porta, primeira_vez, senha_admin, estado)).start()
    try:
        janela_principal(estado, reconfigurar)
    finally:
        (dados / "instancia.json").unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except SystemExit:
        raise
    except Exception:
        detalhe = traceback.format_exc()
        try:
            (pasta_dados() / "jandaia.log").open("a", encoding="utf-8").write(detalhe)
        except OSError:
            pass
        mensagem(APP, f"Erro inesperado:\n\n{detalhe[-800:]}", erro=True)
        sys.exit(1)
