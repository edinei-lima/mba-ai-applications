---
name: paper-analise-macro
description: >-
  Gera um paper técnico reprodutível em Quarto + LaTeX (PDF) no padrão Análise Macro:
  titlepage com logo, resumo, seções no fluxo CRISP-DM, tabelas booktabs/threeparttable
  e bibliografia. Use ao montar a ENTREGA FINAL da disciplina AI Applications (o relatório
  técnico do trabalho final) ou qualquer paper de ciência de dados em PDF.
---

# Skill: Paper técnico estilo Análise Macro

Esta skill ensina o agente a montar o **relatório técnico** da entrega final como um
**paper Quarto → LaTeX (PDF)**, no mesmo padrão do projeto *Sentimento COPOM*.

## Como o aluno instala esta skill

1. Copie a pasta `skill-paper-am/` deste repositório para as skills do seu Claude Code:
   - **Projeto:** `.claude/skills/paper-analise-macro/`
   - **Global:** `~/.claude/skills/paper-analise-macro/`
2. No Claude Code, peça: *"use a skill paper-analise-macro para montar o paper da minha entrega"*.

> A skill é só uma pasta com este `SKILL.md` + os arquivos de `template/` e `exemplo/`.
> Não precisa de instalação — basta o Claude Code enxergar a pasta.

## Quando usar

- Quando o usuário precisa entregar um **relatório técnico em PDF** de um projeto de dados.
- Especialmente na **entrega final** da disciplina (ver `trabalho-final.md`).

## O que produzir

Um paper com **titlepage próprio** (logo `AM.png`, título, autores, data, versão, resumo),
seções na ordem do **CRISP-DM** e tabelas/figuras **geradas por código que roda**.

### Arquivos da skill

- `template/paper.qmd` — esqueleto pronto, com cabeçalho LaTeX e placeholders `{{ }}`.
- `template/referencias.bib` — exemplo de bibliografia (BibTeX).
- `template/AM.png` — logo usada na capa (troque pela do aluno, se houver).
- `exemplo/paper-exemplo.qmd` — **paper completo e renderável** como referência de estilo.

## Estrutura obrigatória do paper

1. **Capa (titlepage)** — logo, título, subtítulo, autores, data, versão e **Resumo** +
   **Palavras-chave**.
2. **Introdução** — problema de negócio e contribuição.
3. **Revisão da Literatura** — trabalhos/abordagens relacionadas.
4. **Metodologia e Dados** — fontes, recorte, e como o método mapeia o CRISP-DM.
5. **Implementação** — chunks de código comentados (coleta, modelagem com LLM, avaliação).
6. **Resultados** — tabelas e figuras geradas pelo código.
7. **Próximos Passos** e **Conclusão**.
8. **Referências** — via `referencias.bib`.

## Regras (não negociáveis)

- **Regra de ouro:** nenhum número é digitado à mão. Toda tabela/figura/estatística vem de
  um **chunk que roda**. Se não rodou, não entra.
- **LLM via API com saída estruturada** (Pydantic / structured output) na seção de Modelagem.
- **Segredos** lidos do ambiente (`.env`), nunca no `.qmd` nem no git.
- Tabelas de regressão em **booktabs + threeparttable** (nota de rodapé embaixo).
- Render com **xelatex** (PDF). LaTeX via `quarto install tinytex`.

## Como renderizar

```bash
quarto render paper.qmd --to pdf
```

## Passo a passo sugerido para o agente

1. Copie `template/paper.qmd` e `template/referencias.bib` para a pasta do projeto.
2. Preencha os placeholders `{{TITULO}}`, `{{AUTOR}}`, `{{RESUMO}}` etc.
3. Conecte os chunks de Implementação aos módulos reais do projeto do aluno.
4. Garanta que cada número exibido sai de uma variável calculada num chunk.
5. `quarto render paper.qmd --to pdf` e reporte se algum chunk falhou.
6. Use `exemplo/paper-exemplo.qmd` como referência de tom, estrutura e formatação.
