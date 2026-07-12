"""
main.py — Pipeline completo: extração → classificação → paper PDF.

Uso:
    python main.py              # executa tudo
    python main.py --skip-llm   # pula classificação (usa classificado.json existente)
    python main.py --skip-pdf   # para antes de renderizar o PDF
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent
QUARTO = Path(r"C:\Program Files\Quarto\bin\quarto.exe")


def etapa_extracao() -> int:
    """Executa a extração de dados do arXiv. Retorna o número de artigos."""
    from extrai_dados import extrair_todos, salvar

    t0 = time.time()
    registros = extrair_todos()
    salvar(registros)
    elapsed = time.time() - t0
    logger.info("Etapa 1 — Extração: %d artigos em %.1fs", len(registros), elapsed)
    return len(registros)


def etapa_classificacao() -> tuple[int, int]:
    """Executa a classificação via LLM. Retorna (total, relevantes)."""
    from classifica_dados import classificar_todos, salvar

    t0 = time.time()
    classificados, periodo = classificar_todos()
    if classificados:
        salvar(classificados, periodo)
    elapsed = time.time() - t0
    relevantes = sum(1 for c in classificados if c.get("relevancia_negocio") in ["alta", "critica"])
    logger.info("Etapa 2 — Classificação: %d/%d relevantes em %.1fs", relevantes, len(classificados), elapsed)
    return len(classificados), relevantes


def etapa_redacao() -> None:
    """Gera resumido.json e paper.qmd."""
    from redige_relatorio import calcular_estatisticas, salvar_resumido, gerar_qmd
    import json

    t0 = time.time()
    input_file = ROOT / "classificado.json"
    if not input_file.exists():
        logger.error("classificado.json não encontrado. Execute a etapa de classificação.")
        sys.exit(1)

    dados = json.loads(input_file.read_text(encoding="utf-8"))
    artigos = dados.get("artigos", [])
    estatisticas = calcular_estatisticas(dados)

    salvar_resumido(estatisticas, artigos)
    gerar_qmd(estatisticas, artigos)
    elapsed = time.time() - t0
    logger.info("Etapa 3 — Redação: paper.qmd + resumido.json em %.1fs", elapsed)


def etapa_renderizacao() -> bool:
    """Renderiza paper.qmd para PDF via Quarto. Retorna True se sucesso."""
    t0 = time.time()
    paper_qmd = ROOT / "paper.qmd"

    if not paper_qmd.exists():
        logger.error("paper.qmd não encontrado. Execute a etapa de redação.")
        return False

    if not QUARTO.exists():
        logger.warning("Quarto não encontrado em %s — pulando renderização.", QUARTO)
        return False

    logger.info("Etapa 4 — Renderizando PDF com Quarto...")
    env = {**__import__("os").environ, "QUARTO_PYTHON": str(ROOT / ".venv" / "Scripts" / "python.exe")}

    result = subprocess.run(
        [str(QUARTO), "render", "paper.qmd", "--to", "pdf"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    elapsed = time.time() - t0

    if result.returncode == 0:
        logger.info("PDF gerado com sucesso em %.1fs", elapsed)
        return True
    else:
        logger.error("Falha na renderização (exit %d):", result.returncode)
        if result.stdout:
            logger.error(result.stdout[-500:])
        if result.stderr:
            logger.error(result.stderr[-500:])
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ArXiv Monitor")
    parser.add_argument("--skip-llm", action="store_true", help="Pular classificação LLM")
    parser.add_argument("--skip-pdf", action="store_true", help="Pular renderização PDF")
    args = parser.parse_args()

    t_total = time.time()
    logger.info("=== Pipeline ArXiv Monitor ===")

    # Etapa 1 — Extração
    logger.info("─" * 50)
    n_pubs = etapa_extracao()

    # Etapa 2 — Classificação
    logger.info("─" * 50)
    if args.skip_llm:
        logger.info("Etapa 2 — Classificação: PULADA (--skip-llm)")
    else:
        n_class, n_rel = etapa_classificacao()

    # Etapa 3 — Redação
    logger.info("─" * 50)
    etapa_redacao()

    # Etapa 4 — Renderização
    logger.info("─" * 50)
    if args.skip_pdf:
        logger.info("Etapa 4 — Renderização: PULADA (--skip-pdf)")
        logger.info("Para renderizar manualmente: quarto render paper.qmd --to pdf")
    else:
        ok = etapa_renderizacao()
        if not ok:
            logger.warning("Renderização falhou ou pulada. Tente manualmente: quarto render paper.qmd --to pdf")

    elapsed_total = time.time() - t_total
    logger.info("─" * 50)
    logger.info("Pipeline concluído em %.1fs", elapsed_total)


if __name__ == "__main__":
    main()
