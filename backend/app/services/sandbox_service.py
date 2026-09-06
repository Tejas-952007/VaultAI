import asyncio
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from backend.app.config import settings


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    timed_out: bool
    error_message: Optional[str] = None


def build_sandbox_command(code: str, timeout: int | None = None) -> list[str]:
    """Construct a hardened Docker command that minimizes privilege and network exposure."""
    if not isinstance(code, str):
        raise TypeError("Sandbox code must be a string.")

    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--cpus",
        "0.5",
        "--memory",
        "256m",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--pids-limit",
        "64",
        "--ulimit",
        "nofile=1024:1024",
        "-i",
        settings.SANDBOX_IMAGE,
        "-c",
        code,
    ]


def _run_sandbox_sync(
    cmd: list[str],
    timeout: int,
) -> tuple[bytes, bytes, int, bool, str | None]:
    """Run Docker synchronously; called from an asyncio worker thread."""
    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return (
            completed.stdout,
            completed.stderr,
            completed.returncode,
            False,
            None,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            b"",
            b"",
            -1,
            True,
            f"TimeoutExpired: {exc!r}",
        )
    except Exception as exc:
        return (
            b"",
            b"",
            -1,
            False,
            f"{type(exc).__name__}: {exc!r}",
        )


async def execute_code(code: str, timeout: int | None = None) -> SandboxResult:
    """Execute Python code inside the hardened Docker sandbox."""
    start = time.time()
    effective_timeout = (
        settings.SANDBOX_TIMEOUT_SECONDS if timeout is None else timeout
    )
    cmd = build_sandbox_command(code, timeout=effective_timeout)

    stdout, stderr, exit_code, timed_out, error_message = await asyncio.to_thread(
        _run_sandbox_sync,
        cmd,
        effective_timeout,
    )

    duration = time.time() - start

    return SandboxResult(
        stdout=stdout.decode(errors="ignore"),
        stderr=stderr.decode(errors="ignore"),
        exit_code=exit_code,
        duration=duration,
        timed_out=timed_out,
        error_message=error_message,
    )
