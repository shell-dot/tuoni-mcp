"""Inventory regressions using Tuoni's actual AgentMetadataResponse fields."""

import json
from dataclasses import replace

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from tuoni_mcp.config import MCPMode
from tuoni_mcp.protocol import DETAIL_RESULT_BUDGET, call_result_size
from tuoni_mcp.server import build_server
from tuoni_mcp.tools.agents import _agent_summary


@pytest.mark.parametrize(
    ("metadata", "expected_os", "expected_process"),
    [
        ({"osArch": "X64", "processArch": "X64"}, "X64", None),
        ({"osArch": "X64", "processArch": "X86"}, "X64", "X86"),
        ({"osArch": "ARM64", "processArch": "X64"}, "ARM64", "X64"),
        ({"osArch": "X64", "processArch": None}, "X64", None),
        ({"osArch": None, "processArch": "X86"}, "", "X86"),
        ({"architecture": "amd64"}, "amd64", None),
        ({"arch": "x86"}, "x86", None),
        ({"osArch": "X64", "architecture": "x86"}, "X64", None),
        ({"osArch": None, "architecture": "amd64"}, "amd64", None),
        ({"OSARCH": "X64", "PROCESSARCH": "X86"}, "X64", "X86"),
        ({}, "", None),
    ],
)
def test_inventory_preserves_os_and_distinct_process_architecture(
    metadata: dict, expected_os: str, expected_process: str | None,
) -> None:
    summary = _agent_summary({"guid": "fixture-agent", "metadata": metadata})

    assert summary["architecture"] == expected_os
    if expected_process is None:
        assert "process_architecture" not in summary
    else:
        assert summary["process_architecture"] == expected_process


def test_inventory_bounds_architecture_metadata() -> None:
    summary = _agent_summary(
        {"metadata": {"osArch": "x" * 100, "processArch": "y" * 100}}
    )

    assert len(summary["architecture"].encode("utf-8")) <= 32
    assert len(summary["process_architecture"].encode("utf-8")) <= 32


@pytest.mark.parametrize("mode", list(MCPMode))
async def test_network_metadata_capabilities_and_new_templates_use_existing_tools(
    mode, patched_server, cfg, fake_c2,
):
    metadata = {
        "hostname": "network-fixture", "os": "WINDOWS", "osArch": "X64", "processArch": "X64",
        "netInterfaces": [{"name": "ethernet0", "macAddress": "02:00:00:00:00:01",
                           "ipv4Addresses": ["192.0.2.10"], "ipv6Addresses": ["2001:db8::10"]}],
        "capabilities": {
            "supportedExecUnitTypesForSelfProcesses": ["DOTNET_EXE"],
            "supportedExecUnitTypesForOtherProcesses": [],
            "nativeCommandSupport": {"CMD": "SUPPORTED", "SH": "UNSUPPORTED", "PS": "UNREPORTED"},
        },
        "customProperties": {"label": "fixture", "nullable": None},
    }
    fake_c2.responses["/api/v1/agents/network-agent"] = {
        "guid": "network-agent", "active": True, "status": "ACTIVE", "metadata": metadata,
        "availableCommandTemplates": ["server-netinfo"],
    }
    fake_c2.responses["/api/v1/command-templates"] = [{
        "id": "server-netinfo", "name": "netinfo", "description": "Report network interface information",
        "configurationSchema": {"type": "object", "properties": {}},
        "supportedExecUnitTypes": [], "exampleConfigurations": [],
    }]
    server = build_server(replace(cfg, mode=mode))
    async with create_connected_server_and_client_session(server.protocol_server) as session:
        catalog = await session.list_tools()
        assert len(catalog.tools) == (12 if mode is MCPMode.NATIVE else 4)

        async def call(name, arguments):
            if mode is MCPMode.DISPATCH:
                return await session.call_tool("tuoni_call", {"name": name, "arguments": arguments})
            return await session.call_tool(name, arguments)

        result = await call("tuoni_agent_get", {"agent_guid": "network-agent"})
        assert not result.isError
        assert call_result_size(result) <= DETAIL_RESULT_BUDGET
        actual = json.loads(result.content[0].text)["data"]["metadata"]
        assert actual["netInterfaces"] == metadata["netInterfaces"]
        assert actual["capabilities"] == metadata["capabilities"]
        assert actual["customProperties"] == metadata["customProperties"]

        found = await call("tuoni_commands_search", {"agent_guid": "network-agent", "query": "netinfo"})
        assert not found.isError
        commands = json.loads(found.content[0].text)["data"]["commands"]
        assert [(item["id"], item["name"]) for item in commands] == [("server-netinfo", "netinfo")]
        assert all(name == "request_get" for name, *_ in fake_c2.calls)
