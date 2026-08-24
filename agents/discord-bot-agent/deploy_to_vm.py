"""
VM Deployment script - backup and deploy to WIN-2HBN30ECLV2.fritz.box
Usage: python deploy_to_vm.py [backup|deploy|restart|all]
"""
import subprocess
import sys
from datetime import datetime

VM_HOST = "WIN-2HBN30ECLV2.fritz.box"
VM_USER = "twan"
SRC_DIR = "/home/twan/Documents/develop/agent-planner/agents/discord-bot-agent/src"


def run_cmd(cmd: str) -> tuple[str, int]:
    """Run a command and return (stdout, returncode)."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def _ssh(cmd: str) -> tuple[str, int]:
    """Shortcut: run an SSH command on the VM. Returns (stdout, returncode)."""
    return run_cmd(f'ssh {VM_USER}@{VM_HOST} "{cmd}"')


def create_backup():
    """Create timestamped backup on VM."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"C:\\ClashKing\\backups\\backup_{ts}"
    print(f"Creating backup at {backup_dir}...")

    # Create backup dir and copy src
    out, rc = _ssh(
        'robocopy "\\\\ClashKing\\src\\" "\\\\ClashKing\\backups\\backup_' + ts + '\\\\src\\" '
        '/E /NFL /NDL /NJH /NJS 2>nul'
    )
    if rc in (0, 1):
        print("  ✓ Backed up src/")

    # Copy .env
    out, rc = _ssh(
        'copy "\\\\ClashKing\\.env" "\\\\ClashKing\\backups\\backup_' + ts + '\\\\.env" >nul 2>nul'
    )
    if rc == 0:
        print("  ✓ Backed up .env")

    # Copy batch files
    for bat in ["launch_bot.bat", "restart_bot.bat"]:
        _ssh(f'copy "\\\\ClashKing\\{bat}" "\\\\ClashKing\\backups\\backup_{ts}\\" >nul 2>nul')

    # Copy logs
    _ssh(
        'mkdir "\\\\ClashKing\\backups\\backup_' + ts + '\\\\logs\\" 2>nul; '
        'copy "\\\\ClashKing\\logs\\bot_wrapper.log" "\\\\ClashKing\\backups\\backup_' + ts + '\\\\logs\\" >nul 2>nul'
    )

    # Clean old backups (keep last 5)
    _ssh(
        'Get-ChildItem "\\\\ClashKing\\backups\\" -Directory | '
        'Sort-Object Name | Select-Object -Skip 5 | Remove-Item -Recurse -Force'
    )
    print("  ✓ Old backups cleaned")
    print(f"  Backup: {backup_dir}")
    return ts


def deploy_files():
    """Deploy src files to VM via rsync, falling back to scp if needed."""
    print(f"Deploying {SRC_DIR}/ -> {VM_USER}@{VM_HOST}:C:/ClashKing/src/")

    # --- Try rsync first (incremental, only transfers changed files) ---
    rsync_cmd = (
        f'rsync -avz --delete '
        f'--exclude=__pycache__/ '
        f'"--rsh=ssh -o StrictHostKeyChecking=no" '
        f'{SRC_DIR}/ '
        f'{VM_USER}@{VM_HOST}:C:/ClashKing/src/'
    )
    out, rc = run_cmd(rsync_cmd)
    if rc == 0:
        print("  ✓ Rsync: Files deployed successfully")
        # Show transferred files
        for line in out.split("\n"):
            if line.startswith("sending") or line.startswith("sending "):
                continue
            if line.startswith("sent"):
                continue
            if line.strip() and not line.strip().startswith("total"):
                if ">" in line or "*" in line or "+" in line:
                    print(f"    {line.strip()}")
        return  # Success, no need for scp fallback

    print(f"  ⚠ Rsync unavailable/failed ({out.strip()}), falling back to scp...")

    # --- Fallback: scp -r (transfers everything) ---
    scp_cmd = (
        f'scp -r '
        f'-o StrictHostKeyChecking=no '
        f'{SRC_DIR}/* '
        f'{VM_USER}@{VM_HOST}:C:/ClashKing/src/'
    )
    out, rc = run_cmd(scp_cmd)
    if rc == 0:
        print("  ✓ SCP: Files deployed successfully")
    else:
        print(f"  ✗ SCP also failed:\n{out}")


def restart_bot():
    """Restart the bot on VM via scheduled task."""
    print("Triggering bot restart via scheduled task...")
    out, rc = _ssh('schtasks /run /tn "AliceIsBored Bot" 2>nul')
    if rc == 0:
        print("  ✓ Bot restart triggered")
    else:
        print(f"  ⚠ Scheduled task run may have already started the bot: {out}")


if __name__ == "__main__":
    print("=== DiscordCoC VM Deployment ===")
    print()

    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    if step in ("backup", "all"):
        print("[1/3] Creating backup...")
        create_backup()
        print()

    if step in ("deploy", "all"):
        print("[2/3] Deploying files...")
        deploy_files()
        print()

    if step in ("restart", "all"):
        print("[3/3] Restarting bot...")
        restart_bot()
        print()

    print("=== Deployment complete ===")
