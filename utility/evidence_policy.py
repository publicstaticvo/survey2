from __future__ import annotations

from copy import deepcopy
from typing import Any


def _relax_schema_node(node: Any, evidence_keys: set[str]) -> None:
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key in evidence_keys:
                prop = properties.get(key)
                if isinstance(prop, dict) and prop.get("type") == "string":
                    prop.pop("minLength", None)
        required = node.get("required")
        if isinstance(required, list):
            node["required"] = [item for item in required if item not in evidence_keys]
        if node.get("type") == "object":
            node["additionalProperties"] = True
        for value in node.values():
            _relax_schema_node(value, evidence_keys)
    elif isinstance(node, list):
        for item in node:
            _relax_schema_node(item, evidence_keys)


def relax_evidence_schema(schema: Any, evidence_keys: set[str]) -> Any:
    relaxed = deepcopy(schema)
    _relax_schema_node(relaxed, evidence_keys)
    return relaxed


def _fill_missing_evidence(value: Any, evidence_keys: set[str]) -> None:
    if isinstance(value, dict):
        for key in evidence_keys:
            value.setdefault(key, "")
        for item in value.values():
            _fill_missing_evidence(item, evidence_keys)
    elif isinstance(value, list):
        for item in value:
            _fill_missing_evidence(item, evidence_keys)


def normalize_optional_evidence(value: Any, evidence_keys: set[str]) -> Any:
    _fill_missing_evidence(value, evidence_keys)
    return value
