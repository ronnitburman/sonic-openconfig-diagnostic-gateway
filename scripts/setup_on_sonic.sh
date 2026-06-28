#!/usr/bin/env bash
# setup_on_sonic.sh — Install and configure the gateway on a SONiC device.
#
# Run AFTER extracting the bundle tarball into the target directory:
#   cd /usr/lib/sonic-openconfig-diagnostic-gateway
#   bash scripts/setup_on_sonic.sh
#
# This script:
#   1. Checks Python 3 availability
#   2. Creates a Python virtual environment
#   3. Installs Python dependencies
#   4. Copies .env.sonic.example → .env (if no .env exists)
#   5. Creates the audit log directory
#   6. Prints instructions for starting the service

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${APP_DIR}/venv"
ENV_FILE="${APP_DIR}/.env"
AUDIT_DIR="/var/log/sonic-openconfig-diagnostic-gateway"

echo "============================================================"
echo " SONiC OpenConfig Diagnostic Gateway — Setup"
echo "============================================================"
echo ""
echo "Target directory: ${APP_DIR}"
echo ""

# ── 1. Check Python ──────────────────────────────────────────────
echo -n "Checking Python... "
PYTHON=""
for candidate in python3 python3.9 python3.10 python3.11 python3.12 python3.13; do
    if command -v "${candidate}" &>/dev/null; then
        PYVER=$("${candidate}" --version 2>&1)
        echo -e "${GREEN}${PYVER}${RESET}"
        PYTHON="${candidate}"
        break
    fi
done

if [ -z "${PYTHON}" ]; then
    echo -e "${RED}Python 3 not found. Install with: sudo apt-get install python3${RESET}"
    exit 1
fi

# ── 2. Create virtual environment ─────────────────────────────────
echo -n "Creating virtual environment... "
if [ -d "${VENV_DIR}" ]; then
    echo -e "${YELLOW}already exists — skipping${RESET}"
else
    ${PYTHON} -m venv "${VENV_DIR}"
    echo -e "${GREEN}done${RESET}"
fi

# Activate for the rest of this script
source "${VENV_DIR}/bin/activate"

# ── 3. Install dependencies ───────────────────────────────────────
echo "Installing Python dependencies..."
pip install --upgrade pip -q 2>/dev/null || true

# Install from pyproject.toml if it exists, otherwise try requirements.txt
if [ -f "${APP_DIR}/pyproject.toml" ]; then
    pip install -e "${APP_DIR}" 2>&1 | tail -3
elif [ -f "${APP_DIR}/requirements.txt" ]; then
    pip install -r "${APP_DIR}/requirements.txt" 2>&1 | tail -3
else
    echo -e "${YELLOW}No pyproject.toml or requirements.txt found. Skipping pip install.${RESET}"
fi

# ── 4. Configure environment ──────────────────────────────────────
echo ""
if [ -f "${ENV_FILE}" ]; then
    echo -e "${YELLOW}.env already exists — not overwriting${RESET}"
else
    if [ -f "${APP_DIR}/.env.sonic.example" ]; then
        cp "${APP_DIR}/.env.sonic.example" "${ENV_FILE}"
        echo -e "${GREEN}.env created from .env.sonic.example${RESET}"
        echo -e "${YELLOW}→ Edit ${ENV_FILE} to set GNMI_HOST, GNMI_USERNAME, GNMI_PASSWORD${RESET}"
    else
        echo -e "${RED}.env.sonic.example not found — create .env manually${RESET}"
    fi
fi

# ── 5. Create audit log directory ─────────────────────────────────
echo -n "Creating audit log directory... "
sudo mkdir -p "${AUDIT_DIR}" 2>/dev/null || {
    echo -e "${YELLOW}could not create ${AUDIT_DIR} (may need sudo)${RESET}"
    echo -n "  → using local: "
    mkdir -p "${APP_DIR}/data"
    echo -e "${YELLOW}${APP_DIR}/data${RESET}"
}
echo -e "${GREEN}${AUDIT_DIR}${RESET}"

# ── 6. Verify installation ────────────────────────────────────────
echo ""
echo "============================================================"
echo " Verifying installation"
echo "============================================================"
echo ""

echo -n "FastAPI version: "
python -c "import fastapi; print(fastapi.__version__)" 2>/dev/null || echo "NOT INSTALLED"

echo -n "uvicorn version: "
python -c "import uvicorn; print(uvicorn.__version__)" 2>/dev/null || echo "NOT INSTALLED"

echo -n "Device mode: "
python -c "from app.config import settings; print(settings.device_mode)" 2>/dev/null || echo "ERROR loading config"

echo -n "gNMI host: "
python -c "from app.config import settings; print(settings.gnmi_host or '(not set)')" 2>/dev/null || echo "ERROR"

echo ""

# ── 7. Start instructions ────────────────────────────────────────
echo "============================================================"
echo " Setup complete!"
echo "============================================================"
echo ""
echo "To start the service:"
echo ""
echo -e "  ${BOLD}cd ${APP_DIR}${RESET}"
echo -e "  ${BOLD}source venv/bin/activate${RESET}"
echo -e "  ${BOLD}uvicorn app.main:app --host 0.0.0.0 --port 8080${RESET}"
echo ""
echo "Then verify from another host:"
echo ""
echo -e "  ${BOLD}curl http://<sonic-ip>:8080/health${RESET}"
echo ""
echo -e "${YELLOW}Note: Edit .env to set DEVICE_MODE=live and configure sandbox credentials.${RESET}"
echo ""
