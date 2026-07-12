"""
redige_relatorio.py — Gera resumo estatístico e renderiza o paper em PDF.

Lê classificado.json, calcula estatísticas, grava resumido.json
e gera paper.qmd preenchido para renderização com Quarto.

Uso:
    python redige_relatorio.py
    quarto render paper.qmd --to pdf
"""

import json
import logging
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = Path(__file__).parent / "classificado.json"
OUTPUT_JSON = Path(__file__).parent / "resumido.json"
OUTPUT_QMD = Path(__file__).parent / "paper.qmd"


# ── Estatísticas ──────────────────────────────────────────────────────────────
def calcular_estatisticas(dados: dict) -> dict:
    """Calcula resumo estatístico a partir do classificado.json."""
    artigos = dados.get("artigos", [])
    total = len(artigos)

    if total == 0:
        logger.warning("Nenhum artigo encontrado para gerar estatísticas.")
        return {}

    # contagem por categoria arXiv
    todas_categorias = []
    for artigo in artigos:
        todas_categorias.extend(artigo.get("categorias", []))
    contagem_categoria = Counter(todas_categorias)

    # contagem por área tecnológica
    contagem_area = Counter(a.get("area_tecnologica", "N/D") for a in artigos)

    # contagem por maturidade
    contagem_maturidade = Counter(a.get("maturidade", "N/D") for a in artigos)

    # contagem por relevância
    contagem_relevancia = Counter(a.get("relevancia_negocio", "N/D") for a in artigos)

    # relevantes (alta + crítica)
    relevantes = [a for a in artigos if a.get("relevancia_negocio") in ["alta", "critica"]]
    pct_relevantes = (len(relevantes) / total * 100) if total > 0 else 0

    # artigos por data
    contagem_data = Counter(a.get("data_publicacao", "")[:10] for a in artigos)

    # top 5 por relevância (critica > alta)
    ordem_relevancia = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
    top5 = sorted(artigos, key=lambda x: ordem_relevancia.get(x.get("relevancia_negocio", "baixa"), 4))[:5]

    # estimativa de custo (baseado em tokens aproximados)
    tokens_por_artigo = 800  # estimativa: input + output
    custo_por_1k_tokens = 0.00025  # Claude Haiku 4.5 pricing
    total_tokens = total * tokens_por_artigo
    custo_total = (total_tokens / 1000) * custo_por_1k_tokens

    return {
        "total_artigos": total,
        "total_relevantes": len(relevantes),
        "pct_relevantes": round(pct_relevantes, 1),
        "categoria_arxiv": dict(contagem_categoria.most_common()),
        "area_tecnologica": dict(contagem_area.most_common()),
        "maturidade": dict(contagem_maturidade),
        "relevancia": dict(contagem_relevancia),
        "por_data": dict(sorted(contagem_data.items())),
        "top5": top5,
        "custo": {
            "total_tokens": total_tokens,
            "custo_por_artigo": round(custo_por_1k_tokens * tokens_por_artigo / 1000, 6),
            "custo_total": round(custo_total, 4),
        },
        "periodo": dados.get("periodo", {}),
    }


# ── JSON ──────────────────────────────────────────────────────────────────────
def salvar_resumido(estatisticas: dict, artigos: list[dict]) -> None:
    """Salva resumido.json com estatísticas + artigos."""
    payload = {
        "data_geracao": datetime.now().isoformat(),
        "estatisticas": estatisticas,
        "artigos": artigos,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Salvo em %s", OUTPUT_JSON)


# ── QMD ───────────────────────────────────────────────────────────────────────
def gerar_qmd(estatisticas: dict, artigos: list[dict]) -> None:
    """Gera paper.qmd com os dados reais da extração/classificação."""

    total = estatisticas.get("total_artigos", 0)
    relevantes = estatisticas.get("total_relevantes", 0)
    pct = estatisticas.get("pct_relevantes", 0)
    periodo = estatisticas.get("periodo", {})
    de = periodo.get("de", "?")
    ate = periodo.get("ate", "?")
    cat = estatisticas.get("categoria_arxiv", {})
    area = estatisticas.get("area_tecnologica", {})
    mat = estatisticas.get("maturidade", {})
    rel = estatisticas.get("relevancia", {})
    top5 = estatisticas.get("top5", [])
    custo = estatisticas.get("custo", {})

    # Tabela 1: Resumo da extração
    tbl_resumo_rows = f"""    Total de artigos & {total} \\\\
    Período & {de} a {ate} \\\\
    Relevantes & {relevantes} ({pct}\\%) \\\\
    Categorias arXiv & {len(cat)} \\\\
    Áreas tecnológicas & {len(area)} \\\\
    Custo estimado & \\${custo.get('custo_total', 0):.4f} \\\\ """

    # Tabela 2: Publicações por categoria arXiv (escapar underscores para LaTeX)
    tbl_cat_rows = "\n".join(f"    {n.replace('_', '\\_')} & {q} \\\\" for n, q in sorted(cat.items(), key=lambda x: -x[1]))

    # Tabela 3: Top áreas tecnológicas
    tbl_area_rows = "\n".join(f"    {n} & {q} \\\\" for n, q in sorted(area.items(), key=lambda x: -x[1]))

    # Tabela 4: Publicações por maturidade (escapar underscores para LaTeX)
    tbl_mat_rows = "\n".join(f"    {n.replace('_', '\\_')} & {q} \\\\" for n, q in sorted(mat.items()))

    # Tabela 5: Top 5 artigos
    tbl_top5_rows = ""
    for i, art in enumerate(top5, 1):
        titulo = art.get("titulo_pt", art.get("titulo", "")).replace("|", "\\|")[:60]
        area_tech = art.get("area_tecnologica", "N/D")
        relev = art.get("relevancia_negocio", "N/D")
        tbl_top5_rows += f"    {i} & {titulo} & {area_tech} & {relev} \\\\\n"

    # Tabela 6: Todos os artigos (multi-coluna) - escapar underscores para LaTeX
    tbl_artigos_rows = ""
    for art in artigos:
        data = art.get("data_publicacao", "")[:10]
        titulo = art.get("titulo_pt", art.get("titulo", "")).replace("|", "\\|").replace("_", "\\_")[:50]
        area_tech = art.get("area_tecnologica", "N/D").replace("_", "\\_")
        mat_val = art.get("maturidade", "N/D").replace("_", "\\_")
        relev = art.get("relevancia_negocio", "N/D").replace("_", "\\_")
        resumo = art.get("resumo_executivo_pt", "")[:80].replace("|", "\\|").replace("_", "\\_")
        tbl_artigos_rows += f"    {data} & {titulo} & {area_tech} & {mat_val} & {relev} & {resumo} \\\\\n"

    # Linhas para busca
    linhas_busca = "\n".join(f"    - `{c}`" for c in cat.keys())

    qmd = f"""---
title: "Relatório Semanal — ArXiv Monitor"
subtitle: "Extração, Classificação e Quantificação de Artigos Científicos"
author: "ArXiv Monitor"
date: today
lang: pt-BR
bibliography: referencias.bib
format:
  pdf:
    pdf-engine: xelatex
    toc: false
    number-sections: true
    geometry:
      - margin=2.5cm
    fontsize: 11pt
    code-overflow: wrap
    code-block-bg: "#F7F7F7"
    code-block-border-left: false
    highlight-style: github
    fig-width: 8
    fig-height: 4.5
    fig-pos: H
header-includes:
  - |
    \\usepackage{{etoolbox}}
    \\usepackage{{graphicx}}
    \\usepackage{{hyperref}}
    \\usepackage{{booktabs}}
    \\usepackage{{threeparttable}}
    \\usepackage{{caption}}
    \\captionsetup[table]{{skip=4pt}}
    \\renewcommand{{\\maketitle}}{{}}
    \\AtBeginEnvironment{{Shaded}}{{\\footnotesize}}
    \\AtBeginEnvironment{{verbatim}}{{\\footnotesize}}
    \\AtBeginEnvironment{{longtable}}{{\\small}}
    \\AtBeginEnvironment{{tabular}}{{\\small}}
execute:
  eval: true
  echo: true
  warning: false
  message: false
---

```{{=latex}}
\\begin{{titlepage}}
\\thispagestyle{{empty}}
\\centering

\\includegraphics[width=4cm]{{AM.png}}

\\vspace{{0.8cm}}

{{\\huge\\bfseries Relatório Semanal — ArXiv Monitor\\par}}

\\vspace{{1em}}

{{\\Large Extração, Classificação e Quantificação de Artigos Científicos\\par}}

\\vspace{{1.5em}}

{{\\large Período: {de} a {ate}\\par}}

\\vspace{{0.5em}}

{{\\normalsize {datetime.now().strftime('%d de %B de %Y')}\\par}}

\\vspace{{0.2em}}

{{\\footnotesize Versão 1.0\\par}}

\\vspace{{1.5em}}

\\begin{{minipage}}{{0.9\\textwidth}}
\\footnotesize
\\setlength{{\\parindent}}{{0pt}}

\\noindent\\textbf{{Resumo.}} Este relatório apresenta a análise semanal de artigos
científicos publicados no arXiv nas categorias de Inteligência Artificial (cs.AI),
Machine Learning (cs.LG), Processamento de Linguagem Natural (cs.CL) e Visão
Computacional (cs.CV). Foram extraídos **{total}** artigos via API, classificados por
um LLM (Claude Haiku) com saída estruturada (Pydantic), dos quais **{relevantes}**
({pct}\\%) foram identificados como relevantes para aplicações de negócios. A classificação
avaliou área tecnológica, maturidade e relevância de cada artigo, seguindo a
metodologia CRISP-DM.

\\smallskip
\\noindent\\textbf{{Palavras-chave:}} arXiv; Artigos Científicos; LLM; Saída Estruturada; CRISP-DM.
\\end{{minipage}}

\\end{{titlepage}}
```

# Resumo

Este relatório semanal analisa artigos científicos publicados no arXiv nas categorias
de Inteligência Artificial, Machine Learning, Processamento de Linguagem Natural e
Visão Computacional. O pipeline automatizado extrai, classifica e gera um relatório
executivo para tomadores de decisão, seguindo a metodologia CRISP-DM.

# Metodologia

Seguindo o fluxo **CRISP-DM**: (i) *entendimento do negócio* — identificar artigos
relevantes para aplicações de negócios em IA/ML/NLP/CV; (ii) *dados* — API pública do
arXiv, período de {de} a {ate}; (iii) *preparação* — extração com retry e filtragem por
data; (iv) *modelagem* — classificação via Claude Haiku com schema Pydantic; (v) *avaliação* —
análise estatística dos resultados; (vi) *implantação* — este paper reprodutível.

# Dados

## Parâmetros da extração

A extração foi realizada utilizando a API pública do arXiv com os seguintes parâmetros:

- **URL base:** `https://export.arxiv.org/api/query`
- **Período:** últimos 7 dias ({de} a {ate})
- **Categorias de busca:**
{linhas_busca}
- **Ordenação:** por data de submissão (decrescente)
- **Limite por página:** 100 artigos

## Schema de classificação

Cada artigo foi classificado com o seguinte schema Pydantic:

```{{python}}
#| echo: true
from pydantic import BaseModel, Field
from typing import Literal

class ArtigoClassificado(BaseModel):
    arxiv_id: str = Field(description="ID do artigo no arXiv")
    titulo_pt: str = Field(description="Título traduzido para o português")
    area_tecnologica: str = Field(description="Área tecnológica principal")
    resumo_executivo_pt: str = Field(description="Resumo executivo em português")
    maturidade: Literal["pesquisa_basica", "pesquisa_aplicada", "prototipo", "producao"]
    relevancia_negocio: Literal["baixa", "media", "alta", "critica"]
    justificativa: str = Field(description="Justificativa da relevância para negócios")

print("Schema definido com sucesso!")
```

# Resultados

## Resumo da extração

A Tabela @tbl-resumo apresenta um resumo dos dados extraídos e classificados.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Resumo da extração.}}
\\label{{tbl-resumo}}
\\begin{{tabular}}{{lr}}
\\toprule
Indicador & Valor \\\\
\\midrule
{tbl_resumo_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

## Distribuição por categoria arXiv

A Tabela @tbl-categoria mostra a distribuição de artigos por categoria arXiv.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Distribuição por categoria arXiv.}}
\\label{{tbl-categoria}}
\\begin{{tabular}}{{lr}}
\\toprule
Categoria & Quantidade \\\\
\\midrule
{tbl_cat_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

## Distribuição por área tecnológica

A Tabela @tbl-area apresenta a distribuição por área tecnológica identificada pelo LLM.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Distribuição por área tecnológica.}}
\\label{{tbl-area}}
\\begin{{tabular}}{{lr}}
\\toprule
Área Tecnológica & Quantidade \\\\
\\midrule
{tbl_area_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

## Distribuição por maturidade

A Tabela @tbl-maturidade mostra o nível de maturidade tecnológica dos artigos.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Distribuição por maturidade tecnológica.}}
\\label{{tbl-maturidade}}
\\begin{{tabular}}{{lr}}
\\toprule
Maturidade & Quantidade \\\\
\\midrule
{tbl_mat_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

## Top 5 artigos por relevância

A Tabela @tbl-top5 apresenta os 5 artigos com maior relevância para negócios.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Top 5 artigos por relevância para negócios.}}
\\label{{tbl-top5}}
\\begin{{tabular}}{{llll}}
\\toprule
\\# & Título & Área & Relevância \\\\
\\midrule
{tbl_top5_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

## Evolução diária

A Figura @fig-diaria mostra a distribuição de publicações por dia no período analisado.

```{{python}}
#| echo: false
#| label: fig-diaria
#| fig-cap: "Publicações por dia no período analisado."
import json
import matplotlib.pyplot as plt
from collections import Counter
from pathlib import Path

# Carregar dados do classificado.json
classificado = Path("classificado.json")
dados = json.loads(classificado.read_text(encoding="utf-8"))
artigos = dados.get("artigos", [])

datas = Counter(a.get("data_publicacao", "")[:10] for a in artigos)
datas_ordenadas = sorted(datas.items())

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar([d[0] for d in datas_ordenadas], [d[1] for d in datas_ordenadas], color="#18a0d7")
ax.set_xlabel("Data")
ax.set_ylabel("Quantidade")
ax.set_title("Publicações por dia")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()
```

## Custo estimado

A Tabela @tbl-custo apresenta a estimativa de custo da classificação via API Anthropic.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\begin{{threeparttable}}
\\caption{{Custo estimado da classificação.}}
\\label{{tbl-custo}}
\\begin{{tabular}}{{lr}}
\\toprule
Métrica & Valor \\\\
\\midrule
Total de tokens & {custo.get('total_tokens', 0):,} \\\\
Custo por artigo & \\${custo.get('custo_por_artigo', 0):.6f} \\\\
Custo total & \\${custo.get('custo_total', 0):.4f} \\\\
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Estimativa baseada em 800 tokens por artigo (input + output). Preço Claude Haiku 4.5: \\$0.25/1M tokens.
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

# Lista de Artigos

## Todos os artigos

A Tabela @tbl-artigos lista todos os artigos extraídos e classificados no período.

```{{=latex}}
\\begin{{table}}[H]
\\centering
\\footnotesize
\\begin{{threeparttable}}
\\caption{{Todos os artigos extraídos no período.}}
\\label{{tbl-artigos}}
\\begin{{tabular}}{{llllll}}
\\toprule
Data & Título & Área & Maturidade & Relevância & Resumo \\\\
\\midrule
{tbl_artigos_rows}
\\bottomrule
\\end{{tabular}}
\\begin{{tablenotes}}\\footnotesize
\\item Fonte: API do arXiv, processado por LLM (Claude Haiku, temperature=0).
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}
```

# Conclusão

Foram extraídos **{total}** artigos do arXiv no período de {de} a {ate}, classificados
por um LLM com saída estruturada. Destes, **{relevantes}** ({pct}\\%) foram identificados
como relevantes para aplicações de negócios. O pipeline automatizado — extração via API,
classificação por LLM com schema Pydantic e geração do relatório — demonstra a viabilidade
de monitorar o arXiv com foco em oportunidades de negócio, seguindo a metodologia CRISP-DM.

O custo estimado da classificação foi de **\\${custo.get('custo_total', 0):.4f}**, tornando
o processo viável para operações semanais.

# Referências

::: {{#refs}}
:::
"""

    OUTPUT_QMD.write_text(qmd, encoding="utf-8")
    logger.info("Paper gerado em %s", OUTPUT_QMD)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not INPUT_FILE.exists():
        logger.error("Arquivo %s não encontrado. Execute classifica_dados.py primeiro.", INPUT_FILE)
        exit(1)

    dados = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    artigos = dados.get("artigos", [])

    estatisticas = calcular_estatisticas(dados)

    salvar_resumido(estatisticas, artigos)
    gerar_qmd(estatisticas, artigos)

    print(f"Resumo salvo em {OUTPUT_JSON.name}")
    print(f"Paper gerado em {OUTPUT_QMD.name}")
    print(f"Renderize com: quarto render paper.qmd --to pdf")
