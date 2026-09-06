from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


def _port_is_local(port: int) -> bool | None:
    """Return True when the local listener is bound only to loopback."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    f"Get-NetTCPConnection -LocalPort {port} "
                    "-State Listen -ErrorAction SilentlyContinue | "
                    "Select-Object LocalAddress | ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            addresses = [str(data.get("LocalAddress", ""))]
        else:
            addresses = [
                str(item.get("LocalAddress", ""))
                for item in data
            ]

        addresses = [
            address
            for address in addresses
            if address
        ]

        if not addresses:
            return None

        loopback = {
            "127.0.0.1",
            "::1",
        }

        return all(
            address in loopback
            for address in addresses
        )

    except Exception:
        return None


def _firewall_status() -> dict:
    """Read Windows Firewall profile state."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-NetFirewallProfile | "
                    "Select-Object Name,Enabled | "
                    "ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return {
                "status": "UNKNOWN",
                "profiles": [],
            }

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        profiles = [
            {
                "name": item.get("Name"),
                "enabled": bool(item.get("Enabled")),
            }
            for item in data
        ]

        enabled = (
            bool(profiles)
            and all(
                profile["enabled"]
                for profile in profiles
            )
        )

        return {
            "status": "PASS" if enabled else "FAIL",
            "profiles": profiles,
        }

    except Exception:
        return {
            "status": "UNKNOWN",
            "profiles": [],
        }


def _vaultai_firewall_rules() -> dict:
    """Check whether our dedicated VaultAI Air-Gap rules exist."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-NetFirewallRule -Group 'VaultAI Air-Gap' "
                    "-ErrorAction SilentlyContinue | "
                    "Select-Object DisplayName,Direction,Action,Enabled | "
                    "ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return {
                "status": "FAIL",
                "rule_count": 0,
                "active_rules": 0,
                "rules": [],
            }

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        rules = [
            {
                "name": item.get("DisplayName"),
                "direction": item.get("Direction"),
                "action": item.get("Action"),
                "enabled": bool(item.get("Enabled")),
            }
            for item in data
        ]

        expected = 6

        active = sum(
            1
            for rule in rules
            if rule["enabled"]
        )

        return {
            "status": (
                "PASS"
                if active >= expected
                else "FAIL"
            ),
            "rule_count": len(rules),
            "active_rules": active,
            "rules": rules,
        }

    except Exception:
        return {
            "status": "UNKNOWN",
            "rule_count": 0,
            "active_rules": 0,
            "rules": [],
        }


def _verify_model(model: str, role: str) -> dict:
    """
    Resolve an Ollama model to its local blob and verify its SHA-256.

    The expected digest is taken from the Ollama blob filename.
    The actual digest is calculated from the local model file.
    """
    base_result = {
        "model": model,
        "role": role,
        "provider": "Ollama (local)",
        "sha256": None,
        "expected_sha256": None,
        "verification": "NOT_VERIFIED",
        "status": "UNKNOWN",
    }

    try:
        result = subprocess.run(
            [
                "ollama",
                "show",
                model,
                "--modelfile",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {
                **base_result,
                "reason": (
                    "Unable to query Ollama model metadata."
                ),
            }

        match = re.search(
            r"(?im)^FROM\s+(.+?)\s*$",
            result.stdout,
        )

        if not match:
            return {
                **base_result,
                "reason": (
                    "Ollama did not expose a local model blob."
                ),
            }

        model_path = (
            match.group(1)
            .strip()
            .strip('"')
        )

        if not os.path.isfile(model_path):
            return {
                **base_result,
                "reason": (
                    "Local model artifact was not found."
                ),
            }

        digest = hashlib.sha256()

        with open(model_path, "rb") as model_file:
            for chunk in iter(
                lambda: model_file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        actual_hash = digest.hexdigest().upper()

        filename = os.path.basename(model_path)

        expected_match = re.match(
            r"sha256-([0-9a-fA-F]{64})$",
            filename,
        )

        expected_hash = (
            expected_match.group(1).upper()
            if expected_match
            else None
        )

        verified = (
            expected_hash is not None
            and actual_hash == expected_hash
        )

        return {
            **base_result,
            "sha256": actual_hash,
            "expected_sha256": expected_hash,
            "verification": (
                "VERIFIED"
                if verified
                else "MISMATCH"
            ),
            "status": (
                "PASS"
                if verified
                else "FAIL"
            ),
        }

    except Exception as exc:
        return {
            **base_result,
            "reason": str(exc),
        }


def _model_checksum() -> dict:
    """
    Verify SHA-256 for all configured VaultAI local models.

    VaultAI uses three sovereign local models:
      - qwen3.5:latest       -> Document / General AI
      - qwen2.5-coder:7b     -> Coding Agent
      - qwen3-vl:8b          -> Vision Agent

    Other Ollama-installed models are intentionally excluded from
    the VaultAI provenance count because they are not configured as
    VaultAI runtime models.
    """
    configured_models = [
        {
            "model": "qwen3.5:latest",
            "role": "Document / General AI",
        },
        {
            "model": "qwen2.5-coder:7b",
            "role": "Coding Agent",
        },
        {
            "model": "qwen3-vl:8b",
            "role": "Vision Agent",
        },
    ]

    results = [
        _verify_model(
            item["model"],
            item["role"],
        )
        for item in configured_models
    ]

    configured_count = len(results)

    verified_count = sum(
        1
        for item in results
        if item["verification"] == "VERIFIED"
    )

    overall_status = (
        "PASS"
        if (
            configured_count == 3
            and verified_count == configured_count
        )
        else "FAIL"
    )

    primary = results[0] if results else {
        "model": None,
        "role": None,
        "provider": "Ollama (local)",
        "sha256": None,
        "expected_sha256": None,
        "verification": "NOT_VERIFIED",
        "status": "UNKNOWN",
    }

    return {
        "status": overall_status,
        "configured_models": configured_count,
        "verified_models": verified_count,

        # Backward-compatible primary model fields.
        "verification": primary["verification"],
        "model": primary["model"],
        "role": primary["role"],
        "provider": primary["provider"],
        "sha256": primary["sha256"],
        "expected_sha256": primary["expected_sha256"],

        # New authoritative multi-model provenance.
        "models": results,
    }


@router.get("/security/status")
def get_security_status():
    firewall = _firewall_status()
    airgap_rules = _vaultai_firewall_rules()
    model_provenance = _model_checksum()

    ports = {
        "frontend": {
            "port": 3001,
            "local_only": _port_is_local(3001),
        },
        "backend": {
            "port": 8000,
            "local_only": _port_is_local(8000),
        },
        "ollama": {
            "port": 11434,
            "local_only": _port_is_local(11434),
        },
        "postgres": {
            "port": 5432,
            "local_only": _port_is_local(5432),
        },
    }

    local_services_pass = all(
        value["local_only"] is True
        for value in ports.values()
    )

    network_isolation_pass = (
        firewall["status"] == "PASS"
        and airgap_rules["status"] == "PASS"
    )

    return {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "hostname": socket.gethostname(),

        "network_isolation": {
            "status": (
                "PASS"
                if network_isolation_pass
                else "FAIL"
            ),
            "firewall": firewall,
            "airgap_rules": airgap_rules,
        },

        "local_services": {
            "status": (
                "PASS"
                if local_services_pass
                else "FAIL"
            ),
            "services": ports,
        },

        "claims": {
            # Software cannot prove a physical air gap.
            "physical_air_gap": "NOT_VERIFIED",

            # No implementation exists for this capability.
            "gpu_memory_encryption": "NOT_IMPLEMENTED",

            # Packet-level telemetry is not currently implemented.
            "packet_telemetry": "NOT_IMPLEMENTED",

            # Overall configured-model verification state.
            "model_checksum": (
                "VERIFIED"
                if model_provenance["verified_models"]
                == model_provenance["configured_models"]
                else "NOT_VERIFIED"
            ),
        },

        "model_provenance": model_provenance,
    }