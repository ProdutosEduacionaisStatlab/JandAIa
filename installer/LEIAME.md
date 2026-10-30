# Guia do instalador (para quem mantém o projeto)

Este guia explica como os instaladores do JandAIa são gerados, testados e publicados.
Quem só quer **instalar** o programa deve seguir o [README](../README.md).

## O que é gerado

| Sistema | Arquivo | Ferramentas | Situação dos testes |
|---|---|---|---|
| Linux (Ubuntu/Debian) | `jandaia_X.Y.Z_amd64.deb` | PyInstaller + `dpkg-deb` | Testado: build, instalação, execução e remoção em Ubuntu 24.04 |
| Windows 10/11 (64 bits) | `JandAIa-Setup-X.Y.Z.exe` | PyInstaller + Inno Setup 6 | **Escrito, mas ainda não executado em máquina Windows** |
| macOS (Apple Silicon) | `JandAIa-X.Y.Z-macOS-arm64.dmg` | PyInstaller + `hdiutil` | **Escrito, mas ainda não executado em máquina Mac** |

Na primeira execução do workflow, é possível que Windows ou macOS precisem de pequenos ajustes. O próprio
workflow roda um **autoteste** do programa empacotado antes de gerar o instalador; se ele falhar, o log mostra o motivo.

## Como lançar uma versão

1. Confirme que tudo está no `main` e que o README está atualizado.
2. Crie e envie a tag (o número da versão vem da tag):
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. O GitHub Actions (aba **Actions**, workflow **Release**) gera os 3 instaladores, calcula o `SHA256SUMS.txt` e cria a
   release com os arquivos anexados e as notas automáticas.
4. Tags com hífen (por exemplo `v1.0.0-rc1`) viram **pré-lançamento**.

**Testar sem publicar:** em **Actions → Release → Run workflow**. Os instaladores ficam disponíveis como *artifacts*
da execução (use isso antes do primeiro `v1.0.0`) e nada é publicado.

## Como o programa instalado funciona

O `launcher.py` é o ponto de entrada. Ele:

- guarda o banco (`db.sqlite3`), a `config.json` (chave da Groq e uma `SECRET_KEY` gerada na primeira execução) e o
  `jandaia.log` na pasta de dados do usuário (veja o README);
- pede a chave da Groq e a senha do administrador na primeira execução;
- aplica as migrações, sobe o servidor local (Waitress, só em `127.0.0.1`) e abre o navegador;
- reaproveita a janela se o programa já estiver aberto.

Opções de linha de comando (úteis para testes):

| Opção | Efeito |
|---|---|
| `--versao` | Mostra a versão. |
| `--configurar` | Reabre a configuração da chave da Groq. |
| `--headless` | Sem janela: usa `GROQ_API_KEY` e `JANDAIA_ADMIN_PASSWORD` do ambiente. |
| `--sem-navegador` | Não abre o navegador. |
| `--porta N` | Porta preferida (padrão 8765; se estiver ocupada, usa outra livre). |
| `--autoteste [ARQUIVO]` | Verifica o pacote (bibliotecas, banco, páginas, estáticos) e sai com código 0 ou 1. |

A chave da Groq fica em texto no `config.json`. No Linux e no macOS o arquivo só é legível pelo usuário; no Windows
vale a permissão da pasta do perfil do usuário.

## Gerar localmente

Na raiz do projeto, com o ambiente virtual ativo:

```
pip install -r requirements.txt -r installer/requirements-installer.txt
python manage.py collectstatic --noinput
pyinstaller installer/jandaia.spec --noconfirm --clean
dist/JandAIa/JandAIa --autoteste        # no Windows: dist\JandAIa\JandAIa.exe --autoteste resultado.txt
```

Depois, o instalador de cada sistema:

- **Windows:** instale o [Inno Setup 6](https://jrsoftware.org/isinfo.php) e rode
  `ISCC.exe /DMyAppVersion=1.0.0 installer\windows\jandaia.iss` (saída em `dist_installer\`).
- **Linux:** `bash installer/linux/build_deb.sh 1.0.0`. Gere em Ubuntu 22.04 para que o pacote funcione também em
  sistemas mais antigos. Instale o Tk antes: `sudo apt install python3-tk`.
- **macOS:** `bash installer/macos/build_dmg.sh 1.0.0`.

O PyInstaller não gera para outro sistema: cada instalador precisa ser construído no próprio sistema (é o que o
workflow faz).

## Dados iniciais (cursos, tópicos e questões)

Sem dados, o programa abre vazio. Para que ele já venha com conteúdo, exporte o seu banco e coloque o arquivo na raiz
do projeto antes do build:

```
python manage.py dumpdata gerador --indent 2 --output dados_iniciais.json
```

Se o arquivo `dados_iniciais.json` existir, ele é empacotado e carregado **só na primeira execução** de cada usuário.
Salve-o em UTF-8 e faça o commit.

## Assinatura de código (evita os avisos de segurança)

**Windows.** Sem assinatura, o SmartScreen mostra o aviso "O Windows protegeu o computador". A opção gratuita para
projetos de código aberto é a [SignPath Foundation](https://signpath.org). Ela exige licença aprovada pela OSI,
repositório público e builds feitos no GitHub Actions. Resumo:

1. Defina a licença do projeto (arquivo `LICENSE` na raiz) e solicite a participação no site da SignPath Foundation.
2. Depois de aprovado, crie o projeto e a política de assinatura na SignPath, com o conector do GitHub.
3. No GitHub, em **Settings → Secrets and variables → Actions**, crie:
   - secret `SIGNPATH_API_TOKEN`;
   - variável `SIGNPATH_ORGANIZATION_ID`;
   - opcionalmente `SIGNPATH_PROJECT_SLUG` (padrão `jandaia`) e `SIGNPATH_POLICY_SLUG` (padrão `release-signing`).
4. O workflow já tem o passo de assinatura: ele só roda quando `SIGNPATH_ORGANIZATION_ID` existe e substitui o
   instalador pelo assinado.

Documentação: <https://docs.signpath.io/trusted-build-systems/github>. Detalhe: com o certificado da fundação, o
"editor" exibido no Windows é a SignPath Foundation, e o aviso some conforme o programa ganha reputação.

**macOS.** Sem o Apple Developer Program (US$ 99 por ano), o app só tem assinatura "ad-hoc" e o usuário precisa usar
"Abrir" com o botão direito na primeira vez. A assinatura com *Developer ID* e a notarização **não estão automatizadas**
no workflow: o `build_dmg.sh` aceita a variável `APPLE_SIGN_IDENTITY`, mas o certificado precisa estar no chaveiro da
máquina (uso local). Instituições de ensino podem pedir isenção da taxa, desde que se inscrevam como organização.

**Linux.** Não há aviso nem necessidade de assinatura.

## Trocar o ícone

O ícone atual é provisório. Para usar o logo do laboratório (imagem quadrada, de preferência 1024x1024 com fundo
transparente):

```
pip install pillow
python installer/gerar_icones.py caminho/do/logo.png
```

## Limitações conhecidas

- Atualização manual: o usuário baixa a versão nova e instala por cima (os dados são mantidos).
- O macOS gerado é para Apple Silicon (o runner `macos-latest` é arm64). Para Intel, seria preciso um runner `macos-13`.
- Só há pacote `.deb`. Para Fedora/Arch seria preciso criar `.rpm` ou AppImage.
- Antivírus podem apontar falso positivo em programas empacotados com PyInstaller. A assinatura de código e o
  envio do arquivo para análise ao fabricante do antivírus ajudam.
- O `AppId` em `installer/windows/jandaia.iss` identifica o programa nas atualizações do Windows: **nunca o altere**
  depois da primeira versão publicada.
