#!/usr/bin/env bash
# One-command setup. Safe to re-run any time (it only does what's missing).
#
#   ./setup.sh            everything: CAD venv, browser viewer, F3D renderer, git hook, smoke test
#   ./setup.sh --minimal  just the CAD venv + git hook + smoke test
#
# Uses uv (https://docs.astral.sh/uv/) so it can fetch the right Python (3.12)
# by itself -- whatever python3 your system has doesn't matter.
set -euo pipefail
cd "$(dirname "$0")"

PY_VERSION="$(cat .python-version)"
MINIMAL=0
[[ "${1:-}" == "--minimal" ]] && MINIMAL=1

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[32mok\033[0m %s\n' "$*"; }
warn() { printf '    \033[33m!!\033[0m %s\n' "$*"; }

have() { command -v "$1" >/dev/null 2>&1; }

# --- 1. uv -------------------------------------------------------------------
step "uv (Python + package manager)"
if ! have uv; then
  if have brew; then
    brew install uv
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi
ok "$(uv --version)"

# --- 2. CAD venv -------------------------------------------------------------
step "CAD environment (./venv, Python $PY_VERSION, build123d)"
[[ -x venv/bin/python ]] || uv venv venv --python "$PY_VERSION"
uv pip install --quiet --python venv/bin/python -r requirements.txt
ok "$(venv/bin/python -c 'import build123d; print("build123d", build123d.__version__)')"

# --- 3. Extras: standalone viewer + F3D --------------------------------------
if [[ $MINIMAL == 0 ]]; then
  step "Browser viewer (./.viewer-venv, for scripts/view.py)"
  [[ -x .viewer-venv/bin/python ]] || uv venv .viewer-venv --python "$PY_VERSION"
  uv pip install --quiet --python .viewer-venv/bin/python -r requirements-viewer.txt
  .viewer-venv/bin/python -c "import ocp_viewer" && ok "ocp_viewer"

  step "F3D (headless PNG renders, for scripts/render.py)"
  if have f3d; then
    ok "$(f3d --version 2>/dev/null | head -1)"
  elif have brew; then
    brew install f3d && ok "f3d installed"
  else
    warn "install F3D yourself (https://f3d.app/ or your package manager); render.py needs it"
  fi
fi

# --- 4. git + pre-commit hook ------------------------------------------------
step "git pre-commit hook (re-checks touched parts before each commit)"
[[ -d .git ]] || git init -q -b main
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
ok "core.hooksPath = .githooks"

# --- 5. Smoke test -----------------------------------------------------------
step "Smoke test: build every part and assembly headless"
venv/bin/python scripts/build_all.py

cat <<'EOF'

All set. Try:

  ./venv/bin/python scripts/view.py shovel_mount     # example part in a browser tab
  ./venv/bin/python scripts/render.py shovel_mount   # PNGs in exports/
  ./venv/bin/python scripts/new.py part my_part      # start your own

First, set your printer's bed size in common/printer.py.
Using Claude Code? Open it in this folder and describe the part you want --
CLAUDE.md teaches it the workflow.
EOF
