# CLAUDE.md — {{NOME DO PROJETO}}

## Objetivo

{{Qual problema de negócio este projeto resolve e qual decisão ele melhora.}}

## Fontes de dados

- {{Fonte 1 (API, banco, planilha) — onde e como acessar}}

## Metodologia (CRISP-DM)

1. **Negócio** — {{objetivo mensurável}}
2. **Dados** — {{fontes, volume, qualidade}}
3. **Preparação** — {{limpeza, recorte de sinal}}
4. **Modelagem** — LLM via API com **saída estruturada** (Pydantic) + baseline
5. **Avaliação** — validar em mais de uma camada/métrica
6. **Implantação** — entrega reprodutível (paper Quarto e/ou automação)

## Regra de ouro

**Nunca inventar número.** Todo valor citado vem de um chunk/execução real.

## Segredos

Chaves de API só no `.env` (no `.gitignore`), lidas por variável de ambiente.
Nunca versionar `.env`.

## Stack

- Python ≥ 3.10 em `.venv`
- Quarto + LaTeX (TinyTeX) para entrega em PDF
- Claude Code como agente de desenvolvimento
