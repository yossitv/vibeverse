#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_DIR="$ROOT_DIR/mcp"
VENV_DIR="$ROOT_DIR/.venv"
ENV_FILE="$ROOT_DIR/.env"

# ---------- Colors ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log()  { echo -e "${CYAN}[vibeverse]${NC} $*"; }
ok()   { echo -e "${GREEN}[vibeverse]${NC} $*"; }
err()  { echo -e "${RED}[vibeverse]${NC} $*" >&2; }

# ---------- Preflight checks ----------
if [ ! -f "$ENV_FILE" ]; then
  err ".env not found at $ENV_FILE"
  err "Copy the example and fill in your keys:"
  err "  cp .env.example .env"
  exit 1
fi

# Export .env so both backend and MCP pick up the keys
set -a
source "$ENV_FILE"
set +a

# ---------- Virtual environment ----------
if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q -r "$MCP_DIR/requirements.txt"
fi

PYTHON="$VENV_DIR/bin/python"

# ---------- Cleanup on exit ----------
PIDS=()
cleanup() {
  log "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  ok "All services stopped."
}
trap cleanup EXIT INT TERM

# ---------- Start Backend API ----------
log "Starting backend API on http://127.0.0.1:8000 ..."
cd "$ROOT_DIR"
$PYTHON -m backend.api.server --host 127.0.0.1 --port 8000 &
PIDS+=($!)

# ---------- Start MCP Server (HTTP) ----------
log "Starting MCP server on http://127.0.0.1:8001 ..."
cd "$MCP_DIR"
$PYTHON -c "
from server import mcp
mcp.run(transport='http', host='127.0.0.1', port=8001)
" &
PIDS+=($!)

# ---------- Ready ----------
sleep 1
ok "========================================="
ok "  Backend API : http://127.0.0.1:8000"
ok "  MCP Server  : http://127.0.0.1:8001"
ok "========================================="
ok "Press Ctrl+C to stop all services."

wait
