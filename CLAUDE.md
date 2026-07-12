# CLAUDE.md — ArXiv Monitor

## Objetivo

Monitorar semanalmente os artigos científicos publicados no arXiv nas categorias de
Inteligência Artificial (cs.AI), Machine Learning (cs.LG), Processamento de Linguagem
Natural (cs.CL) e Visão Computacional (cs.CV), classificando-os por área tecnológica,
maturidade e relevância para negócios, e gerando um relatório executivo semanal para
tomadores de decisão.

## Fontes de dados

- **arXiv API** — API pública (export.arxiv.org/api/query), sem autenticação, retorno em formato Atom XML
- Categorias: cs.AI, cs.LG, cs.CL, cs.CV
- Período: últimos 7 dias

## Metodologia (CRISP-DM)

1. **Negócio** — Identificar artigos relevantes para aplicações de negócios em IA/ML/NLP/CV
2. **Dados** — Extração via API arXiv, filtragem por data, paginação
3. **Preparação** — Normalização de campos, tradução de títulos, deduplicação
4. **Modelagem** — LLM via API com **saída estruturada** (Pydantic) para classificação e resumo executivo
5. **Avaliação** — Análise estatística dos resultados, distribuições, top artigos
6. **Implantação** — Paper reprodutível (Quarto → PDF) com gráficos e tabelas

## Regra de ouro

**Nunca inventar número.** Todo valor citado vem de um chunk/execução real.

## Segredos

Chaves de API só no `.env` (no `.gitignore`), lidas por variável de ambiente.
Nunca versionar `.env`.

## APIs utilizadas

- **Anthropic** — Classificação de artigos (Claude Haiku 4.5, temperature=0)
- **Google** — Reservada para futuras integrações

## Stack

- Python ≥ 3.10 em `.venv`
- Quarto + LaTeX (TinyTeX) para entrega em PDF
- Requests + BeautifulSoup para extração de dados
- Pydantic para schemas estruturados
- Matplotlib/Seaborn para gráficos
