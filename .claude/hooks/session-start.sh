#!/bin/bash
# Início de sessão: liga a trava do push deste clone (scripts/ganchos/pre-push roda a verificação antes de qualquer push para o main).
# O site não tem dependências de pacotes: só python3 (gerador e verificação) e node (conferência do JavaScript).
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
if [ -f scripts/ganchos/pre-push ] && [ "$(git config --get core.hooksPath 2>/dev/null)" != "scripts/ganchos" ]; then
  git config core.hooksPath scripts/ganchos 2>/dev/null || echo "aviso: não consegui ligar a trava do push (rode: git config core.hooksPath scripts/ganchos)" >&2
fi
command -v python3 >/dev/null 2>&1 || echo "aviso: python3 ausente (o gerador e a verificação não rodam)" >&2
exit 0
