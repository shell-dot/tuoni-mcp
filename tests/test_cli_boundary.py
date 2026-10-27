import subprocess
import sys
import json
import os
from dataclasses import replace

import pytest

from tuoni_mcp.config import Settings
from tuoni_mcp import server


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.0.2.1", "remote.example"])
def test_http_cli_rejects_non_loopback_hosts_before_startup(host):
    process = subprocess.run([
        sys.executable, "-m", "tuoni_mcp.server", "--transport", "streamable-http", "--host", host
    ], capture_output=True, text=True, timeout=5)
    assert process.returncode == 2
    assert "HTTP transports are local-only" in process.stderr
    assert not process.stdout


def test_doctor_offline_is_json_and_does_not_start_mcp_or_contact_backend():
    env = {key: value for key, value in os.environ.items() if not key.startswith("TUONI_")}
    env.update(TUONI_URL="https://127.0.0.1:1", TUONI_USERNAME="doctor", TUONI_PASSWORD="secret-marker")
    process = subprocess.run(
        [sys.executable, "-m", "tuoni_mcp.server", "doctor", "--offline"],
        env=env, capture_output=True, text=True, timeout=5,
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["ok"] is True
    assert report["backend"]["status"] == "not_checked"
    assert report["catalog"]["enabled_operations"] == 12
    assert not process.stderr
    assert "secret-marker" not in process.stdout
    assert "127.0.0.1" not in process.stdout


@pytest.mark.parametrize("ok,exit_code", [(True, 0), (False, 1)])
def test_doctor_cli_propagates_report_and_status(monkeypatch, capsys, ok, exit_code):
    cfg = Settings(url="https://example.test", username="u", password="secret", verify=True)
    monkeypatch.setattr(server.Settings, "from_env", lambda: cfg)
    monkeypatch.setattr(sys, "argv", ["tuoni-mcp", "doctor"])

    async def doctor(actual_cfg, *, offline):
        assert actual_cfg == cfg
        assert offline is False
        return {"ok": ok, "backend": {"status": "ok" if ok else "degraded"}}

    monkeypatch.setattr(server, "_doctor", doctor)
    with pytest.raises(SystemExit) as exc:
        server.main()
    assert exc.value.code == exit_code
    assert json.loads(capsys.readouterr().out)["ok"] is ok


async def test_doctor_uses_no_lifespan_and_closes_client_even_on_cancellation(monkeypatch):
    cfg = Settings(url="https://example.test", username="u", password="secret", verify=True)
    import asyncio
    from unittest.mock import MagicMock
    client = MagicMock()
    monkeypatch.setattr(server, "TuoniC2", lambda **kwargs: client)

    async def collect(ctx, *, check_connection, catalog):
        assert ctx.c2 is client
        assert check_connection is True
        assert ctx.event_bridge is None
        assert catalog["enabled_operations"] == 7
        raise asyncio.CancelledError

    monkeypatch.setattr(server, "collect_diagnostics", collect)
    with pytest.raises(asyncio.CancelledError):
        await server._doctor(replace(cfg, read_only=True), offline=False)
    client.close.assert_called_once_with()


@pytest.mark.parametrize("args", [["--offline"], ["doctor", "--offline"]])
def test_doctor_config_errors_exit_two_without_json(args):
    env = {key: value for key, value in os.environ.items() if not key.startswith("TUONI_")}
    process = subprocess.run(
        [sys.executable, "-m", "tuoni_mcp.server", *args],
        env=env, capture_output=True, text=True, timeout=5,
    )
    assert process.returncode == 2
    assert not process.stdout
