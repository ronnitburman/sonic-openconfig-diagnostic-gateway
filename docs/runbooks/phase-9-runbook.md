# Phase 9 Runbook

## Prerequisites

- Phase 8 complete (application structure ready for packaging).
- `dpkg-deb` available (`brew install dpkg` on macOS, or native on Linux).
- Target SONiC device accessible via SSH.

---

## Build the Debian Package

```bash
cd sonic-openconfig-diagnostic-gateway

# Build the .deb
bash scripts/build_deb.sh
```

Output:
```
Building sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb...
✓ Package created: sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb
```

---

## Verify Package Contents

```bash
# Check metadata
dpkg-deb --info sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb

# Check file listing
dpkg-deb --contents sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb

# Check control scripts
dpkg-deb --control sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb
```

Expected contents:
```
/usr/lib/sonic-openconfig-diagnostic-gateway/app/
/usr/lib/sonic-openconfig-diagnostic-gateway/fixtures/
/usr/lib/sonic-openconfig-diagnostic-gateway/pyproject.toml
/etc/sonic-openconfig-diagnostic-gateway/gateway.env
/lib/systemd/system/sonic-openconfig-diagnostic-gateway.service
/var/log/sonic-openconfig-diagnostic-gateway/
```

---

## Transfer and Install on SONiC

### Transfer

```bash
scp sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb admin@<sonic-ip>:/tmp/
```

### Install

```bash
# On SONiC
sudo dpkg -i /tmp/sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb

# If dependency errors:
sudo apt-get install -f
```

**During install, postinst will:**
1. Create `/var/log/sonic-openconfig-diagnostic-gateway/` with proper permissions.
2. Create the Python virtual environment at `/usr/lib/sonic-openconfig-diagnostic-gateway/venv/`.
3. Install Python dependencies from `pyproject.toml`.
4. Run `systemctl daemon-reload` and `systemctl enable`.
5. Print configuration instructions.

---

## Configure Credentials

```bash
# On SONiC — edit the environment file
sudo vi /etc/sonic-openconfig-diagnostic-gateway/gateway.env
```

Set real values:
```dotenv
DEVICE_MODE=live
GNMI_HOST=<sandbox-ip>
GNMI_USERNAME=<sandbox-username>
GNMI_PASSWORD=<sandbox-password>
GNMI_INSECURE=true
```

Secure the file:
```bash
sudo chmod 600 /etc/sonic-openconfig-diagnostic-gateway/gateway.env
```

---

## Start and Verify

```bash
# Start the service
sudo systemctl start sonic-openconfig-diagnostic-gateway

# Check status
sudo systemctl status sonic-openconfig-diagnostic-gateway
# ● sonic-openconfig-diagnostic-gateway.service - SONiC OpenConfig Diagnostic Gateway
#    Loaded: loaded (/lib/systemd/system/sonic-openconfig-diagnostic-gateway.service; enabled)
#    Active: active (running)

# View live logs
sudo journalctl -u sonic-openconfig-diagnostic-gateway -f

# Health check
curl http://localhost:8080/health
# {"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}

# Full diagnostic test (fixture mode)
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0"
  }' | python3 -m json.tool
```

---

## Verify Auto-Start on Reboot

```bash
# On SONiC
sudo reboot

# After SONiC comes back — re-SSH
ssh admin@<sonic-ip>

# Service should already be running
sudo systemctl status sonic-openconfig-diagnostic-gateway
# Active: active (running) since <boot-time>

curl http://localhost:8080/health
# {"status":"ok",...}
```

If the service didn't start:
```bash
# Check boot-time logs
sudo journalctl -u sonic-openconfig-diagnostic-gateway -b

# Common cause: network wasn't ready fast enough
# Fix: add RestartSec=10 to unit file, or check network-online.target
```

---

## Service Control Commands

```bash
# Using systemctl directly
sudo systemctl start sonic-openconfig-diagnostic-gateway
sudo systemctl stop sonic-openconfig-diagnostic-gateway
sudo systemctl restart sonic-openconfig-diagnostic-gateway
sudo systemctl status sonic-openconfig-diagnostic-gateway

# Or use the helper script
sudo /usr/lib/sonic-openconfig-diagnostic-gateway/scripts/sonic_ctl.sh status
sudo /usr/lib/sonic-openconfig-diagnostic-gateway/scripts/sonic_ctl.sh restart
sudo /usr/lib/sonic-openconfig-diagnostic-gateway/scripts/sonic_ctl.sh logs
sudo /usr/lib/sonic-openconfig-diagnostic-gateway/scripts/sonic_ctl.sh health
```

---

## Viewing Logs

```bash
# Follow live logs
sudo journalctl -u sonic-openconfig-diagnostic-gateway -f

# Last 50 lines
sudo journalctl -u sonic-openconfig-diagnostic-gateway -n 50

# Logs since last boot
sudo journalctl -u sonic-openconfig-diagnostic-gateway -b

# Audit trail (JSON Lines)
cat /var/log/sonic-openconfig-diagnostic-gateway/audit.jsonl | python3 -m json.tool
```

---

## Uninstall

```bash
# Remove package (keeps config files in /etc/)
sudo dpkg -r sonic-openconfig-diagnostic-gateway

# Purge completely (removes config files too)
sudo dpkg -P sonic-openconfig-diagnostic-gateway

# Verify removal
dpkg -l sonic-openconfig-diagnostic-gateway
# Should show: "No packages found"
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Service fails to start | `journalctl -u sonic-openconfig-diagnostic-gateway -n 20` |
| `ModuleNotFoundError: No module named 'fastapi'` | venv not created — re-run `dpkg -i` or manually run `postinst` steps |
| `Address already in use` on port 8080 | Something else on 8080. Change `APP_PORT` in `gateway.env` and restart |
| gNMI unreachable in live mode | Sandbox IP wrong or port blocked. Test: `nc -zv <sandbox> 50052` |
| Service works but dies after hours | Check memory limits. Add `MemoryMax=256M` to unit file if needed |
| `curl: (7) Failed to connect` from Mac | Firewall on SONiC. Check `iptables -L` for port 8080 |
| `dpkg` dependency errors | `sudo apt-get install -f` to fix missing deps |
| Audit log not writable | Check permissions: `ls -la /var/log/sonic-openconfig-diagnostic-gateway/` |

---

## Package Management Reference

```bash
# List installed version
dpkg -l sonic-openconfig-diagnostic-gateway

# List all files installed by the package
dpkg -L sonic-openconfig-diagnostic-gateway

# Reconfigure (re-runs postinst)
sudo dpkg-reconfigure sonic-openconfig-diagnostic-gateway

# Upgrade to newer version
sudo dpkg -i sonic-openconfig-diagnostic-gateway_0.2.0_amd64.deb
```
