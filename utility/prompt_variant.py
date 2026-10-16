from __future__ import annotations

from copy import deepcopy
from typing import Any


def optional_string_fields(schema: Any, field_names: set[str]) -> Any:
    relaxed = deepcopy(schema)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for name in field_names:
                    prop = properties.get(name)
                    if isinstance(prop, dict) and prop.get("type") == "string":
                        prop.pop("minLength", None)
            required = node.get("required")
            if isinstance(required, list):
                node["required"] = [name for name in required if name not in field_names]
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(relaxed)
    return relaxed


def fill_empty_fields(value: Any, field_names: set[str]) -> Any:
    if isinstance(value, dict):
        for name in field_names:
            value.setdefault(name, "")
        for item in value.values():
            fill_empty_fields(item, field_names)
    elif isinstance(value, list):
        for item in value:
            fill_empty_fields(item, field_names)
    return value
