---
type: Playbook
title: Local setup
description: Install the locked dependencies and start a local collector and dashboard against a separate development archive, with optional tunnel and restart task.
resource: ../../scripts/start-local.ps1
tags: [local, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l62
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L62-L126
    title: README.md lines 62-126, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Install and start

Requires Python 3.12 or newer; development and the container use 3.13.
The launcher below starts collection and a dashboard. These are not needed to
operate the deployed cloud services. The example selects a separate local archive
under the ignored `data/` directory so development does not change the cutover
backup or connect to the active cloud archive.

PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -r requirements-build.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
Remove-Item Env:SCJ_BUCKET -ErrorAction SilentlyContinue
$env:SCJ_DATA_DIR = Join-Path (Get-Location) 'data\development'
.\scripts\start-local.ps1 -NoTunnel
```

The archive variables are described in [configuration](../architecture/configuration.md).

# Temporary tunnel

Omit `-NoTunnel` to also start a temporary public tunnel when
`.runtime/cloudflared.exe` is present. This workspace already has the binary.
On a new machine, install `cloudflared` from its official release and put the
executable there, or run a tunnel separately:

```powershell
cloudflared tunnel --url http://127.0.0.1:8050
```

# Automatic restart

Automatic local restart is optional: `scripts/install-local-task.ps1` registers
`SC-Jail-Local`, which runs the launcher every minute while the user is signed in.
It does not save the current shell's `SCJ_DATA_DIR`, `SCJ_BUCKET`, or `-NoTunnel`
choice. Configure the intended archive in the scheduled task's environment before
enabling it. Without archive overrides, its launcher uses `data/` and starts any
available tunnel. Keep this task disabled for the cloud deployment.

# Direct commands

Direct commands also work on Linux/macOS using the environment's Python:

```text
python -m sc_jail collect
python -m sc_jail schedule
python -m sc_jail dashboard --port 8050
python -m sc_jail status
```

The dashboard binds to loopback unless `--host` is explicitly supplied. It has
no collection or file browsing endpoint. Use an OS service to supervise the two
long-running commands on Linux; Cloud Run uses a different request-driven mode.

# Stop and restart

Stop this project's local processes and disable its automatic restart:

```powershell
.\scripts\stop-local.ps1
```

Restart Python after changing code, retaining the tunnel URL and restart task:

```powershell
.\scripts\stop-local.ps1 -KeepTask -KeepTunnel
.\scripts\start-local.ps1
```

Logs and process IDs are in `.runtime/`. The launcher checks process identity
before acting, and shutdown includes the Python children of Windows' venv
launchers.
