#!/usr/bin/env python3
"""
deploy.py - Safe production deployment to the Discord bot VM.

Enforces the rule: BACKUP BEFORE OVERWRITE.
Before any file is transferred, a timestamped backup of the current VM state
is created at C:\\ClashKing\\backups\\backup_YYYYMMDD_HHMMSS\\

Usage:
    python deploy.py                        # Deploy all src + .env + launcher
    python deploy.py src/database.py        # Deploy only specific files
    python deploy.py --backup-only          # Only create a backup, no file transfer
    python deploy.py --rollback             # Restore from latest backup
    python deploy.py --cleanup-backups      # Delete old backups (keep last 5)

Configuration:
    Set environment variables: VM_HOST, VM_USER, VM_PASS
    Or edit the constants below.
"""

import subprocess
import sys
import os
import base64
from datetime import datetime
from pathlib import Path

# VM Configuration
VM_HOST = os.getenv("VM_HOST", "http://WIN-2HBN30ECLV2.fritz.box:5985/wsman")
VM_USER = os.getenv("VM_USER", "administrator")
VM_PASS = os.getenv("VM_PASS", "")
REMOTE_ROOT = "C:\\ClashKing"
BACKUP_BASE = REMOTE_ROOT + "\\backups"
SRC_REMOTE = REMOTE_ROOT + "\\src"

# Files to deploy
LOCAL_SRC = Path(__file__).parent / "src"
LOCAL_ENV = Path(__file__).parent / ".env"


def get_session():
    try:
        import winrm
    except ImportError:
        print("ERROR: Install winrm first: pip install winrm")
        sys.exit(1)

    # Resolve credentials in order: env var > .vm-creds file > ask user
    password = VM_PASS
    if not password:
        creds_file = Path(__file__).parent / ".vm-creds"
        if creds_file.exists():
            for line in creds_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("VM_PASS="):
                    password = line.split("=", 1)[1]
                    break

    if not password:
        print("ERROR: Set VM_PASS environment variable or create .vm-creds file")
        print("  echo 'VM_PASS=your_password' > .vm-creds")
        sys.exit(1)

    return winrm.Session(VM_HOST, auth=(VM_USER, password), transport="ntlm")


def run_ps(s, script, label=""):
    """Execute a PowerShell script via WinRM. Returns (success, output)."""
    if label:
        print("\n  > " + label)
    ps_bytes = script.encode("utf_16_le")
    encoded = base64.b64encode(ps_bytes).decode()
    r = s.run_cmd("powershell.exe -ExecutionPolicy Bypass -EncodedCommand " + encoded)
    stdout = r.std_out.decode("utf-8", errors="replace").strip()
    stderr = r.std_err.decode("utf-8", errors="replace").strip()
    output = stdout
    if stderr:
        output += "\n  [stderr] " + stderr[:500]
    success = r.status_code == 0
    mark = "\u2713" if success else "\u2717"
    print("  " + mark + " " + (label or "PowerShell"))
    if output and len(output) < 2000:
        print("    " + output)
    elif output:
        print("    (output truncated, " + str(len(output)) + " chars)")
    return success, output


def create_backup(s, keep_last=5):
    """Create a timestamped backup of the current VM state."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_BASE + "\\backup_" + ts

    lines = [
        "$ts = Get-Date -Format 'yyyyMMdd_HHmmss'",
        "$backupDir = \"" + BACKUP_BASE + "\\backup_$ts\"",
        "New-Item -ItemType Directory -Path $backupDir -Force | Out-Null",
        "",
        "if (Test-Path '" + SRC_REMOTE + "') {",
        "    $srcDest = Join-Path $backupDir 'src'",
        "    New-Item -ItemType Directory -Path $srcDest -Force | Out-Null",
        "    Copy-Item (Join-Path '" + SRC_REMOTE + "' '*') $srcDest -Recurse -Force",
        "}",
        "",
        "if (Test-Path '" + REMOTE_ROOT + "\\env') {",
        "    Copy-Item '" + REMOTE_ROOT + "\\env' (Join-Path $backupDir 'env') -Force",
        "}",
        "foreach ($bat in @('launch_bot.bat', 'restart_bot.bat')) {",
        "    $src = Join-Path '" + REMOTE_ROOT + "' $bat",
        "    if (Test-Path $src) { Copy-Item $src $backupDir -Force }",
        "}",
        "$logDir = Join-Path $backupDir 'logs'",
        "New-Item -ItemType Directory -Path $logDir -Force | Out-Null",
        "if (Test-Path '" + REMOTE_ROOT + "\\logs\\bot_wrapper.log') {",
        "    Copy-Item '" + REMOTE_ROOT + "\\logs\\bot_wrapper.log' (Join-Path $logDir 'bot_wrapper.log') -Force",
        "}",
        "Write-Host 'Backup created: $backupDir'",
        "Get-ChildItem -Path $backupDir -Recurse",
    ]
    script = "\n".join(lines)
    return run_ps(s, script, "Backup created: backup_" + ts)


def rsync_files(s, files_to_deploy=None):
    """Deploy files to the VM using PowerShell base64 transfer."""
    if files_to_deploy is None:
        py_files = list(LOCAL_SRC.glob("*.py"))
        files_to_deploy = ["src/" + p.name for p in sorted(py_files)]
        if LOCAL_ENV.exists():
            files_to_deploy.insert(0, ".env")

    success_count = 0
    fail_count = 0
    results = []

    for rel_path in files_to_deploy:
        local_file = Path(rel_path)
        if not local_file.exists():
            results.append("  X SKIP (not found): " + rel_path)
            fail_count += 1
            continue

        if rel_path == ".env":
            remote_dest = REMOTE_ROOT + "\\env"
        else:
            rel = rel_path.replace("src/", "")
            remote_dest = SRC_REMOTE + "\\" + rel

        dest_dir = str(Path(remote_dest).parent)
        mkdir_lines = [
            "$dir = '" + dest_dir + "'",
            "New-Item -ItemType Directory -Path $dir -Force | Out-Null",
        ]
        ok, _ = run_ps(s, "\n".join(mkdir_lines), "Ensure dir for " + rel_path)
        if not ok:
            results.append("  X Failed dir: " + rel_path)
            fail_count += 1
            continue

        file_bytes = local_file.read_bytes()
        b64 = base64.b64encode(file_bytes).decode()
        write_lines = [
            "$data = [Convert]::FromBase64String('" + b64 + "')",
            "$dest = '" + remote_dest + "'",
            "[System.IO.File]::WriteAllBytes($dest, $data)",
            "Write-Host ('Written: ' + $dest + ' (' + $data.Length + ' bytes)')",
        ]
        ok, out = run_ps(s, "\n".join(write_lines), rel_path)
        if ok:
            success_count += 1
            results.append(out.strip().split("\n")[-1])
        else:
            fail_count += 1
            results.append("  X Failed: " + rel_path)

    results.append("\n  Summary: " + str(success_count) + " OK, " + str(fail_count) + " failed")
    return fail_count == 0, "\n".join(results)


def cleanup_backups(s, keep=5):
    """Delete old backups, keeping the most recent keep ones."""
    lines = [
        "$backups = Get-ChildItem '" + BACKUP_BASE + "' -Directory | Sort-Object Name",
        "$toDelete = $backups.Count - " + str(keep),
        "if ($toDelete -gt 0) {",
        "    $backups | Select-Object -First $toDelete | Remove-Item -Recurse -Force",
        "    Write-Host ('Deleted ' + $toDelete + ' old backup(s)')",
        "} else {",
        "    Write-Host 'No backups to delete (keeping " + str(keep) + ")'.",
        "}",
        "Get-ChildItem '" + BACKUP_BASE + "' -Directory | Sort-Object Name | Select-Object Name, LastWriteTime",
    ]
    return run_ps(s, "\n".join(lines), "Cleanup old backups")


def rollback(s):
    """Rollback to the latest backup."""
    lines = [
        "$latest = Get-ChildItem '" + BACKUP_BASE + "' -Directory | Sort-Object Name -Descending | Select-Object -First 1",
        "if (-not $latest) { Write-Host 'No backups found!'; exit 1 }",
        "$srcDest = '" + SRC_REMOTE + "'",
        "$logDir = '" + REMOTE_ROOT + "\\logs'",
        "New-Item -ItemType Directory -Path $srcDest -Force | Out-Null",
        "New-Item -ItemType Directory -Path $logDir -Force | Out-Null",
        'Copy-Item (Join-Path $latest.FullName "src\\*") $srcDest -Recurse -Force',
        'if (Test-Path (Join-Path $latest.FullName "env")) {',
        "    Copy-Item (Join-Path $latest.FullName 'env') '" + REMOTE_ROOT + "\\env' -Force",
        "}",
        "foreach ($bat in @('launch_bot.bat', 'restart_bot.bat')) {",
        "    $b = Join-Path $latest.FullName $bat",
        "    if (Test-Path $b) { Copy-Item $b '" + REMOTE_ROOT + "\\*' -Force }",
        "}",
        'if (Test-Path (Join-Path $latest.FullName "logs\\bot_wrapper.log")) {',
        "    Copy-Item (Join-Path $latest.FullName 'logs\\bot_wrapper.log') (Join-Path $logDir 'bot_wrapper.log') -Force",
        "}",
        "Write-Host 'Rollback complete. Restored from: ' + $latest.FullName",
        "Write-Host ('  Backup: ' + $latest.Name + '  Date: ' + $latest.LastWriteTime)",
    ]
    return run_ps(s, "\n".join(lines), "Rollback to latest backup")


def verify_deployment(s):
    """Verify files are in place and report sizes."""
    lines = [
        "Write-Host '=== Deployment Verification ==='",
        "$files = @(",
        "    '" + REMOTE_ROOT + "\\env',",
        "    '" + REMOTE_ROOT + "\\launcher.py',",
        "    '" + REMOTE_ROOT + "\\monitor.py',",
        "    '" + REMOTE_ROOT + "\\launch_bot.bat',",
        "    '" + REMOTE_ROOT + "\\restart_bot.bat'",
        ")",
        "$srcFiles = Get-ChildItem '" + SRC_REMOTE + "' -Filter '*.py' | Sort-Object Name",
        "foreach ($f in $srcFiles) {",
        "    Write-Host ('  src/' + (Split-Path $f.Name -Leaf) + ': ' + $f.Length + ' bytes')",
        "}",
        "foreach ($f in $files) {",
        "    if (Test-Path $f) {",
        "        $info = Get-Item $f",
        "        Write-Host ('  ' + (Split-Path $f -Leaf) + ': ' + $info.Length + ' bytes')",
        "    } else {",
        "        Write-Host ('  MISSING: ' + $f)",
        "    }",
        "}",
        "Write-Host '=== Backup History ==='",
        "Get-ChildItem '" + BACKUP_BASE + "' -Directory | Sort-Object Name | Select-Object Name, LastWriteTime",
    ]
    return run_ps(s, "\n".join(lines), "Verification")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    s = get_session()

    if "--rollback" in args:
        ok, out = rollback(s)
        print(out)
        sys.exit(0 if ok else 1)

    if "--cleanup-backups" in args:
        ok, out = cleanup_backups(s, keep=5)
        print(out)
        sys.exit(0 if ok else 1)

    if "--backup-only" in args:
        ok, out = create_backup(s)
        print(out)
        sys.exit(0 if ok else 1)

    deploy_files = args if args else None

    print("=" * 60)
    print("  Discord Bot Production Deployment")
    print("=" * 60)

    print("\n[STEP 1/3] Creating backup...")
    ok, out = create_backup(s)
    print(out)
    if not ok:
        print("\nERROR: BACKUP FAILED - aborting deployment!")
        sys.exit(1)

    print("\n[STEP 2/3] Deploying files...")
    ok, out = rsync_files(s, deploy_files)
    print(out)
    if not ok:
        print("\nWARNING: Some files failed to deploy.")

    print("\n[STEP 3/3] Verifying deployment...")
    ok, out = verify_deployment(s)
    print(out)

    print("\n" + "=" * 60)
    print("  Deployment complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
