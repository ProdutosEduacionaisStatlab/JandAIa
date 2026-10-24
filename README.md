# StatLab — Gerador de Avaliações com IA

O **StatLab** é uma aplicação web (Django) que gera **provas e gabaritos de qualquer disciplina** (exatas, humanas, linguagens, entre outras) com apoio de IA generativa. O professor monta a avaliação escolhendo o nível de escolaridade, o contexto alvo, os tópicos e o formato das questões. O sistema sorteia, entre os moldes de questões cadastrados para aquele contexto, os que vão entrar na prova e pede à IA que produza enunciados com elementos novos (valores, nomes, datas, lugares ou situações, conforme a disciplina). Mostra na tela, separados, a **prova** e o **gabarito com resolução passo a passo**, prontos para imprimir ou salvar em PDF.

## Problema que resolve

Preparar várias versões de uma avaliação exige reescrever enunciados, trocar valores e refazer a resolução de cada versão à mão. O StatLab automatiza esse trabalho mantendo fixa a estrutura de cada questão, variando só o que pode mudar entre versões, e adaptando o contexto ao público (Ensino Fundamental, Médio ou Superior).

## Como funciona

1. **Banco de esqueletos:** cada questão é guardada como um "esqueleto", com tópico, subtópico, enunciado-base com variáveis (X, Y, Z) no lugar do que muda entre versões, regras de variação e resposta esperada e os **cursos (contextos alvo)** em que ela vale. Um esqueleto sem nenhum curso marcado vale para todos os contextos.
2. **Alimentação do banco:** os esqueletos são cadastrados ou importados pelo painel administrativo, ou extraídos automaticamente de uma lista de exercícios em PDF (a IA lê o PDF e o converte em moldes genéricos).
3. **Montagem da prova:** na página inicial o professor informa nome e período, escolhe o nível de escolaridade e o contexto alvo (curso) e adiciona blocos de questão, definindo tópico, quantidade de subitens e formato (aberta ou múltipla escolha). Os tópicos oferecidos são filtrados pelo contexto alvo escolhido: só aparecem os que têm questões para ele.
4. **Geração:** para cada bloco, o sistema sorteia um esqueleto do tópico (apenas entre os do contexto alvo ou os sem curso marcado), monta o prompt e o envia a um modelo hospedado na Groq.
5. **Saída:** a resposta é dividida em prova e gabarito, em LaTeX apenas do corpo (sem preâmbulo). A tela converte esse LaTeX simples para HTML, mostra a prova com cabeçalho (professor, semestre e contexto) e traz um botão para alternar para o gabarito. O botão de imprimir salva em PDF o que estiver na tela.

## Para quem é

Qualquer professor que queira agilizar o processo de criação de provas, produzindo avaliações e variações de questões com rapidez, sem abrir mão do rigor de cada disciplina.

## Tecnologias

Python 3.12 · Django 6 · SQLite · API compatível com OpenAI (Groq) · MathJax · PyPDF2 · django-import-export · Gunicorn + WhiteNoise · Docker (com TeX Live)

## Estrutura do repositório

- `statlab/`: configuração do projeto Django (settings, urls, wsgi/asgi)
- `gerador/`: app principal (modelos `Curso`, `Topico` e `EsqueletoQuestao`, views de geração e de treinamento, templates `index.html` e `visualizar.html`)
- `Dockerfile` e `requirements.txt`: empacotamento e deploy

## ⚙️ Primeira Instalação (Setup em um PC novo)

Se você for rodar este projeto pela primeira vez ou configurá-lo em um computador novo, siga este passo a passo do zero:

1. **Clone o repositório e entre na pasta:**
```bash
git clone https://github.com/ProdutosEduacionaisStatlab/produtoes_educacionais.git
cd produtoes_educacionais
```

2. **Crie o ambiente virtual:**

```bash
python -m venv .venv
```

3. **Ative o ambiente virtual:**

```bash
.venv\Scripts\activate
```

*(O terminal deve exibir um `(.venv)` verde no começo da linha).*

4. **Instale as bibliotecas obrigatórias:**

```bash
pip install -r requirements.txt
```

5. **Configure a Chave Secreta da API:**

* Acesse <https://console.groq.com> e faça login (ou crie uma conta gratuita).
* No menu lateral, vá em **API Keys** e clique em **Create API Key**.
* Copie a chave gerada (começa com `gsk_`) — ela só é exibida uma vez, então salve antes de fechar a tela.
* Crie um arquivo chamado `.env` na raiz do projeto (na mesma pasta do `manage.py`).
* Cole a sua chave da Groq dentro dele assim:

```text
GROQ_API_KEY=gsk_sua-chave-aqui
```

> **Atenção:** nunca envie o `.env` para o Git nem compartilhe a chave. O arquivo já deve estar no `.gitignore`.

6. **Prepare o Banco de Dados inicial e crie o Usuário Admin:**

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Como Rodar o Projeto no Dia a Dia

Se o projeto já está configurado e você quer apenas ligar o sistema para programar ou testar:

1. **Ative o Ambiente Virtual:**

```bash
.venv\Scripts\activate
```

2. **Ligue o Servidor:**

```bash
python manage.py runserver
```

3. **Acesse o Sistema no Navegador (localmente):**

* **Página Inicial (Gerador):** http://127.0.0.1:8000/
* **Painel do Professor (Admin):** http://127.0.0.1:8000/admin/
---

## Cadastrando questões (esqueletos)

No painel administrativo (`/admin/`), cadastre nesta ordem:

1. **Cursos:** cada curso é um **contexto alvo**, com nome, nível (fundamental, médio ou superior) e uma descrição de contexto, que vai para o prompt da IA.
2. **Tópicos:** por exemplo, Probabilidade, Revolução Francesa ou Funções em Python.
3. **Esqueletos de questão:** informe tópico, subtópico, enunciado-base com variáveis (X, Y, Z) e as regras de variação e a resposta esperada. No campo **Cursos**, escolha em quais contextos a questão deve aparecer; deixe vazio para valer para todos.

Os esqueletos também podem ser importados em lote pelo painel. As colunas esperadas são `id` (vazio para criar um novo), `topico`, `subtopico`, `enunciado_base`, `instrucoes_ia` e `cursos`. Em `topico` e `cursos` use os **ids** dos registros existentes, e em `cursos` separe vários ids por vírgula (vazio = todos os contextos).

Dica para as regras de variação: indique o que pode mudar (números, nomes, datas, lugares), dentro de faixas ou listas plausíveis, e restrições que evitem resultados ambíguos ou absurdos. Em disciplinas sem números, as variáveis podem ser sorteadas de listas de opções (por exemplo, personagens, períodos ou regiões).

---

## 🛠️ Comandos Úteis (Manutenção)

* **Atualizar o Banco de Dados (Use sempre que modificar o arquivo `models.py`):**

```bash
python manage.py makemigrations
python manage.py migrate
```

* **Depois de baixar atualizações do repositório (`git pull`):** aplique as migrações novas com `python manage.py migrate`.

* **Criar um usuário administrador extra:**

```bash
python manage.py createsuperuser
```