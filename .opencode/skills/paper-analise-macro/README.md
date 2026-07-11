# skill-paper-am — Paper técnico estilo Análise Macro

Skill do Claude Code para montar o **relatório técnico** da entrega final como um
**paper Quarto → LaTeX (PDF)**, no padrão do projeto *Sentimento COPOM*.

## Instalar a skill

Copie esta pasta para as skills do seu Claude Code:

```bash
# por projeto
mkdir -p .claude/skills && cp -r skill-paper-am .claude/skills/paper-analise-macro
# ou global
mkdir -p ~/.claude/skills && cp -r skill-paper-am ~/.claude/skills/paper-analise-macro
```

Depois, no Claude Code: *"use a skill paper-analise-macro para montar o paper da entrega"*.

## Conteúdo

```
skill-paper-am/
├── SKILL.md                  # instruções da skill (lido pelo agente)
├── template/
│   ├── paper.qmd             # esqueleto com cabeçalho LaTeX e placeholders {{ }}
│   ├── referencias.bib       # exemplo de bibliografia
│   └── AM.png                # logo da capa
└── exemplo/
    ├── paper-exemplo.qmd     # paper completo e RENDERÁVEL (dados simulados)
    ├── paper-exemplo.pdf     # saída renderizada (referência de estilo)
    ├── referencias.bib
    └── AM.png
```

## Renderizar o exemplo

```bash
cd exemplo
python3 -m venv .venv && source .venv/bin/activate
pip install numpy pandas statsmodels matplotlib jupyter
quarto render paper-exemplo.qmd --to pdf
```

Pré-requisito de PDF: LaTeX via `quarto install tinytex`.

## Regra de ouro

Todo número exibido no paper vem de um **chunk que roda**. Nada digitado à mão.
