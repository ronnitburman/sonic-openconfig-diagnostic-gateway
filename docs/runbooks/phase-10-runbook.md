# Phase 10 Runbook

## Prerequisites

- Phase 9 complete (valid `.deb` built and tested via manual install).
- EC2 instance (or Linux VM) with ≥100 GB disk, ≥16 GB RAM, Docker installed.
- `dpkg-dev` installed (`sudo apt-get install -y dpkg-dev`).
- Internet access for cloning `sonic-buildimage` and pulling Docker images.

> **Important:** SONiC builds happen inside Linux Docker containers and consume significant disk. Your Mac is the *control plane* — all build commands run on EC2.

---

## 0. EC2 Instance Setup

### Instance type

| Requirement | Recommended | Minimum |
|---|---|---|
| vCPU | 8 | 4 |
| RAM | 16 GB | 8 GB |
| Disk (EBS) | **100 GB gp3** | 50 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 20.04 LTS |

**Recommended:** `c5.2xlarge` (8 vCPU, 16 GB) or `m5.2xlarge`. Budget option: `t3.xlarge` with burst credits.

> **Disk is critical.** A full SONiC VS build with Docker images consumes 40–60 GB. If EBS fills up, the build fails mid-way. Use gp3 with at least 100 GB.

### Launch and connect

```bash
# Fix key permissions (required by SSH)
chmod 600 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

### Use tmux for long-running commands

EC2 SSH sessions can drop. Start a `tmux` session so builds survive disconnects:

```bash
# Start a named session
tmux new -s sonic

# Run your long command inside tmux (e.g. make init, make target/...)
make init

# Detach (leave running in background): press Ctrl+B, then D

# If disconnected, reattach:
ssh -i your-key.pem ubuntu@<ec2-public-ip>
tmux attach -t sonic
```

| Action | Command |
|---|---|
| New session | `tmux new -s name` |
| Detach | `Ctrl+B` then `D` |
| Reattach | `tmux attach -t name` |
| List sessions | `tmux ls` |
| Scroll up | `Ctrl+B` then `[` (arrows to scroll, `q` to quit) |

### Install build dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    docker.io \
    dpkg-dev \
    git \
    make \
    python3 \
    python3-pip

# Add ubuntu user to docker group (avoids sudo for every docker command)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker ps
# Should show no containers but no permission error
```

> **Next:** After dependencies are installed, go to **Step 2** to clone `sonic-buildimage` and run `make init`. This pulls Docker images and git submodules (~30-60 minutes on first run, run inside `tmux`).

### (Optional) QEMU/KVM for testing the built image

If you want to boot the SONiC VS image on the same EC2 instance to verify:

```bash
# Only works on bare-metal instances (.metal) or instances with nested virt:
# - c5.metal, m5.metal, i3.metal
# Standard virtualized EC2 instances do NOT support KVM.
# Alternative: download the image and boot locally, or test on a separate
# physical machine with QEMU installed.

# If on a metal instance:
sudo apt-get install -y qemu-kvm
kvm-ok  # Should say "KVM acceleration can be used"
```

> **If you can't run QEMU on EC2:** Build the image on EC2, then `scp` the resulting `target/sonic-vs.img.gz` back to your Mac or a machine with QEMU/KVM support for boot testing. The *build* happens on EC2; the *boot test* can be done elsewhere.

### Transfer the project to EC2

```bash
# From your Mac — scp the gateware repo (exclude venv, it's 50MB+)
cd sonic-openconfig-diagnostic-gateway
tar czf gateway-repo.tar.gz \
    --exclude='.venv' --exclude='venv' --exclude='__pycache__' \
    --exclude='.git' --exclude='*.deb' \
    app/ fixtures/ scripts/ packaging/ pyproject.toml .env.sonic.example

scp -i your-key.pem gateway-repo.tar.gz ubuntu@<ec2-ip>:~/

# On EC2
tar xzf gateway-repo.tar.gz
# Produces: app/ fixtures/ scripts/ packaging/ pyproject.toml .env.sonic.example
```

---

## 1. Build the .deb (on EC2)

```bash
# Using the extracted tarball from Step 0
cd ~
bash scripts/build_deb.sh
# → sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb (25KB)

# If dpkg-deb is missing:
sudo apt-get install -y dpkg-dev
bash scripts/build_deb.sh
```

---

## 2. Set Up sonic-buildimage (on EC2)

> **Run inside `tmux`** — this takes 30-60 minutes and your SSH session may drop.

```bash
cd ~
git clone https://github.com/sonic-net/sonic-buildimage.git
cd sonic-buildimage
git checkout 202405  # stable branch as of mid-2025

# Pulls Docker images and git submodules (~30-60 minutes)
make init
```

> **If `make init` fails with disk space:** Check `df -h`. You need at least 60 GB free. Docker images are large. Consider attaching a second EBS volume mounted at `/var/lib/docker`.

---

## 3. Add the Gateway Package (on EC2)

```bash
# Still in ~/sonic-buildimage

# Copy the .deb from the extracted project
mkdir -p src/sonic-openconfig-diagnostic-gateway
cp ~/sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb \
   src/sonic-openconfig-diagnostic-gateway/

# Copy the build rule file
cp ~/packaging/sonic-buildimage/sonic-openconfig-diagnostic-gateway.mk \
   rules/

# Verify
ls src/sonic-openconfig-diagnostic-gateway/
# → sonic-openconfig-diagnostic-gateway_0.1.0_amd64.deb

ls rules/sonic-openconfig-diagnostic-gateway.mk
# → rules/sonic-openconfig-diagnostic-gateway.mk
```

---

## 4. Configure the Build (Optional)

For faster builds, disable features you don't need:

```bash
export ENABLE_SYNCD_RPC=n
export ENABLE_DHCP_GRAPH_SERVICE=n
export ENABLE_PFCWD=n
export ENABLE_NAT=n
export INSTALL_DEBUG_TOOLS=n
```

---

## 5. Build the Image

```bash
# Virtual Switch (VS) platform — fastest, for testing
export PLATFORM=vs
make target/sonic-vs.img.gz

# For Broadcom hardware
# export PLATFORM=broadcom
# make target/sonic-broadcom.bin
```

**First build:** 2–4 hours. Subsequent builds with the same platform: ~30 min (cached).

---

## 6. Verify the Image

```bash
# Check the image was produced
ls -lh target/sonic-vs.img.gz

# Verify our package is in the image's package pool
ls target/debs/bullseye/sonic-openconfig-diagnostic-gateway_*.deb
```

---

## 7. Boot the Image in QEMU (on a KVM-capable machine)

> **EC2 limitation:** Standard virtualized EC2 instances (c5, m5, t3) do NOT support nested KVM.
> You have three options:
>
> **Option A — Bare-metal EC2:** Launch a `.metal` instance (c5.metal, m5.metal) with KVM support.
>
> **Option B — Download and boot locally:** `scp target/sonic-vs.img.gz` back to your
> Mac or a Linux machine with QEMU/KVM. The build happens on EC2; the boot test happens
> wherever QEMU runs.
>
> **Option C — Skip QEMU boot test:** Verify the package is in the image via
> `dpkg-deb --contents` (Step 6), then deploy directly to physical hardware.

### Option B — Download to a machine with QEMU

```bash
# From your Mac or Linux machine with QEMU:
scp -i your-key.pem ubuntu@<ec2-ip>:~/sonic-buildimage/target/sonic-vs.img.gz ./

# Install QEMU if not present
# macOS:
#   brew install qemu
# Linux:
#   sudo apt-get install -y qemu-kvm

# Boot the VS image
# macOS (no KVM, uses emulation — slower but works):
qemu-system-x86_64 -m 4096 -smp 2 \
  -drive file=sonic-vs.img.gz,if=virtio \
  -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
  -nographic

# Linux with KVM (fast):
sudo kvm -m 4096 -smp 2 \
  -drive file=sonic-vs.img.gz,if=virtio \
  -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
  -nographic
```

Login:
```
Username: admin
Password: YourPaSsWoRd
```

---

## 8. Verify Pre-Installed Gateway

```bash
# Check package installed
dpkg -l sonic-openconfig-diagnostic-gateway
# Expected: ii  sonic-openconfig-diagnostic-gateway  0.1.0  amd64

# Check all files
dpkg -L sonic-openconfig-diagnostic-gateway

# Check systemd service enabled
systemctl status sonic-openconfig-diagnostic-gateway
# Expected: Loaded: loaded (...; enabled)
#           Active: inactive (dead) — not started until configured

# Check venv exists
ls /usr/lib/sonic-openconfig-diagnostic-gateway/venv/bin/python

# Check fixtures
ls /usr/lib/sonic-openconfig-diagnostic-gateway/fixtures/capabilities/
```

---

## 9. Configure and Start

```bash
# Edit environment file with your settings
sudo vi /etc/sonic-openconfig-diagnostic-gateway/gateway.env
# Set at minimum: DEVICE_MODE=fixture (or live with sandbox credentials)

# Start the service
sudo systemctl start sonic-openconfig-diagnostic-gateway

# Verify
curl http://localhost:8080/health
# {"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}

# Test a diagnostic
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "GigabitEthernet0/0"}' \
  | python3 -m json.tool
```

---

## 10. Test Reboot Persistence

```bash
sudo reboot

# After SONiC comes back
ssh admin@<sonic-ip>

# Service should be running
systemctl status sonic-openconfig-diagnostic-gateway
# Active: active (running)

curl http://localhost:8080/health
# {"status":"ok",...}
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| `make init` fails | Docker not running or permissions. `sudo usermod -aG docker $USER` |
| Build fails with "deb not found" | Wrong filename in `.mk`. Verify: `ls src/sonic-openconfig-diagnostic-gateway/` |
| Package not in image | Rule file not in `rules/`. Check `make` output for our package name |
| Service not enabled after boot | postinst may have failed silently. Check Docker build logs |
| `pip install` fails during image build | Docker container has no internet. Use `file://` URL and build venv in `.deb` instead |
| QEMU boot hangs | Increase memory: `-m 8192`. Check image format matches QEMU expectations |

---

## Physical Hardware (Beyond VS)

For actual switch deployment:

```bash
# Broadcom switches
export PLATFORM=broadcom
make target/sonic-broadcom.bin

# Install via ONIE
onie-nos-install http://<tftp-server>/sonic-broadcom.bin
```

Install ONIE is vendor-specific. Refer to your switch vendor's ONIE documentation.

---

## Definition of Done

- [x] Image built: `target/sonic-vs.img.gz` exists.
- [x] Image boots in QEMU successfully.
- [x] Gateway package pre-installed: `dpkg -l` shows `ii`.
- [x] systemd service enabled at boot.
- [x] Service starts after configuring `.env`.
- [x] `curl localhost:8080/health` returns 200.
- [x] Service survives reboot.
