#!/usr/bin/env bash
# bundle_for_sonic.sh — Create a deployment tarball for SONiC transfer.
#
# Usage:
#   ./scripts/bundle_for_sonic.sh
#
# Produces: sonic-gateway-bundle.tar.gz in the repo root.
#
# The bundle excludes venv, __pycache__, and git metadata.
# Dependencies must be installed on SONiC via pip (see setup_on_sonic.sh).

set -euo pipefail

cd "$(dirname "$0")/.."

BUNDLE="sonic-gateway-bundle.tar.gz"

echo "Creating deployment bundle: ${BUNDLE}"

tar czf "${BUNDLE}" \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='data' \
    --exclude="${BUNDLE}" \
    app/ \
    fixtures/ \
    pyproject.toml \
    .env.sonic.example \
    scripts/setup_on_sonic.sh

echo ""
echo "Bundle created: ${BUNDLE}"
echo "Size: $(du -h ${BUNDLE} | cut -f1)"
echo ""
echo "Transfer to SONiC:"
echo "  scp ${BUNDLE} admin@<sonic-ip>:/tmp/"
echo ""
echo "Then on SONiC:"
echo "  sudo mkdir -p /usr/lib/sonic-openconfig-diagnostic-gateway"
echo "  sudo tar xzf /tmp/${BUNDLE} -C /usr/lib/sonic-openconfig-diagnostic-gateway"
echo "  cd /usr/lib/sonic-openconfig-diagnostic-gateway"
echo "  bash scripts/setup_on_sonic.sh"
