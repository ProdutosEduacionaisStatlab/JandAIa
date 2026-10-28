# JandAIa — Gerador de Avaliações com IA

O **JandAIa** é uma aplicação web (Django) que gera **provas e gabaritos de qualquer disciplina** com apoio de IA generativa. O professor escolhe o nível de escolaridade, o contexto alvo (curso), os tópicos e o formato de cada questão. O sistema sorteia, entre os moldes cadastrados, os que vão entrar na prova e pede à IA que escreva enunciados com valores e situações novas. A tela mostra a **prova** e o **gabarito com resolução passo a passo**, prontos para imprimir ou salvar em PDF.

> **Importante:** o enunciado **e a resolução** são escritos pela IA. Ela pode errar contas ou ser imprecisa. **Revise sempre a prova e o gabarito antes de aplicar.**

## Sumário

1. [Para que serve](#para-que-serve)
2. [Como funciona](#como-funciona)
3. [Usando o sistema (professor)](#usando-o-sistema-professor)
4. [Instalação (primeira vez)](#instalação-primeira-vez)
5. [Rodar no dia a dia](#rodar-no-dia-a-dia)
6. [Cadastrando questões (esqueletos)](#cadastrando-questões-esqueletos)
7. [Configurações](#configurações)
8. [Docker e publicação em servidor](#docker-e-publicação-em-servidor)
9. [Solução de problemas](#solução-de-problemas)
10. [Limitações conhecidas](#limitações-conhecidas)
11. [Estrutura do repositório](#estrutura-do-repositório)

## Para que serve

Preparar várias versões de uma avaliação exige reescrever enunciados, trocar valores e refazer a resolução de cada versão à mão. O JandAIa automatiza esse trabalho: mantém fixa a estrutura de cada questão, varia só o que pode mudar entre versões e adapta o contexto ao público (Ensino Fundamental, Médio ou Superior).

**Para quem é:** professores de qualquer disciplina (exatas, humanas, linguagens etc.) que queiram agilizar a criação de provas e variações de questões.

## Como funciona

1. **Banco de esqueletos.** Cada questão é guardada como um *esqueleto*: tópico, subtópico, enunciado-base com variáveis (X, Y, Z) no lugar do que muda, regras de variação e os **cursos** (contextos alvo) em que vale. Esqueleto sem curso marcado vale para todos os contextos.
2. **Montagem.** Na página inicial, o professor informa nome e período, escolhe nível e contexto alvo e adiciona blocos de questão (tópico, quantidade de subitens e formato). Só aparecem os tópicos que têm questões para o contexto escolhido.
3. **Geração.** Para cada bloco, o sistema sorteia um esqueleto do tópico (entre os do contexto alvo ou os sem curso), monta o prompt e envia a um modelo hospedado na [Groq](https://groq.com) (API compatível com OpenAI).
4. **Saída.** A resposta é dividida em prova e gabarito (LaTeX só do corpo, sem preâmbulo). A tela renderiza as fórmulas com MathJax e mostra a prova com cabeçalho (professor, período e contexto), com um botão para alternar para o gabarito.

## Usando o sistema (professor)

Abra `http://127.0.0.1:8000/` (ou o endereço do seu servidor).

1. Preencha **Professor** e **Período**.
2. Escolha o **Nível de Escolaridade**. O campo **Contexto Alvo** só é liberado depois disso.
3. Escolha o **Contexto Alvo** (o curso).
4. Clique em **+ Questão** para cada questão da prova e preencha:
   - **Tópico**;
   - **Itens**: quantidade de subitens (a, b, c...). Use `0` para questão direta, sem subitens;
   - **Formato**: *Aberta* ou *Múltipla*.
5. Clique em **GERAR PDF E GABARITO** e aguarde a IA responder.
6. Na tela da avaliação:
   - **Ver gabarito / Ver prova** alterna entre os dois textos;
   - **Imprimir / Salvar PDF** usa a impressão do navegador, então salva o que estiver na tela (prova **ou** gabarito);
   - **Voltar e Montar Outra** retorna ao início.
7. **Confira o resultado** antes de usar.

## Instalação (primeira vez)

Requisitos: **Python 3.12 ou superior**, **Git** e uma **chave de API da Groq** (gratuita). O sistema precisa de internet para chamar a IA e para carregar Bootstrap e MathJax.

**1. Baixe o projeto**

```
git clone https://github.com/joaoatilamonteiro/JandAIa.git
cd JandAIa
```

**2. Crie e ative o ambiente virtual**

```
python -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS, ative com `source .venv/bin/activate`. O terminal deve mostrar `(.venv)` no início da linha.

**3. Instale as bibliotecas**

```
pip install -r requirements.txt
```

> O segundo comando é necessário porque `django-import-export` é usado pelo sistema mas **ainda não está listado no `requirements.txt`**. Sem ele, qualquer comando do Django termina com `No module named 'import_export'`.

**4. Configure a chave da Groq**

- Acesse [console.groq.com](https://console.groq.com), entre (ou crie uma conta), vá em **API Keys** e clique em **Create API Key**.
- Copie a chave (começa com `gsk_`). Ela só é exibida uma vez.
- Crie um arquivo chamado `.env` na raiz do projeto (ao lado do `manage.py`) com este conteúdo:

```
GROQ_API_KEY=gsk_sua-chave-aqui
```

No Windows, confirme que o arquivo se chama `.env` e não `.env.txt`.

> Nunca envie o `.env` ao Git nem compartilhe a chave. Ele já está no `.gitignore`.
> Faça este passo **antes** do próximo: sem a chave, o `migrate` falha com `Missing credentials`.

**5. Crie o banco de dados e o usuário administrador**

```
python manage.py migrate
python manage.py createsuperuser
```

**6. Ligue o servidor**

```
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. O sistema ainda está vazio: cadastre cursos, tópicos e esqueletos como na próxima seção.

### Instalação no Linux

Os comandos abaixo valem para Ubuntu/Debian, Fedora e Arch.

**1. Instale as dependências do sistema**

```
# Ubuntu / Debian
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip

# Fedora
sudo dnf install -y git python3 python3-pip

# Arch / Manjaro
sudo pacman -S --needed git python python-pip
```

Confira a versão com `python3 --version`: precisa ser **3.12 ou superior**. O Ubuntu 24.04 em diante e o Fedora recente já trazem essa versão.

**2. Baixe o projeto e crie o ambiente virtual**

```
git clone https://github.com/joaoatilamonteiro/JandAIa.git
cd JandAIa
python3 -m venv .venv      
source .venv/bin/activate
```

**3. Instale as bibliotecas**

```
pip install -r requirements.txt
```


**4. Configure a chave da Groq**

Crie a chave em [console.groq.com](https://console.groq.com) (**API Keys** → **Create API Key**) e salve-a no `.env`:

```
echo "GROQ_API_KEY=gsk_sua-chave-aqui" > .env
```

**5. Crie o banco, o administrador e ligue o servidor**

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

**Para abrir em outros computadores da rede**, rode `python manage.py runserver 0.0.0.0:8000` e acesse pelo IP do computador (descubra com `hostname -I`). Se os formulários derem erro 403, acrescente esse endereço em `CSRF_TRUSTED_ORIGINS` no `settings.py`. Para uso permanente, prefira o [Docker](#docker-e-publicação-em-servidor).

## Rodar no dia a dia

```
.venv\Scripts\activate
python manage.py runserver
```

No Linux, troque a primeira linha por `source .venv/bin/activate`.

| Endereço | O que é |
|---|---|
| `http://127.0.0.1:8000/` | Gerador de provas |
| `http://127.0.0.1:8000/admin/` | Painel administrativo (cursos, tópicos, esqueletos) |
| `http://127.0.0.1:8000/admin-treinar/` | Importação de lista de exercícios em PDF (exige login de administrador) |

Depois de um `git pull`, rode `python manage.py migrate` para aplicar migrações novas.

## Cadastrando questões (esqueletos)

No painel `/admin/`, cadastre nesta ordem:

1. **Cursos.** Cada curso é um **contexto alvo**, com nome, nível (fundamental, médio ou superior) e uma descrição de contexto, que vai para o prompt da IA.
2. **Tópicos.** Por exemplo: Probabilidade, Revolução Francesa, Funções em Python.
3. **Esqueletos de questão.** Informe tópico, subtópico, enunciado-base com variáveis (X, Y, Z), regras de variação e resposta esperada. No campo **Cursos**, escolha em quais contextos a questão deve aparecer; deixe vazio para valer para todos.

**Dica para as regras de variação:** diga o que pode mudar (números, nomes, datas, lugares), dentro de faixas ou listas plausíveis, e acrescente restrições que evitem resultados ambíguos ou absurdos. Em disciplinas sem números, sorteie de listas de opções (personagens, períodos, regiões).

### Importação em lote (CSV/planilha)

Na lista de esqueletos do admin há os botões **Importar** e **Exportar**. As colunas esperadas são `id` (vazio para criar um novo), `topico`, `subtopico`, `enunciado_base`, `instrucoes_ia` e `cursos`. Em `topico` e `cursos`, use os **ids** dos registros existentes. Em `cursos`, separe vários ids por vírgula (vazio = todos os contextos).

### Extração automática a partir de um PDF

Entre como administrador e abra `/admin-treinar/`. Envie uma lista de exercícios em **PDF**. A IA lê o texto e cria esqueletos genéricos, que são salvos direto no banco. Observações:

- Só aceita `.pdf` com texto selecionável (PDF escaneado como imagem não funciona).
- Os esqueletos criados ficam **sem curso**, ou seja, valem para todos os contextos. Associe os cursos depois, no admin.
- Revise os esqueletos criados: a extração é feita pela IA.

## Configurações

| Onde | O que |
|---|---|
| `.env` → `GROQ_API_KEY` | **Obrigatória.** Chave da Groq. |
| `.env` → `SECRET_KEY` | Recomendada em servidor. Se ausente, o sistema usa uma chave padrão de desenvolvimento. |
| `gerador/views.py` → `MODELO` | Modelo da Groq usado nas chamadas (atualmente `openai/gpt-oss-120b`). |
| `jandaia/settings.py` | Banco SQLite (`db.sqlite3`, ignorado pelo Git), idioma `pt-br`, fuso `America/Sao_Paulo`. |

**Para uso em servidor**, revise também em `jandaia/settings.py`: `DEBUG` (hoje `True`), `ALLOWED_HOSTS` (hoje `['*']`) e `CSRF_TRUSTED_ORIGINS` (lista fixa de endereços: troque pelo endereço do seu servidor, senão os formulários retornam erro 403).

**Acesso:** a página inicial e a geração de provas **não exigem login**. Quem tiver o endereço consegue gerar provas e consumir a cota da sua chave da Groq. Em servidor público, restrinja o acesso.

## Docker e publicação em servidor

O repositório traz apenas o `Dockerfile` (Python 3.12 + TeX Live + Gunicorn na porta 8000). Ele **não** executa `migrate` automaticamente e **não** traz `docker-compose.yml`. Exemplo de uso (adapte ao seu servidor):

```
docker build -t jandaia .
touch db.sqlite3
docker run -d --name jandaia -p 8000:8000 --env-file .env -v "$PWD/db.sqlite3:/app/db.sqlite3" jandaia
docker exec jandaia python manage.py migrate
docker exec -it jandaia python manage.py createsuperuser
```

No Linux, instale o Docker Engine pelo [guia oficial](https://docs.docker.com/engine/install/) e, para usar sem `sudo`, rode `sudo usermod -aG docker $USER` e abra uma nova sessão.

Cuidados:

- O arquivo `db.sqlite3` mapeado como volume guarda o banco fora do container. Sem ele, os dados somem ao recriar o container.
- Não há `.dockerignore`: um `.env` presente na pasta é copiado para dentro da imagem. **Não publique a imagem** em registro público.
- Depois de mudar `requirements.txt` ou o `Dockerfile`, reconstrua a imagem (`docker build` ou `docker compose up -d --build`).

## Solução de problemas

| Sintoma | O que fazer |
|---|---|
| `OpenAIError: Missing credentials` ao rodar o Django | O `.env` não existe, está com outro nome ou sem `GROQ_API_KEY`. Confira a raiz do projeto e reinicie. |
| Tela "Erro na IA" ao gerar | Leia a mensagem: chave inválida, cota da Groq esgotada, modelo indisponível ou falta de internet. |
| Aparece "A IA não separou o gabarito corretamente" | A IA não inseriu o marcador de separação. Gere novamente. |
| Nenhum tópico aparece no bloco | O contexto alvo escolhido não tem esqueletos (nem esqueletos sem curso). Cadastre no admin. |
| Fórmulas aparecem como texto cru | MathJax é carregado da internet. Verifique a conexão. |
| Erro 403 (CSRF) em servidor | O endereço de acesso não está em `CSRF_TRUSTED_ORIGINS`. |
| `/admin-treinar/` leva ao login | Entre como administrador no `/admin/` e acesse de novo. |
| `ensurepip is not available` ao criar o ambiente (Ubuntu/Debian) | Instale o pacote com `sudo apt install python3-venv` e crie o ambiente de novo. |
| `No matching distribution found for Django==6...` ou erro de versão | Seu Python é anterior ao 3.12. Veja `python3 --version` e instale o 3.12 com o uv (seção Linux). |
| `venv` não ativa no PowerShell | Rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo. |

## Limitações conhecidas

- **Correção pela IA.** Nada valida automaticamente se as contas e a resposta final estão certas. A revisão pelo professor é obrigatória.
- Cada clique em **Gerar** produz uma prova nova. Para ter o gabarito da mesma prova, use o botão **Ver gabarito** na mesma tela, sem gerar de novo.
- O PDF sai pela impressão do navegador, e não há histórico de provas geradas.
- O sorteio escolhe **um** esqueleto por bloco. Se o tópico não tiver esqueleto para o contexto, a IA recebe só o nome do tópico.
- Existem as rotas `baixar-latex/` e `baixar-pacote/` (download de `.tex` e `.zip`), mas ainda não há botões para elas na interface.
- Os templates `ia.html`, `importar.html` e `previa.html` não estão ligados a nenhuma rota atual.

## Estrutura do repositório

```
JandAIa/
├── manage.py
├── requirements.txt       # dependências (arquivo em UTF-16; falta django-import-export)
├── Dockerfile             # Python 3.12 + TeX Live + Gunicorn
├── jandaia/               # configuração do Django (settings, urls, wsgi, asgi)
└── gerador/               # app principal
    ├── models.py          # Curso, Topico, EsqueletoQuestao
    ├── admin.py           # painel admin (importação/exportação de esqueletos)
    ├── views.py           # index, gerar_provas, treinar_ia, downloads
    ├── urls.py
    ├── migrations/
    └── templates/gerador/ # index.html (construtor), visualizar.html (prova/gabarito), treinar.html, ...
```

**Tecnologias:** Python 3.12 · Django 6 · SQLite · API da Groq (compatível com OpenAI) · MathJax · Bootstrap · PyPDF2 · django-import-export · Gunicorn + WhiteNoise · Docker.