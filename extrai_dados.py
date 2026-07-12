"""
extrai_dados.py — Extrai artigos do arXiv nas categorias cs.AI, cs.LG, cs.CL, cs.CV
via API Atom XML e salva em coletado.json.

Uso:
    python extrai_dados.py
"""

import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Configuração ──────────────────────────────────────────────────────────────
BASE_URL = "https://export.arxiv.org/api/query"

CATEGORIAS = [
    "cat:cs.AI",  # Inteligência Artificial
    "cat:cs.LG",  # Machine Learning
    "cat:cs.CL",  # Processamento de Linguagem Natural
    "cat:cs.CV",  # Visão Computacional
]

TODAY = datetime.utcnow()
FROM_DATE = (TODAY - timedelta(days=7)).strftime("%Y-%m-%d")
TO_DATE = TODAY.strftime("%Y-%m-%d")

MAX_RESULTS = 100
PAGE_SIZE = 100
MAX_ARTIGOS = 100  # limite para teste rápido
OUTPUT_FILE = Path(__file__).parent / "coletado.json"

# Namespaces Atom
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


# ── Sessão HTTP com Retry ─────────────────────────────────────────────────────
def criar_sessao() -> requests.Session:
    """Cria uma sessão requests com retry e backoff exponencial."""
    sessao = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    sessao.mount("https://", adapter)
    sessao.mount("http://", adapter)
    return sessao


# ── Extração ──────────────────────────────────────────────────────────────────
def montar_query() -> str:
    """Monta a query combinando categorias com OR."""
    return " OR ".join(CATEGORIAS)


def buscar_pagina(sessao: requests.Session, start: int) -> list[dict]:
    """Busca uma página de resultados na API arXiv.
    Retorna lista de artigos extraídos do XML."""
    query = montar_query()
    params = {
        "search_query": query,
        "start": start,
        "max_results": PAGE_SIZE,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        resp = sessao.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Erro de rede ao buscar start=%d: %s", start, e)
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.error("Erro ao parsear XML: %s", e)
        return []

    entries = root.findall("atom:entry", NS)
    artigos = []

    for entry in entries:
        artigo = extrair_campos(entry)
        if artigo:
            artigos.append(artigo)

    logger.info("start=%d Artigos=%d (total na página: %d)", start, len(artigos), len(entries))
    return artigos


def extrair_campos(entry) -> dict | None:
    """Extrai e normaliza os campos relevantes de uma entry Atom."""
    # Título
    titulo_elem = entry.find("atom:title", NS)
    titulo = titulo_elem.text.strip().replace("\n", " ") if titulo_elem is not None else ""

    # Autores
    autores = []
    for author in entry.findall("atom:author", NS):
        name = author.find("atom:name", NS)
        if name is not None:
            autores.append(name.text.strip())

    # Resumo (abstract)
    summary_elem = entry.find("atom:summary", NS)
    resumo = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""

    # Data de publicação
    published_elem = entry.find("atom:published", NS)
    data_publicacao = published_elem.text.strip() if published_elem is not None else ""

    # Categorias
    categorias = []
    for cat in entry.findall("atom:category", NS):
        term = cat.get("term", "")
        if term:
            categorias.append(term)

    # ID do artigo (arXiv ID)
    id_elem = entry.find("atom:id", NS)
    arxiv_id = ""
    link_pdf = ""
    if id_elem is not None:
        arxiv_id = id_elem.text.strip()
        # Extrair apenas o ID numérico (ex: 2407.12345v1)
        if "/abs/" in arxiv_id:
            arxiv_id = arxiv_id.split("/abs/")[-1]
        # Montar link para PDF
        link_pdf = f"https://arxiv.org/pdf/{arxiv_id}"

    # Filtrar por data (últimos 7 dias)
    if data_publicacao:
        try:
            data_pub = datetime.fromisoformat(data_publicacao.replace("Z", "+00:00"))
            data_limite = TODAY - timedelta(days=7)
            if data_pub.replace(tzinfo=None) < data_limite:
                return None  # Artigo fora do período
        except ValueError:
            pass  # Se não conseguir parsear, incluir o artigo

    if not titulo:
        return None

    return {
        "arxiv_id": arxiv_id,
        "titulo": titulo,
        "autores": autores,
        "resumo": resumo,
        "data_publicacao": data_publicacao[:10],  # YYYY-MM-DD
        "categorias": categorias,
        "link_pdf": link_pdf,
    }


def extrair_todos() -> list[dict]:
    """Loopa todas as páginas, coletando artigos únicos dos últimos 7 dias."""
    sessao = criar_sessao()
    todos: list[dict] = []
    vistos: set[str] = set()
    start = 0

    while True:
        logger.info("Buscando artigos (start=%d)", start)
        artigos = buscar_pagina(sessao, start)

        if not artigos:
            break

        for artigo in artigos:
            chave = artigo["arxiv_id"] or artigo["titulo"]
            if chave and chave not in vistos:
                vistos.add(chave)
                todos.append(artigo)

        start += PAGE_SIZE
        time.sleep(3)  # respeitar rate limit do arXiv

        # Parar se não houver mais resultados ou atingir limite
        if len(artigos) < PAGE_SIZE or len(todos) >= MAX_ARTIGOS:
            break

    logger.info("Total de artigos coletados: %d", len(todos))
    return todos


# ── Persistência ──────────────────────────────────────────────────────────────
def salvar(registros: list[dict]) -> None:
    """Salva os registros em coletado.json."""
    payload = {
        "fonte": "arXiv API",
        "data_extracao": TODAY.isoformat(),
        "periodo": {"de": FROM_DATE, "ate": TO_DATE},
        "categorias": CATEGORIAS,
        "total": len(registros),
        "artigos": registros,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Salvo em %s", OUTPUT_FILE)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    registros = extrair_todos()
    salvar(registros)
    print(f"Extração concluída: {len(registros)} artigos salvos em {OUTPUT_FILE.name}")
