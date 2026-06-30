#!/usr/bin/env bash
# build_deb.sh — Build the Debian package for SONiC deployment.
#
# Usage:
#   ./scripts/build_deb.sh
#
# Produces: sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb
#
# The package installs to:
#   /usr/lib/sonic-openconfig-diagnostic-gateway/  (application code + fixtures)
#   /etc/sonic-openconfig-diagnostic-gateway/       (environment config template)
#   /lib/systemd/system/                            (systemd unit file)
#   /var/log/sonic-openconfig-diagnostic-gateway/   (audit log directory)
#
# Python dependencies are installed in postinst on the target SONiC,
# NOT bundled in the package (ensures binary compatibility).

set -euo pipefail

# Resolve the repo root regardless of where the script is invoked from
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PACKAGE="sonic-openconfig-diagnostic-gateway"
VERSION="0.1.0"
ARCH="amd64"
DEB_NAME="${PACKAGE}_${VERSION}_${ARCH}.deb"

STAGING="packaging/debian"
APP_STAGING="${STAGING}/usr/lib/sonic-openconfig-diagnostic-gateway"

echo "============================================================"
echo " Building ${DEB_NAME}"
echo "============================================================"
echo ""

# ── 1. Clean previous build ──────────────────────────────────────
echo "Cleaning previous build..."
rm -rf "${APP_STAGING}"
rm -f "${DEB_NAME}"

# ── 2. Create staging directories ─────────────────────────────────
echo "Creating staging directories..."
mkdir -p "${APP_STAGING}"

# ── 3. Copy application code ──────────────────────────────────────
echo "Copying application code..."
cp -r app          "${APP_STAGING}/"
cp -r fixtures     "${APP_STAGING}/"
cp pyproject.toml  "${APP_STAGING}/"
cp .env.sonic.example "${APP_STAGING}/"

# ── 3b. Bundle gnmic binary for the target architecture ──────────
echo "Bundling gnmic CLI..."
GNMIC_VERSION="0.46.0"
GNMIC_DIR="${STAGING}/usr/local/bin"
mkdir -p "${GNMIC_DIR}"

# Download gnmic for linux/amd64 (matches Architecture: amd64 in control)
GNMIC_URL="https://github.com/openconfig/gnmic/releases/download/v${GNMIC_VERSION}/gnmic_${GNMIC_VERSION}_Linux_x86_64.tar.gz"
if curl -fSL "${GNMIC_URL}" 2>/dev/null | tar xz -C "${GNMIC_DIR}" --strip-components=1 gnmic 2>/dev/null; then
    chmod +x "${GNMIC_DIR}/gnmic"
    echo "  gnmic ${GNMIC_VERSION} bundled"
else
    echo "  WARNING: Could not download gnmic — it must be installed manually on the target"
fi

# Copy helper scripts (optional)
mkdir -p "${APP_STAGING}/scripts"
if [ -f scripts/sonic_ctl.sh ]; then
    cp scripts/sonic_ctl.sh "${APP_STAGING}/scripts/"
    chmod +x "${APP_STAGING}/scripts/sonic_ctl.sh"
fi

# ── 4. Clean up dev-only files from staging ───────────────────────
echo "Cleaning dev artifacts from staging..."
find "${APP_STAGING}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${APP_STAGING}" -type f -name '*.pyc' -delete 2>/dev/null || true

# ── 5. Ensure systemd unit is in staging ──────────────────────────
echo "Ensuring systemd unit file..."
SYSTEMD_SRC="packaging/systemd/sonic-openconfig-diagnostic-gateway.service"
SYSTEMD_DST="${STAGING}/lib/systemd/system/sonic-openconfig-diagnostic-gateway.service"
if [ ! -f "${SYSTEMD_DST}" ]; then
    if [ -f "${SYSTEMD_SRC}" ]; then
        cp "${SYSTEMD_SRC}" "${SYSTEMD_DST}"
    else
        echo "ERROR: Systemd unit file not found at ${SYSTEMD_SRC}"
        exit 1
    fi
fi

# ── 6. Verify DEBIAN scripts are executable ───────────────────────
chmod +x "${STAGING}/DEBIAN/postinst" 2>/dev/null || true
chmod +x "${STAGING}/DEBIAN/prerm"   2>/dev/null || true

# ── 7. Build the .deb ─────────────────────────────────────────────
echo ""
echo "Building .deb package..."
dpkg-deb --build "${STAGING}" "${DEB_NAME}"

# ── 8. Report ─────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Package built successfully!"
echo "============================================================"
echo ""
echo "  ${DEB_NAME}  ($(du -h ${DEB_NAME} | cut -f1))"
echo ""
echo "Verify contents:"
echo "  dpkg-deb --info ${DEB_NAME}"
echo "  dpkg-deb --contents ${DEB_NAME}"
echo ""
echo "Install on SONiC:"
echo "  scp ${DEB_NAME} admin@<sonic-ip>:/tmp/"
echo "  ssh admin@<sonic-ip> 'sudo dpkg -i /tmp/${DEB_NAME}'"
echo ""
