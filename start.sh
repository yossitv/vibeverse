#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_DIR="$ROOT_DIR/mcp"
VENV_DIR="$ROOT_DIR/.venv"
ENV_FILE="$ROOT_DIR/.env"
SESSION="vibeverse"

# ---------- Colors ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[vibeverse]${NC} $*"; }
ok()   { echo -e "${GREEN}[vibeverse]${NC} $*"; }
err()  { echo -e "${RED}[vibeverse]${NC} $*" >&2; }

# ---------- Preflight checks ----------
if ! command -v tmux &>/dev/null; then
  err "tmux is required. Install with: brew install tmux"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  err ".env not found at $ENV_FILE"
  err "Copy the example and fill in your keys:"
  err "  cp .env.example .env"
  exit 1
fi

# ---------- Virtual environment ----------
if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q -r "$MCP_DIR/requirements.txt"
fi

PYTHON="$VENV_DIR/bin/python"

# ---------- Kill existing session if any ----------
if tmux has-session -t "$SESSION" 2>/dev/null; then
  log "Killing existing '$SESSION' session..."
  tmux kill-session -t "$SESSION"
fi

# ---------- Build env export string for tmux ----------
ENV_EXPORT="set -a; source $ENV_FILE; set +a"

# ---------- Create tmux session with backend ----------
log "Starting tmux session '$SESSION'..."

tmux new-session -d -s "$SESSION" -n backend \
  "$ENV_EXPORT; cd $ROOT_DIR; $PYTHON -m backend.api.server --host 127.0.0.1 --port 8000; read"

# ---------- Add MCP window ----------
tmux new-window -t "$SESSION" -n mcp \
  "$ENV_EXPORT; cd $MCP_DIR; $PYTHON -c \"from server import mcp; mcp.run(transport='http', host='127.0.0.1', port=8001)\"; read"

# ---------- Done ----------
ok "========================================="
ok "  tmux session : $SESSION"
ok "  backend      : http://127.0.0.1:8000  (window 0)"
ok "  mcp          : http://127.0.0.1:8001  (window 1)"
ok "========================================="
ok ""
ok "Commands:"
ok "  tmux attach -t $SESSION        # attach to session"
ok "  tmux select-window -t ${SESSION}:backend  # switch to backend"
ok "  tmux select-window -t ${SESSION}:mcp      # switch to mcp"
ok "  tmux kill-session -t $SESSION  # stop all"
