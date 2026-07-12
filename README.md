# ArXiv Monitor

Monitoramento semanal de artigos científicos publicados no arXiv nas categorias de
Inteligência Artificial (cs.AI), Machine Learning (cs.LG), Processamento de Linguagem
Natural (cs.CL) e Visão Computacional (cs.CV).

## Metodologia

Este projeto segue a metodologia **CRISP-DM**:

1. **Negócio** — Identificar artigos relevantes para aplicações de negócios
2. **Dados** — Extração via API arXiv (Atom XML)
3. **Preparação** — Normalização de campos, tradução de títulos
4. **Modelagem** — Classificação via LLM (Claude Haiku) com saída estruturada (Pydantic)
5. **Avaliação** — Análise estatística dos resultados
6. **Implantação** — Paper reprodutível (Quarto → PDF)

## Requisitos

- Python ≥ 3.10
- Quarto + LaTeX (TinyTeX)
- Chave de API Anthropic (`.env`)

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar chaves de API
cp .env.example .env
# Editar .env com suas chaves
```

## Uso

```bash
# Executar pipeline completo
python main.py

# Pular classificação LLM (usar classificado.json existente)
python main.py --skip-llm

# Pular renderização PDF
python main.py --skip-pdf

# Renderizar manualmente
quarto render paper.qmd --to pdf
```

## Estrutura

```
.
├── extrai_dados.py      # Extrai artigos do arXiv
├── classifica_dados.py  # Classifica artigos via LLM
├── redige_relatorio.py  # Gera estatísticas e paper.qmd
├── main.py              # Orquestra o pipeline
├── coletado.json        # Dados brutos extraídos
├── classificado.json    # Artigos classificados
├── resumido.json        # Resumo estatístico
├── paper.qmd            # Documento Quarto
├── paper.pdf            # PDF renderizado
├── referencias.bib      # Bibliografia
├── AM.png               # Logo para o paper
├── requirements.txt     # Dependências Python
├── .env                 # Chaves de API (não versionado)
└── .env.example         # Exemplo de .env
```

## Regra de Ouro

**Nunca inventar número.** Todo valor citado vem de um chunk/execução real.
