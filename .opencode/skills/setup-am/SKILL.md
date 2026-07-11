---
name: setup-am
description: >-
  Guia e prepara o ambiente da disciplina AI Applications a partir do bootstrap mínimo
  (VS Code + Claude Code + conta Claude): instala Python, Quarto, LaTeX (TinyTeX) e Git;
  conduz a criação das chaves de API (Anthropic, Google, OpenAI) e da conta Meta (WhatsApp);
  conecta o VS Code ao GitHub e publica o repositório; cria o .venv e a fundação do projeto;
  e ajuda a rodar o exemplo da disciplina. Use no início de qualquer projeto ou setup.
---

# Skill: Setup do ambiente (estilo Análise Macro)

Esta skill guia o agente a montar o ambiente da disciplina **uma vez** e a deixar um
projeto novo pronto para começar. Ela **não cria contas** (isso é manual), mas conduz a
checagem e a instalação das ferramentas e monta a fundação do projeto.

## Como o aluno instala esta skill

Copie a pasta `skill-setup-am/` para as skills do seu Claude Code
(`.claude/skills/setup-am/` no projeto, ou `~/.claude/skills/setup-am/` global) e peça:
*"use a skill setup-am para preparar meu ambiente"*. Instruções de download no README.

## Premissa: o bootstrap mínimo já foi feito

Esta skill assume que o aluno já fez **na mão** o mínimo: instalou o **VS Code**, a
**extensão Claude Code** e está **logado na conta Claude**. Tudo o que vem abaixo a skill
**guia/executa** a partir daqui — instalar ferramentas, criar chaves/contas, conectar o
GitHub e rodar o exemplo.

> Conduza **uma etapa por vez** e **espere o aluno confirmar** antes de avançar. Não crie
> contas por ele (isso é manual); guie com links e diga onde colar cada valor.

## Passo 0 — Guiar a criação de contas e chaves

Acompanhe o aluno na criação de cada conta/chave e ajude a preencher o `.env`:

- **GitHub** — <https://github.com/signup> (versão + GitHub Actions)
- **Anthropic (API)** — <https://console.anthropic.com> → *Settings → API Keys → Create Key*
  → `ANTHROPIC_API_KEY`
- **Google AI Studio** — <https://aistudio.google.com/apikey> → *Create API key* → `GOOGLE_API_KEY`
- **OpenAI** — <https://platform.openai.com/api-keys> → *Create new secret key* → `OPENAI_API_KEY`
- **Meta for Developers (WhatsApp Cloud API)** — <https://developers.facebook.com> →
  *Get Started* → criar app **Business** → adicionar **WhatsApp** → em *API Setup* pegar
  **token**, **Phone number ID** e cadastrar o **número destinatário** de teste
  (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_DESTINO`)

Lembre o aluno: a **conta Claude.ai** (assinatura) é diferente da **conta de API da
Anthropic** (console, paga por uso). Cada chave aparece **uma única vez** — copie na hora.
Coloque limites de gasto na Anthropic/OpenAI; o Gemini tem plano gratuito.

## Passo 1 — Detectar o sistema e instalar as ferramentas

Detecte o SO e use o gerenciador de pacotes adequado. **Confirme com o usuário antes de
instalar** qualquer coisa.

**macOS (Homebrew):**
```bash
brew install --cask visual-studio-code
brew install python quarto
```

**Windows (winget):**
```powershell
winget install Microsoft.VisualStudioCode
winget install Python.Python.3.12
winget install Posit.Quarto
```

**Linux (Debian/Ubuntu):** instale o VS Code pelo `.deb` oficial, `python3`/`python3-venv`
via apt e o Quarto pelo `.deb` em <https://quarto.org/docs/get-started/>.

Extensões do VS Code (todas as plataformas):
```bash
code --install-extension ms-python.python
code --install-extension quarto.quarto
code --install-extension anthropic.claude-code
```

LaTeX para PDF (qualquer SO):
```bash
quarto install tinytex
```

## Passo 1.5 — Conectar ao GitHub

Garanta que o aluno consegue versionar e publicar a partir do VS Code.

1. Instale o **Git** (se faltar) e configure a identidade:
```bash
git config --global user.name  "Nome do Aluno"
git config --global user.email "aluno@email.com"
```

2. Autentique no GitHub (uma vez), por uma das vias:
   - **VS Code:** ícone *Accounts* (canto inferior esquerdo) → *Sign in with GitHub*.
   - **Terminal:** `gh auth login` (GitHub CLI).

3. Verifique:
```bash
git --version
gh auth status   # se usar o GitHub CLI
```

## Passo 2 — Fundação do projeto

Copie os arquivos de `template/` para a pasta do projeto do aluno e ajuste o conteúdo:

- `template/CLAUDE.md` → briefing com objetivo, fontes, CRISP-DM e regra de ouro
- `template/.gitignore` → Python/Quarto + `.env`
- `template/.env.example` → variáveis de chave (sem valores reais)
- `template/requirements.txt` → dependências do projeto

Crie e ative o ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

No VS Code, selecione o interpretador do `.venv`
(`Ctrl/Cmd+Shift+P → Python: Select Interpreter`).

## Passo 2.5 — Criar e publicar o repositório

Inicialize o git, faça o primeiro commit e publique no GitHub. Confirme com o aluno se o
repositório deve ser **público** ou **privado**.

```bash
git init -b main
git add -A
git commit -m "Estrutura inicial do projeto"
gh repo create <nome-do-repo> --public --source=. --remote=origin --push
```

Sem o GitHub CLI, oriente o caminho do VS Code: painel **Source Control** →
*Initialize Repository* → **Commit** → **Publish to GitHub**. Garanta que o `.gitignore`
já existe (Passo 2) **antes** do primeiro commit, para o `.env` nunca subir.

## Passo 3 — Conferir tudo

Rode o verificador e reporte o que faltar:
```bash
bash scripts/verificar-ambiente.sh
quarto check
```

## Passo 4 — Rodar o exemplo da disciplina

Quando o ambiente estiver pronto, ajude o aluno a rodar o exemplo (relatório semanal no
WhatsApp), que vive em `projeto-exemplo/` do repositório da disciplina:

```bash
cd projeto-exemplo
pip install -r requirements.txt
cp .env.example .env        # preencha as chaves (Passo 0)
python main.py
```

Para o paper de entrega, oriente o uso da skill **paper-analise-macro**
(`quarto render paper.qmd --to pdf`).

## Regras (não negociáveis)

- **Sempre confirmar antes de instalar** software no computador do usuário.
- Chaves de API **só** no `.env` (no `.gitignore`); nunca no código nem no git.
- Um `.venv` por projeto. Não instalar pacotes no Python global.
- Ao final, o `quarto check` deve passar (Python, Jupyter e LaTeX OK).
