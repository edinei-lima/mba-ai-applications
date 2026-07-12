"""
classifica_dados.py — Classifica artigos do arXiv usando LLM Anthropic.

Lê coletado.json, envia cada artigo para o Claude Haiku com saída
estruturada via tool_use e salva o resultado em classificado.json.

Uso:
    python classifica_dados.py
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Literal

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Variáveis de ambiente ─────────────────────────────────────────────────────
load_dotenv()

INPUT_FILE = Path(__file__).parent / "coletado.json"
OUTPUT_FILE = Path(__file__).parent / "classificado.json"

MODELO = "claude-haiku-4-5"
TEMPERATURA = 0
MAX_RETRIES = 3
RETRY_DELAY = 2


# ── Schema de saída estruturada ──────────────────────────────────────────────
class ArtigoClassificado(BaseModel):
    """Schema Pydantic para saída estruturada do LLM."""

    arxiv_id: str = Field(description="ID do artigo no arXiv")
    titulo_en: str = Field(description="Título original em inglês")
    titulo_pt: str = Field(description="Título traduzido para o português")
    autores: list[str] = Field(description="Lista de autores")
    data_publicacao: str = Field(description="Data de publicação ISO 8601")
    categorias: list[str] = Field(description="Categorias arXiv do artigo")
    area_tecnologica: str = Field(
        description="Área tecnológica principal: "
                    "LLM, Visão Computacional, Aprendizado por Reforço, "
                    "IA Generativa, MLOps, Robótica, Segurança em IA, Outra"
    )
    resumo_executivo_en: str = Field(
        description="Executive summary in English, max 3 sentences"
    )
    resumo_executivo_pt: str = Field(
        description="Resumo executivo em português, linguagem executiva, máximo 3 frases"
    )
    maturidade: Literal[
        "pesquisa_basica", "pesquisa_aplicada", "prototipo", "producao"
    ] = Field(description="Nível de maturidade tecnológica do trabalho")
    relevancia_negocio: Literal["baixa", "media", "alta", "critica"] = Field(
        description="Relevância para aplicações de negócios"
    )
    justificativa: str = Field(
        default="",
        description="Por que este artigo tem esta relevância para negócios"
    )
    link: str = Field(
        default="",
        description="URL do artigo no arXiv"
    )


# ── Tool definition for structured output ─────────────────────────────────────
CLASSIFICATION_TOOL = {
    "name": "classificar_artigo",
    "description": "Classifica um artigo do arXiv nas categorias de IA/ML/NLP/CV.",
    "input_schema": ArtigoClassificado.model_json_schema(),
}


# ── Prompt de sistema ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Você é um analista de tecnologia e negócios sênior, especializado em Inteligência
Artificial, Machine Learning, Processamento de Linguagem Natural e Visão Computacional.

Sua tarefa é classificar artigos científicos do arXiv nas categorias cs.AI, cs.LG, cs.CL
e cs.CV.

Diretrizes:
1. Traduza o título para português (titulo_pt), mantendo o original em inglês (titulo_en).
2. Resuma o abstract em português (resumo_executivo_pt) e inglês (resumo_executivo_en),
   linguagem executiva e objetiva, máximo 3 frases cada.
3. Identifique a área tecnológica principal (LLM, Visão Computacional, Aprendizado por
   Reforço, IA Generativa, MLOps, Robótica, Segurança em IA ou Outra).
4. Avalie a maturidade tecnológica (pesquisa_basica, pesquisa_aplicada, prototipo, producao).
5. Avalie a relevância para negócios (baixa, media, alta, critica).
6. Justifique a relevância para negócios em 1-2 frases.

REGRA DE OURO: Use SOMENTE informações presentes no abstract fornecido.
Nunca invente dados, valores ou nomes que não estejam no texto original.

IMPORTANTE: Você DEVE usar a ferramenta classificar_artigo para retornar sua classificação."""


# ── Classificação ─────────────────────────────────────────────────────────────
def classificar_artigo(
    client: anthropic.Anthropic, artigo: dict
) -> dict | None:
    """Envia um artigo para o LLM e retorna a classificação estruturada via tool_use."""
    texto = f"""\
Título: {artigo.get('titulo', '')}
Autores: {', '.join(artigo.get('autores', []))}
Data de publicação: {artigo.get('data_publicacao', '')}
Categorias: {', '.join(artigo.get('categorias', []))}
Abstract: {artigo.get('resumo', '')}
Link: {artigo.get('link_pdf', '')}"""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resposta = client.messages.create(
                model=MODELO,
                max_tokens=1024,
                temperature=TEMPERATURA,
                system=SYSTEM_PROMPT,
                tools=[CLASSIFICATION_TOOL],
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": texto}],
            )

            # Extract tool call result
            for block in resposta.content:
                if block.type == "tool_use" and block.name == "classificar_artigo":
                    dados_parse = block.input
                    classificacao = ArtigoClassificado(**dados_parse)
                    return {
                        **artigo,
                        "titulo_en": classificacao.titulo_en,
                        "titulo_pt": classificacao.titulo_pt,
                        "area_tecnologica": classificacao.area_tecnologica,
                        "resumo_executivo_en": classificacao.resumo_executivo_en,
                        "resumo_executivo_pt": classificacao.resumo_executivo_pt,
                        "maturidade": classificacao.maturidade,
                        "relevancia_negocio": classificacao.relevancia_negocio,
                        "justificativa": classificacao.justificativa,
                    }

            # Fallback: if no tool_use block, log warning
            logger.warning("Sem tool_use na resposta (tentativa %d/%d)", attempt, MAX_RETRIES)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return None

        except anthropic.APIError as e:
            logger.error("Erro na API Anthropic (tentativa %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return None
        except Exception as e:
            logger.error("Erro inesperado: %s", e)
            return None

    return None


def classificar_todos() -> tuple[list[dict], dict]:
    """Lê coletado.json e classifica cada artigo."""
    if not INPUT_FILE.exists():
        logger.error("Arquivo %s não encontrado. Execute extrai_dados.py primeiro.", INPUT_FILE)
        return [], {}

    dados = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    artigos = dados.get("artigos", [])
    periodo = dados.get("periodo", {})
    logger.info("Classificando %d artigos...", len(artigos))

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY não encontrada no ambiente.")
        return [], {}

    client = anthropic.Anthropic(api_key=api_key)
    classificados: list[dict] = []

    for i, artigo in enumerate(artigos, 1):
        logger.info("[%d/%d] Classificando: %s", i, len(artigos), artigo.get("titulo", "")[:60])
        resultado = classificar_artigo(client, artigo)
        if resultado:
            classificados.append(resultado)
        time.sleep(0.3)  # respeitar rate limit

    logger.info("Classificados: %d/%d", len(classificados), len(artigos))
    return classificados, periodo


# ── Persistência ──────────────────────────────────────────────────────────────
def salvar(classificados: list[dict], periodo: dict) -> None:
    """Salva o resultado em classificado.json."""
    relevantes = [c for c in classificados if c.get("relevancia_negocio") in ["alta", "critica"]]
    payload = {
        "total_classificados": len(classificados),
        "total_relevantes": len(relevantes),
        "periodo": periodo,
        "artigos": classificados,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Salvo em %s (%d relevantes)", OUTPUT_FILE, len(relevantes))


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    classificados, periodo = classificar_todos()
    if classificados:
        salvar(classificados, periodo)
        print(f"Classificação concluída: {len(classificados)} artigos salvos em {OUTPUT_FILE.name}")
    else:
        print("Nenhum artigo classificado.")
