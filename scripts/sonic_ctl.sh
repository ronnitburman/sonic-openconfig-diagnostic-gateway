#!/bin/bash
# sonic_ctl.sh — Control script for SONiC OpenConfig Diagnostic Gateway.
#
# Installed to /usr/lib/sonic-openconfig-diagnostic-gateway/scripts/
#
# Usage:
#   sonic_ctl.sh status      Show service status
#   sonic_ctl.sh start       Start the service
#   sonic_ctl.sh stop        Stop the service
#   sonic_ctl.sh restart     Restart the service
#   sonic_ctl.sh logs        Follow service logs (journalctl -f)
#   sonic_ctl.sh health      Quick health check (curl localhost:8080)
#   sonic_ctl.sh config      Edit the environment file

set -e

SERVICE="sonic-openconfig-diagnostic-gateway"
ENV_FILE="/etc/sonic-openconfig-diagnostic-gateway/gateway.env"

usage() {
    echo "Usage: $(basename "$0") {status|start|stop|restart|logs|health|config}"
    echo ""
    echo "  status    Show systemd service status"
    echo "  start     Start the service"
    echo "  stop      Stop the service"
    echo "  restart   Restart the service"
    echo "  logs      Follow live logs (journalctl -f)"
    echo "  health    Quick health check (GET /health)"
    echo "  config    Edit the environment file"
    exit 1
}

case "${1:-}" in
    status)
        systemctl status "${SERVICE}"
        ;;
    start)
        systemctl start "${SERVICE}"
        echo "Service started."
        ;;
    stop)
        systemctl stop "${SERVICE}"
        echo "Service stopped."
        ;;
    restart)
        systemctl restart "${SERVICE}"
        echo "Service restarted."
        ;;
    logs)
        journalctl -u "${SERVICE}" -f
        ;;
    health)
        echo -n "Health check: "
        curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || \
            echo "FAILED — is the service running?"
        ;;
    config)
        if [ -f "${ENV_FILE}" ]; then
            ${EDITOR:-vi} "${ENV_FILE}"
            echo ""
            echo "Configuration edited. Restart to apply changes:"
            echo "  sudo systemctl restart ${SERVICE}"
        else
            echo "Environment file not found: ${ENV_FILE}"
            exit 1
        fi
        ;;
    *)
        usage
        ;;
esac
