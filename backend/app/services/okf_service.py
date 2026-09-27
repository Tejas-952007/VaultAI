from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class OKFService:
    def __init__(self, okf_root: Path | None = None):
        self.okf_root = okf_root or Path("okf")
        self.documents_path = self.okf_root / "concepts" / "documents"
        self.agents_path = self.okf_root / "concepts" / "agents"

    def _load_yaml_files(self, directory: Path) -> List[Dict[str, Any]]:
        concepts: List[Dict[str, Any]] = []

        if not directory.exists():
            return concepts

        for file_path in sorted(directory.glob("*.yaml")):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = yaml.safe_load(file) or {}

                if isinstance(data, dict):
                    data["_source_file"] = str(file_path)
                    concepts.append(data)

            except Exception as exc:
                print(f"OKF: Failed to load {file_path}: {exc}")

        return concepts

    def load_document_concepts(self) -> List[Dict[str, Any]]:
        return self._load_yaml_files(self.documents_path)

    def load_agent_concepts(self) -> List[Dict[str, Any]]:
        return self._load_yaml_files(self.agents_path)

    def get_document_concept(
        self, concept_id: str
    ) -> Dict[str, Any] | None:
        for concept in self.load_document_concepts():
            concept_data = concept.get("concept", {})

            if concept_data.get("id") == concept_id:
                return concept

        return None

    def get_agent_concept(
        self, concept_id: str
    ) -> Dict[str, Any] | None:
        for concept in self.load_agent_concepts():
            concept_data = concept.get("concept", {})

            if concept_data.get("id") == concept_id:
                return concept

        return None

    
    # Explicit mapping from VaultAI DB positions to OKF roles.
    # Unmapped positions are denied by default.
    POSITION_TO_OKF_ROLE = {
        "Administrator": "admin",
        "Engineer": "engineer",
    }

    def resolve_okf_role(self, position_name: str) -> str | None:
        """Map a VaultAI database position to an OKF role."""
        if not position_name:
            return None

        return self.POSITION_TO_OKF_ROLE.get(position_name)

    def get_allowed_roles(self, concept_id: str) -> List[str]:
        """Return roles allowed by a document OKF concept."""
        concept = self.get_document_concept(concept_id)

        if not concept:
            return []

        access = concept.get("access", {})
        allowed_roles = access.get("allowed_roles", [])

        if not isinstance(allowed_roles, list):
            return []

        return [str(role).strip() for role in allowed_roles if str(role).strip()]

    def is_position_allowed(
        self,
        concept_id: str,
        position_name: str,
    ) -> bool:
        """Check whether a DB position is allowed by an OKF document concept."""
        okf_role = self.resolve_okf_role(position_name)

        if not okf_role:
            return False

        allowed_roles = self.get_allowed_roles(concept_id)

        return okf_role in allowed_roles


okf_service = OKFService()
