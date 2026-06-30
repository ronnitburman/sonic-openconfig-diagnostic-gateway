# Reference copy — copy this file to sonic-buildimage/rules/ before building.
# See docs/plans/phase-10-sonic-image-bake.md for full build instructions.

SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_VERSION = 0.1.0
SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64 = sonic-openconfig-diagnostic-gateway_$(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_VERSION)_amd64.deb

# For local builds: use file:// to reference the .deb in src/
$(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)_URL = \
    file:///sonic-buildimage/src/sonic-openconfig-diagnostic-gateway/$(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)

# For release builds: use https:// to download from GitHub releases
# $(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)_URL = \
#     https://github.com/your-org/sonic-openconfig-diagnostic-gateway/releases/download/v$(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_VERSION)/$(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)

# Register the package for all supported Debian distros
SONIC_STRETCH_DEBS += $(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)
SONIC_BUSTER_DEBS += $(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)
SONIC_BULLSEYE_DEBS += $(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)
SONIC_BOOKWORM_DEBS += $(SONIC_OPENCONFIG_DIAGNOSTIC_GATEWAY_AMD64)
