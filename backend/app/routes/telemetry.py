import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
from fastapi import APIRouter

router = APIRouter()

_process = psutil.Process(os.getpid())
_process.cpu_percent(interval=None)

# Filesystem allocation is expensive to calculate.
# Keep the latest result cached and refresh it in a background thread.
_storage_cache = {
    "timestamp": 0.0,
    "data": None,
}

_storage_lock = threading.Lock()
_storage_refresh_running = False

_STORAGE_CACHE_SECONDS = 30

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_nvidia_gpu():
    command = [
        "nvidia-smi",
        "--query-gpu=name,utilization.gpu,memory.total,memory.used,memory.free,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return {
                "available": False,
                "reason": "nvidia-smi unavailable",
            }

        gpus = []

        for line in result.stdout.strip().splitlines():
            parts = [part.strip() for part in line.split(",")]

            if len(parts) != 7:
                continue

            (
                name,
                gpu_util,
                memory_total,
                memory_used,
                memory_free,
                temperature,
                power,
            ) = parts

            gpus.append(
                {
                    "name": name,
                    "utilization_percent": float(gpu_util),
                    "memory_total_mb": float(memory_total),
                    "memory_used_mb": float(memory_used),
                    "memory_free_mb": float(memory_free),
                    "temperature_c": float(temperature),
                    "power_watts": float(power),
                }
            )

        if not gpus:
            return {
                "available": False,
                "reason": "no NVIDIA GPU data",
            }

        return {
            "available": True,
            "count": len(gpus),
            "gpus": gpus,
        }

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        ValueError,
        OSError,
    ) as exc:
        return {
            "available": False,
            "reason": type(exc).__name__,
        }


def get_directory_size(path: Path) -> int:
    total = 0

    try:
        for root, dirs, files in os.walk(path):
            # Do not follow symbolic links.
            dirs[:] = [
                directory
                for directory in dirs
                if not (Path(root) / directory).is_symlink()
            ]

            for filename in files:
                file_path = Path(root) / filename

                try:
                    if not file_path.is_symlink():
                        total += file_path.stat().st_size
                except (OSError, PermissionError):
                    continue

    except (OSError, PermissionError):
        return 0

    return total


def build_storage_allocation():
    allocations = []

    try:
        for entry in PROJECT_ROOT.iterdir():
            if not entry.is_dir():
                continue

            # Skip very large generated/dependency trees.
            # These are intentionally excluded from the recursive
            # workspace allocation scan.
            if entry.name in {
                ".git",
                "node_modules",
                ".next",
            }:
                continue

            size = get_directory_size(entry)

            allocations.append(
                {
                    "name": entry.name,
                    "size_bytes": size,
                }
            )

        # Files directly inside the project root.
        root_files_size = 0

        for entry in PROJECT_ROOT.iterdir():
            if entry.is_file():
                try:
                    root_files_size += entry.stat().st_size
                except (OSError, PermissionError):
                    continue

        if root_files_size:
            allocations.append(
                {
                    "name": "[root files]",
                    "size_bytes": root_files_size,
                }
            )

        allocations.sort(
            key=lambda item: item["size_bytes"],
            reverse=True,
        )

        return {
            "available": True,
            "path": str(PROJECT_ROOT),
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "entries": allocations,
        }

    except (OSError, PermissionError) as exc:
        return {
            "available": False,
            "reason": type(exc).__name__,
        }


def _refresh_storage_in_background():
    global _storage_refresh_running

    try:
        data = build_storage_allocation()

        with _storage_lock:
            _storage_cache["timestamp"] = time.time()
            _storage_cache["data"] = data

    finally:
        with _storage_lock:
            _storage_refresh_running = False


def get_storage_allocation():
    global _storage_refresh_running

    now = time.time()

    with _storage_lock:
        cached_data = _storage_cache["data"]
        cache_age = now - _storage_cache["timestamp"]

        needs_refresh = (
            cached_data is None
            or cache_age >= _STORAGE_CACHE_SECONDS
        )

        if needs_refresh and not _storage_refresh_running:
            _storage_refresh_running = True

            thread = threading.Thread(
                target=_refresh_storage_in_background,
                daemon=True,
                name="vaultai-storage-telemetry",
            )

            thread.start()

        if cached_data is not None:
            return cached_data

    return {
        "available": False,
        "reason": "initial filesystem scan in progress",
    }


@router.get("/telemetry")
def get_telemetry():
    # interval=None makes this call non-blocking.
    cpu_percent = psutil.cpu_percent(interval=None)

    memory = psutil.virtual_memory()

    disk = psutil.disk_usage(
        os.path.abspath(os.sep)
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "system": {
            "cpu_percent": round(
                cpu_percent,
                1,
            ),
            "memory_percent": round(
                memory.percent,
                1,
            ),
            "memory_used_bytes": memory.used,
            "memory_total_bytes": memory.total,
            "uptime_seconds": round(
                time.time() - psutil.boot_time(),
                1,
            ),
        },

        "disk": {
            "usage_percent": round(
                disk.percent,
                1,
            ),
            "used_bytes": disk.used,
            "total_bytes": disk.total,
            "free_bytes": disk.free,
        },

        "storage_allocation": get_storage_allocation(),

        "backend_process": {
            "cpu_percent": round(
                _process.cpu_percent(interval=None),
                1,
            ),
            "memory_bytes": _process.memory_info().rss,
        },

        "gpu": get_nvidia_gpu(),
    }