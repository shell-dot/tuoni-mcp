from __future__ import annotations

import json
import time
from dataclasses import replace
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from tuoni.TuoniExceptions import ExceptionTuoniRequestFailed

from tuoni_mcp.config import Profile, Settings
from tuoni_mcp.server import build_server


AGENT_OPS_TOOLS = (
    "tuoni_agents_list",
    "tuoni_agent_get",
    "tuoni_commands_search",
    "tuoni_command_describe",
    "tuoni_command_prepare",
    "tuoni_command_update_prepare",
    "tuoni_command_stop_prepare",
    "tuoni_operation_execute",
    "tuoni_command_get",
    "tuoni_commands_list",
    "tuoni_capabilities",
)


def _command_data(result: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "id": 42,
        "commandTemplateId": "template-cmd",
        "commandTemplateName": "cmd",
        "configuration": {"command": "whoami /all"},
        "execConf": {},
        "status": "COMPLETE" if result is not None else "SENT",
        "created": "2026-07-20T00:00:00Z",
        "sent": "2026-07-20T00:00:01Z",
        "result": result,
    }


def _text_result(value: str) -> dict[str, Any]:
    return {
        "status": "SUCCESS",
        "errorMessage": None,
        "received": "2026-07-20T00:00:02Z",
        "childResults": [{"type": "text", "name": "stdout", "value": value}],
    }


def _agent_data(
    guid: str = "agent-1", template_ids: list[str] | None = None
) -> dict[str, Any]:
    return {
        "guid": guid,
        "firstRegistrationTime": "2026-07-20T00:00:00Z",
        "lastCallbackTime": "2026-07-20T00:00:01Z",
        "metadata": {
            "hostname": "workstation-1",
            "username": "operator",
            "os": "WINDOWS",
            "architecture": "amd64",
        },
        "active": True,
        "status": "ACTIVE",
        "recentListeners": [],
        "availableCommandTemplates": template_ids or [],
    }


def _agents_page(*agents: dict[str, Any]) -> dict[str, Any]:
    return {
        "items": list(agents),
        "page": 0,
        "pageSize": 10,
        "itemCount": len(agents),
        "totalCount": len(agents),
        "totalPages": 1,
        "hasMorePages": False,
    }


def _template_data(
    *,
    name: str = "cmd",
    template_id: str = "template-cmd",
    plugin_id: str = "shelldot.commands.native",
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
    files_schema: dict[str, Any] | None = None,
    example_configuration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if properties is None:
        properties = {
            "command": {"type": "string", "description": "Command text"},
            "stdin": {"type": "array", "items": {"type": "string"}},
        }
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required is not None:
        schema["required"] = required
    if files_schema is not None:
        schema["files"] = files_schema
    if example_configuration is None:
        example_configuration = {key: None for key in properties}
    return {
        "id": template_id,
        "name": name,
        "pluginId": plugin_id,
        "scope": "global",
        "qualifiedName": f"{plugin_id}:global:{name}",
        "fullyQualifiedName": f"{plugin_id}:global:{name}",
        "description": f"Run {name}",
        "configurationSchema": schema,
        "updateSchema": {
            "type": "object",
            "properties": {
                "stdin": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": False,
        },
        "supportedExecUnitTypes": ["SHELLCODE_NATIVE", "DOTNET_EXE"],
        "defaultConfiguration": None,
        "exampleConfigurations": [
            {"name": "default", "configuration": example_configuration}
        ],
    }


def _payload(result) -> dict[str, Any]:
    blocks = [json.loads(item.text) for item in result.content if item.type == "text"]
    assert len(blocks) == 1
    return blocks[0]


def _success(result) -> dict[str, Any]:
    assert result.isError is False
    payload = _payload(result)
    assert set(payload) == {"ok", "data", "next_cursor", "next"}
    assert payload["ok"] is True
    return payload


def _error(result, code: str) -> dict[str, Any]:
    assert result.isError is True
    payload = _payload(result)
    assert set(payload) == {"code", "message", "retryable", "hint"}
    assert payload["code"] == code
    return payload


@pytest.fixture
def cfg() -> Settings:
    return Settings(
        url="https://example.test:8443",
        username="test",
        password="test",
        verify=False,
        profiles=frozenset({Profile.AGENT_OPS}),
    )


@pytest.fixture
def patched_server(monkeypatch, fake_c2, cfg):
    """Use the real in-memory MCP transport with a FakeC2 lifespan context."""
    from tuoni_mcp import connection, server as server_mod

    login_calls = []

    async def _fake_login(context):
        context.last_login = time.monotonic()
        login_calls.append(context)

    monkeypatch.setattr(connection, "login", _fake_login)
    monkeypatch.setattr(server_mod, "TuoniC2", lambda *args, **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", _fake_login)
    server = build_server(cfg)
    server.smoke_login_calls = login_calls
    return server


async def test_memory_transport_runs_lifespan_login_and_lists_agent_ops(
    patched_server,
) -> None:
    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.list_tools()

    assert tuple(tool.name for tool in result.tools) == AGENT_OPS_TOOLS
    assert len(patched_server.smoke_login_calls) == 1


async def test_initial_login_failure_does_not_hide_tool_catalog(
    monkeypatch, fake_c2, cfg
) -> None:
    from tuoni_mcp import server as server_mod

    async def _failed_login(_context):
        raise OSError("C2 is temporarily unavailable")

    monkeypatch.setattr(server_mod, "TuoniC2", lambda *args, **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", _failed_login)
    server = build_server(cfg)

    async with create_connected_server_and_client_session(
        server.protocol_server
    ) as session:
        result = await session.list_tools()

    assert tuple(tool.name for tool in result.tools) == AGENT_OPS_TOOLS


@pytest.mark.parametrize("events", [False, True])
async def test_slow_initial_login_does_not_delay_mcp_handshake(monkeypatch, fake_c2, cfg, events):
    import asyncio
    import anyio
    from dataclasses import replace
    from tuoni_mcp import server as server_mod

    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def slow_login(_context):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(server_mod, "TuoniC2", lambda **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", slow_login)
    if events:
        cfg = replace(cfg, profiles=frozenset({Profile.AGENT_OPS, Profile.EVENTS}))
    server = build_server(cfg)
    with anyio.fail_after(2):
        async with create_connected_server_and_client_session(server.protocol_server) as session:
            tools = await session.list_tools()
            assert len(tools.tools) == (13 if events else 12)
            await started.wait()
    assert cancelled.is_set()


async def test_agents_list_uses_v2_pagination_and_canonical_envelope(
    patched_server, fake_c2
) -> None:
    agent = _agent_data()
    path = "/api/v2/agents?page=0&pageSize=10&status=ACTIVE"
    fake_c2.responses[("GET", path)] = _agents_page(agent)

    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.call_tool("tuoni_agents_list", {})

    data = _success(result)["data"]
    assert data["returned"] == data["total"] == 1
    assert data["agents"][0] == {
        "guid": "agent-1",
        "status": "ACTIVE",
        "active": True,
        "last_callback_time": "2026-07-20T00:00:01Z",
        "hostname": "workstation-1",
        "username": "operator",
        "os": "WINDOWS",
        "architecture": "amd64",
    }
    assert any(
        call[0] == "request_get" and call[1][0] == path for call in fake_c2.calls
    )


async def test_agents_list_maps_missing_v2_endpoint_to_version_error(
    patched_server, fake_c2
) -> None:
    def missing_v2(uri, result_as_json=True, result_as_bytes=False):
        fake_c2._record("request_get", uri, result_as_json, result_as_bytes)
        raise ExceptionTuoniRequestFailed("404 Not Found")

    fake_c2.request_get = missing_v2
    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.call_tool("tuoni_agents_list", {})

    error = _error(result, "INCOMPATIBLE_TUONI_SERVER")
    assert "0.17.0" in error["hint"]


async def test_native_command_workflow_search_prepare_execute_and_poll(
    patched_server, fake_c2
) -> None:
    marker = "RESULT_BODY_MARKER_"
    value = marker + "🙂e\u0301\\quoted\"-" + "0123456789" * 1_000
    template = _template_data()
    agent = _agent_data(template_ids=[template["id"]])
    command = _command_data(_text_result(value))
    fake_c2.responses[("GET", "/api/v1/agents/agent-1")] = agent
    fake_c2.responses[("GET", "/api/v1/command-templates")] = [template]
    fake_c2.responses[("POST", "/api/v1/agents/agent-1/commands")] = command
    fake_c2.responses[("GET", "/api/v1/commands/42")] = command

    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        searched = await session.call_tool(
            "tuoni_commands_search", {"agent_guid": "agent-1", "query": "cmd"}
        )
        search_payload = _success(searched)
        summary = search_payload["data"]["commands"][0]
        assert summary["id"] == "template-cmd"
        assert "configurationSchema" not in json.dumps(search_payload)

        described = await session.call_tool(
            "tuoni_command_describe",
            {"agent_guid": "agent-1", "template": summary["id"]},
        )
        description = _success(described)["data"]
        assert {field["name"] for field in description["fields"]} >= {
            "command",
            "stdin",
        }
        assert description["prepare_arguments_example"]["shell_command"] == "COMMAND_TEXT_GOES_HERE"

        prepared = await session.call_tool(
            "tuoni_command_prepare",
            {
                "agent_guid": "agent-1",
                "template": summary["id"],
                "shell_command": "whoami /all",
            },
        )
        preparation = _success(prepared)
        preparation_id = preparation["data"]["preparation_id"]
        assert preparation["next"] == {
            "name": "tuoni_operation_execute",
            "arguments": {"preparation_id": preparation_id},
        }
        assert not any(call[0] == "request_post" for call in fake_c2.calls)

        executed = await session.call_tool(
            "tuoni_operation_execute", {"preparation_id": preparation_id}
        )
        execution = _success(executed)
        assert execution["data"]["command_id"] == 42
        assert execution["next"] == {
            "name": "tuoni_command_get",
            "arguments": {"command_id": 42},
        }

        manifest_result = await session.call_tool(
            "tuoni_command_get", {"command_id": 42}
        )
        manifest = _success(manifest_result)
        assert marker not in json.dumps(manifest)
        assert manifest["data"]["result"]["part_count"] == 1
        assert manifest["data"]["result"]["parts"][0]["total_chars"] == len(
            value
        )

        window_result = await session.call_tool(
            "tuoni_command_get",
            {
                "command_id": 42,
                "part_index": 0,
                "offset_chars": 7,
                "max_chars": 128,
            },
        )
        window = _success(window_result)

    posts = [call for call in fake_c2.calls if call[0] == "request_post"]
    assert len(posts) == 1
    assert posts[0][1][0] == "/api/v1/agents/agent-1/commands"
    assert posts[0][1][1] == {
        "template": "template-cmd",
        "configuration": {"command": "whoami /all"},
    }
    part = window["data"]["result"]["part"]
    assert part["value"] == value[7:135]
    assert part["next_offset_chars"] == 135
    assert window["next"]["arguments"]["offset_chars"] == 135


async def test_prepare_rejects_wrong_shell_argument_without_mutation(
    patched_server, fake_c2
) -> None:
    template = _template_data()
    fake_c2.responses[("GET", "/api/v1/agents/agent-1")] = _agent_data(
        template_ids=[template["id"]]
    )
    fake_c2.responses[("GET", "/api/v1/command-templates")] = [template]

    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.call_tool(
            "tuoni_command_prepare",
            {
                "agent_guid": "agent-1",
                "template": "cmd",
                "configuration": {"args": "whoami /all"},
            },
        )

    error = _error(result, "INVALID_COMMAND_CONFIGURATION")
    assert "shell_command" in error["hint"]
    assert not any(call[0] == "request_post" for call in fake_c2.calls)


async def test_inline_attachment_is_prepared_then_sent_as_multipart(
    patched_server, fake_c2
) -> None:
    template = _template_data(
        name="upload",
        template_id="template-upload",
        plugin_id="shelldot.commands.fs",
        properties={"path": {"type": "string"}},
        required=["path"],
        files_schema={"input": {"type": "file", "required": True}},
        example_configuration={"path": "C:/Temp/payload.bin"},
    )
    fake_c2.responses[("GET", "/api/v1/agents/agent-1")] = _agent_data(
        template_ids=[template["id"]]
    )
    fake_c2.responses[("GET", "/api/v1/command-templates")] = [template]
    submitted = _command_data(None)
    submitted.update(
        {
            "commandTemplateId": "template-upload",
            "commandTemplateName": "upload",
            "configuration": {"path": "C:/Temp/payload.bin"},
        }
    )
    fake_c2.responses[("POST", "/api/v1/agents/agent-1/commands")] = submitted

    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        prepared = await session.call_tool(
            "tuoni_command_prepare",
            {
                "agent_guid": "agent-1",
                "template": "template-upload",
                "configuration": {"path": "C:/Temp/payload.bin"},
                "execution": {"execType": "SELF"},
                "attachments": [
                    {
                        "field": "input",
                        "filename": "payload.bin",
                        "content_base64": "YWJj",
                    }
                ],
            },
        )
        preparation_id = _success(prepared)["data"]["preparation_id"]
        assert not any(call[0] == "request_post" for call in fake_c2.calls)
        executed = await session.call_tool(
            "tuoni_operation_execute", {"preparation_id": preparation_id}
        )

    assert _success(executed)["data"]["command_id"] == 42
    post = next(call for call in fake_c2.calls if call[0] == "request_post")
    assert post[1][1] == {
        "template": "template-upload",
        "configuration": {"path": "C:/Temp/payload.bin"},
        "execConf": {"execType": "SELF"},
    }
    assert post[1][2] == {"input": ["payload.bin", b"abc"]}


async def test_command_get_pending_result_returns_exact_poll_call(
    patched_server, fake_c2
) -> None:
    fake_c2.responses[("GET", "/api/v1/commands/42")] = _command_data(None)

    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.call_tool("tuoni_command_get", {"command_id": 42})

    payload = _success(result)
    assert payload["data"]["status"] == "SENT"
    assert payload["data"]["result"] is None
    assert payload["next"] == {
        "name": "tuoni_command_get",
        "arguments": {"command_id": 42},
    }


async def test_invalid_command_window_bound_is_a_canonical_tool_error(
    patched_server,
) -> None:
    async with create_connected_server_and_client_session(
        patched_server.protocol_server
    ) as session:
        result = await session.call_tool(
            "tuoni_command_get", {"command_id": 42, "max_chars": 16_385}
        )

    error = _error(result, "INVALID_ARGUMENTS")
    assert "max_chars" in error["hint"]


async def test_read_only_default_keeps_only_observational_agent_ops(
    monkeypatch, fake_c2, cfg
) -> None:
    from tuoni_mcp import connection, server as server_mod

    async def _fake_login(context):
        context.last_login = time.monotonic()

    monkeypatch.setattr(connection, "login", _fake_login)
    monkeypatch.setattr(server_mod, "TuoniC2", lambda *args, **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", _fake_login)
    server = build_server(replace(cfg, read_only=True))

    async with create_connected_server_and_client_session(
        server.protocol_server
    ) as session:
        names = {tool.name for tool in (await session.list_tools()).tools}

    assert names == {
        "tuoni_agents_list",
        "tuoni_agent_get",
        "tuoni_commands_search",
        "tuoni_command_describe",
        "tuoni_command_get",
        "tuoni_commands_list",
        "tuoni_capabilities",
    }


async def test_profiles_add_access_artifacts_discovery_and_raw_tools(
    monkeypatch, fake_c2, cfg
) -> None:
    from tuoni_mcp import connection, server as server_mod

    async def _fake_login(context):
        context.last_login = time.monotonic()

    monkeypatch.setattr(connection, "login", _fake_login)
    monkeypatch.setattr(server_mod, "TuoniC2", lambda *args, **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", _fake_login)
    profiles = frozenset(
        {
            Profile.AGENT_OPS,
            Profile.ACCESS,
            Profile.ARTIFACTS,
            Profile.DISCOVERY,
            Profile.RAW,
        }
    )
    server = build_server(replace(cfg, profiles=profiles))

    async with create_connected_server_and_client_session(
        server.protocol_server
    ) as session:
        names = {tool.name for tool in (await session.list_tools()).tools}

    assert set(AGENT_OPS_TOOLS) <= names
    assert {
        "tuoni_listeners_list",
        "tuoni_listener_create",
        "tuoni_payloads_list",
        "tuoni_payload_create",
        "tuoni_files_list",
        "tuoni_file_upload",
        "tuoni_hosts_list",
        "tuoni_host_add",
        "tuoni_raw_request",
    } <= names


async def test_additive_profile_argument_errors_use_canonical_contract(
    monkeypatch, fake_c2, cfg
) -> None:
    from tuoni_mcp import connection, server as server_mod

    async def _fake_login(context):
        context.last_login = time.monotonic()

    monkeypatch.setattr(connection, "login", _fake_login)
    monkeypatch.setattr(server_mod, "TuoniC2", lambda *args, **kwargs: fake_c2)
    monkeypatch.setattr(server_mod, "login", _fake_login)
    profiles = frozenset({Profile.ARTIFACTS, Profile.DISCOVERY})
    server = build_server(replace(cfg, profiles=profiles))

    async with create_connected_server_and_client_session(
        server.protocol_server
    ) as session:
        oversized_page = await session.call_tool(
            "tuoni_hosts_list", {"page_size": 100_000}
        )
        invalid_base64 = await session.call_tool(
            "tuoni_file_upload",
            {"hosted_path": "/x/y.bin", "content_base64": "!!! not base64 !!!"},
        )

    _error(oversized_page, "INVALID_ARGUMENTS")
    _error(invalid_base64, "TOOL_EXECUTION_FAILED")
    assert fake_c2.calls == []
