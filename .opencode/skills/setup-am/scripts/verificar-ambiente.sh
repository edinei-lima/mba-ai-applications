#!/usr/bin/env bash
# Verifica se o ambiente da disciplina AI Applications está pronto.
# Uso: bash scripts/verificar-ambiente.sh

set -u

ok()   { printf "  ✅ %s\n" "$1"; }
falta(){ printf "  ❌ %s\n" "$1"; }

checar() {
  local nome="$1" cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$nome ($("$cmd" --version 2>&1 | head -1))"
  else
    falta "$nome — não encontrado (instale antes de continuar)"
  fi
}

echo "== Ferramentas =="
checar "VS Code"  code
checar "Python"   python3
checar "Quarto"   quarto
checar "Git"      git

echo "== LaTeX (para PDF) =="
if command -v xelatex >/dev/null 2>&1 || [ -d "$HOME/Library/TinyTeX" ] || [ -d "$HOME/.TinyTeX" ]; then
  ok "LaTeX/TinyTeX presente"
else
  falta "LaTeX — rode: quarto install tinytex"
fi

echo "== Ambiente virtual =="
if [ -d ".venv" ]; then ok ".venv existe nesta pasta"; else falta ".venv — rode: python3 -m venv .venv"; fi

echo "== Segredos =="
if [ -f ".env" ]; then ok ".env existe"; else falta ".env — copie de .env.example e preencha"; fi
if [ -f ".gitignore" ] && grep -q "^.env$" .gitignore 2>/dev/null; then
  ok ".env está no .gitignore"
else
  falta ".env NÃO está no .gitignore — adicione antes de commitar"
fi

echo
echo "Dica: rode também 'quarto check' para o diagnóstico completo do Quarto."
