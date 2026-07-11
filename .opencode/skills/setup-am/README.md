# skill-setup-am — Setup do ambiente

Skill do Claude Code que prepara o ambiente da disciplina *AI Applications*: verifica/instala
VS Code, Python, Claude Code, Quarto e LaTeX, cria o `.venv` e a fundação do projeto, e
confere tudo com `quarto check`.

## Instalar a skill

Veja o [README do repositório](../README.md#-como-baixar-as-skills) para as formas de baixar.
Resumindo, copie esta pasta para:

```bash
# por projeto
cp -r skill-setup-am .claude/skills/setup-am
# ou global
cp -r skill-setup-am ~/.claude/skills/setup-am
```

Depois, no Claude Code: *"use a skill setup-am para preparar meu ambiente"*.

## Conteúdo

```
skill-setup-am/
├── SKILL.md                       # instruções da skill (lido pelo agente)
├── scripts/
│   └── verificar-ambiente.sh      # checa ferramentas, .venv e segredos
└── template/
    ├── CLAUDE.md                  # briefing do projeto
    ├── .gitignore                 # Python/Quarto + .env
    ├── .env.example               # variáveis de chave (sem valores)
    └── requirements.txt           # dependências base
```

## Conferir o ambiente manualmente

```bash
bash scripts/verificar-ambiente.sh
quarto check
```
