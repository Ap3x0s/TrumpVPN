import shlex
from datetime import datetime

import paramiko

from app.models import VpnServer


class ProvisioningError(Exception):
    pass


def _run_ssh(server: VpnServer, command: str, timeout: float = 20.0) -> str:
    if not server.ssh_key_path:
        raise ProvisioningError("Server SSH key not configured")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=server.ssh_host,
            port=server.ssh_port,
            username=server.ssh_user,
            key_filename=server.ssh_key_path or None,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        if exit_code != 0:
            raise ProvisioningError(f"SSH command failed: {err or out or f'code {exit_code}'}")
        return out
    except ProvisioningError:
        raise
    except Exception as exc:
        raise ProvisioningError(str(exc)) from exc
    finally:
        client.close()


def _expiry_arg(expires_at: datetime | None) -> str:
    if not expires_at:
        return ""
    return f" --expiry {shlex.quote(expires_at.strftime('%Y-%m-%dT%H:%M:%SZ'))}"


def add_client(server: VpnServer, secret: str, email_tag: str, expires_at: datetime | None) -> None:
    """Provision one client on the server. secret=uuid(vless) or password(hy2)."""
    if (server.protocol or "").strip().lower() == "hysteria2":
        cmd = (
            f"sudo {shlex.quote(server.remote_add_script)} "
            f"--password {shlex.quote(secret)} "
            f"--name {shlex.quote(email_tag)}"
            f"{_expiry_arg(expires_at)}"
        )
    else:
        cmd = (
            f"sudo {shlex.quote(server.remote_add_script)} "
            f"--uuid {shlex.quote(secret)} "
            f"--email {shlex.quote(email_tag)}"
            f"{_expiry_arg(expires_at)}"
        )
    _run_ssh(server, cmd, timeout=20.0)


def remove_client(server: VpnServer, secret: str) -> None:
    flag = "--password" if (server.protocol or "").strip().lower() == "hysteria2" else "--uuid"
    cmd = (
        f"sudo {shlex.quote(server.remote_remove_script)} "
        f"{flag} {shlex.quote(secret)} || true"
    )
    try:
        _run_ssh(server, cmd, timeout=90.0)
    except ProvisioningError:
        # best-effort removal; idempotent
        pass
