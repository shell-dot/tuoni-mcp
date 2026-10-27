"""Tests for the tuoni_api_spec tool — offline, no C2 server needed."""

from __future__ import annotations

from typing import Any

import pytest

from tuoni_mcp.tools.api_spec import (
    ApiSpecInput,
    _HTTP_METHODS,
    _endpoint_lines,
    _resolve_refs,
)


# -- Input validation --

def test_empty_filter_accepted() -> None:
    inp = ApiSpecInput(filter="")
    assert inp.filter == ""


def test_default_filter_is_empty() -> None:
    inp = ApiSpecInput()
    assert inp.filter == ""


def test_filter_max_length_enforced() -> None:
    with pytest.raises(Exception):
        ApiSpecInput(filter="x" * 257)


def test_filter_within_max_length() -> None:
    inp = ApiSpecInput(filter="x" * 256)
    assert len(inp.filter) == 256


def test_cursor_defaults_to_none() -> None:
    inp = ApiSpecInput()
    assert inp.cursor is None


def test_cursor_accepted() -> None:
    inp = ApiSpecInput(cursor="abc123")
    assert inp.cursor == "abc123"


# -- Spec fixtures --

SAMPLE_SPEC: dict[str, Any] = {
    "info": {"version": "0.17.0", "title": "Tuoni API"},
    "components": {
        "schemas": {
            "AgentSummary": {
                "type": "object",
                "properties": {
                    "guid": {"type": "string"},
                    "hostname": {"type": "string"},
                },
            },
            "CreateListenerRequestBody": {
                "type": "object",
                "required": ["name", "pluginId"],
                "properties": {
                    "name": {"type": "string"},
                    "pluginId": {"type": "integer"},
                    "config": {"$ref": "#/components/schemas/ListenerConfig"},
                },
            },
            "ListenerConfig": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer"},
                    "host": {"type": "string"},
                },
            },
        },
    },
    "paths": {
        "/api/v1/agents": {
            "get": {
                "summary": "List agents",
                "tags": ["Agents"],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AgentSummary"},
                            },
                        },
                    },
                },
            },
        },
        "/api/v1/agents/{guid}": {
            "get": {"summary": "Get agent by GUID", "tags": ["Agents"]},
        },
        "/api/v1/listeners": {
            "get": {"summary": "List listeners", "tags": ["Listeners"]},
            "post": {
                "summary": "Create listener",
                "tags": ["Listeners"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateListenerRequestBody"},
                        },
                    },
                },
            },
        },
        "/api/v2/auth/login": {
            "post": {"summary": "Authenticate", "tags": ["Auth"]},
        },
    },
}


# -- HTTP method filtering --

def test_http_methods_filter_non_operations() -> None:
    assert "get" in _HTTP_METHODS
    assert "post" in _HTTP_METHODS
    assert "parameters" not in _HTTP_METHODS
    assert "servers" not in _HTTP_METHODS


# -- $ref resolution --

def test_resolve_refs_simple() -> None:
    node = {"schema": {"$ref": "#/components/schemas/AgentSummary"}}
    resolved = _resolve_refs(node, SAMPLE_SPEC["components"])
    assert resolved["schema"]["type"] == "object"
    assert "guid" in resolved["schema"]["properties"]


def test_resolve_refs_nested() -> None:
    """CreateListenerRequestBody references ListenerConfig — both should resolve."""
    node = {"$ref": "#/components/schemas/CreateListenerRequestBody"}
    resolved = _resolve_refs(node, SAMPLE_SPEC["components"])
    assert resolved["type"] == "object"
    assert "name" in resolved["properties"]
    config = resolved["properties"]["config"]
    assert config["type"] == "object"
    assert "port" in config["properties"]


def test_resolve_refs_missing_ref_unchanged() -> None:
    node = {"$ref": "#/components/schemas/DoesNotExist"}
    resolved = _resolve_refs(node, SAMPLE_SPEC["components"])
    assert resolved == node


def test_resolve_refs_depth_limited() -> None:
    circular: dict[str, Any] = {
        "schemas": {
            "A": {"$ref": "#/components/schemas/B"},
            "B": {"$ref": "#/components/schemas/A"},
        },
    }
    resolved = _resolve_refs({"$ref": "#/components/schemas/A"}, circular)
    assert isinstance(resolved, dict)


def test_resolve_refs_non_local_ref_unchanged() -> None:
    node = {"$ref": "https://example.com/schema.json#/Foo"}
    resolved = _resolve_refs(node, SAMPLE_SPEC["components"])
    assert resolved == node


# -- Endpoint line extraction --

def test_endpoint_lines_sorted_and_filtered() -> None:
    lines = _endpoint_lines(SAMPLE_SPEC["paths"])
    methods = [m for _, m, _, _ in lines]
    assert all(m in _HTTP_METHODS for m in methods)
    paths = [p for p, _, _, _ in lines]
    assert paths == sorted(paths)


def test_endpoint_lines_count() -> None:
    lines = _endpoint_lines(SAMPLE_SPEC["paths"])
    assert len(lines) == 5


# -- Filter matching --

def test_exact_path_match_case_insensitive() -> None:
    paths = SAMPLE_SPEC["paths"]
    query = "/api/v1/agents"
    path_lower_map = {p.lower(): p for p in paths}
    assert query.lower() in path_lower_map


def test_filter_narrows_by_tag() -> None:
    lines = _endpoint_lines(SAMPLE_SPEC["paths"])
    query = "listener"
    matches = [
        f"{m.upper()} {p}"
        for p, m, tag, summary in lines
        if any(query in text.lower() for text in (p, tag, summary))
    ]
    assert len(matches) == 2
    assert "GET /api/v1/listeners" in matches
    assert "POST /api/v1/listeners" in matches


def test_filter_no_match_returns_empty() -> None:
    lines = _endpoint_lines(SAMPLE_SPEC["paths"])
    query = "nonexistent"
    matches = [
        line for line in lines
        if any(query in text.lower() for text in line)
    ]
    assert len(matches) == 0


def test_unfiltered_lists_all_operations() -> None:
    lines = _endpoint_lines(SAMPLE_SPEC["paths"])
    assert len(lines) == 5
