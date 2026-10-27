"""Gate the portable evaluation against its committed baseline.

This is the regression barrier for small-model friendliness: it fails when a
change makes the interface complete fewer workflows, emit malformed calls, need
more hops, or return more bytes than the recorded baseline.
"""

from __future__ import annotations

import asyncio
import json
import runpy
from pathlib import Path

import pytest

from evaluation.portable.plans import WORKFLOW_PLANS
from evaluation.portable.runner import PORTABLE_MODES, run_portable_evaluation
from evaluation.portable.scoring import WORKFLOW_IDS, score

ROOT = Path(__file__).parents[1]
RUNNER = runpy.run_path(str(ROOT / "evaluation" / "run_portable_eval.py"))


@pytest.fixture(scope="module")
def evaluated() -> tuple[dict, dict]:
    """Run the whole harness once and score it."""

    document = asyncio.run(run_portable_evaluation())
    report = score(document["run"], document["results"])
    return document, report


def test_plans_cover_every_workflow_exactly_once() -> None:
    covered = [workflow_id for workflow_id, _ in WORKFLOW_PLANS]

    assert tuple(covered) == WORKFLOW_IDS
    assert len(set(covered)) == 20


def test_harness_emits_a_scorable_portable_document(evaluated) -> None:
    document, report = evaluated

    assert document["run"]["kind"] == "portable"
    assert len(document["results"]) == 20 * len(PORTABLE_MODES)
    assert tuple(report["modes"]) == PORTABLE_MODES
    # Catalog identity is the portable run's whole benchmark profile.
    assert report["modes"]["native"]["catalog_tools"] == 12
    assert report["modes"]["dispatch"]["catalog_tools"] == 4


def test_report_identifies_scripted_contract_checks(evaluated) -> None:
    """The harness describes tool contracts without claiming model performance."""

    _document, report = evaluated

    assert report["kind"] == "portable"
    assert "Scripted contract checks" in report["portable_gate"]["note"]
    assert report["portable_gate"]["passed"] is True


def test_every_call_the_scripted_client_makes_is_schema_valid(evaluated) -> None:
    _document, report = evaluated

    for mode in PORTABLE_MODES:
        scored = report["modes"][mode]
        assert scored["valid_tool_call_rate"] == 1.0, (
            f"{mode} emitted a call the advertised schema rejected"
        )
        assert scored["context_overflows"] == 0
        assert scored["unintended_mutations"] == 0


def test_no_regression_against_committed_baseline(evaluated) -> None:
    _document, report = evaluated
    baseline = RUNNER["load_baseline"]()
    assert baseline is not None, "evaluation/portable/baseline.json is missing"

    regressions = RUNNER["compare"](RUNNER["summarize"](report), baseline)

    assert regressions == [], (
        "the portable evaluation regressed against its baseline:\n  - "
        + "\n  - ".join(regressions)
        + "\n\nIf the change is a deliberate improvement, refresh the baseline with:\n"
        "  python evaluation/run_portable_eval.py --update-baseline"
    )


def test_the_baseline_cannot_be_refreshed_below_a_floor() -> None:
    """Refreshing the baseline is a deliberate act, but it must not be able to
    quietly record a regression. These floors hold whatever the file says."""

    baseline = json.loads((ROOT / "evaluation" / "portable" / "baseline.json").read_text(encoding="utf-8"))

    for mode in PORTABLE_MODES:
        recorded = baseline["modes"][mode]
        assert recorded["completed_workflows"] == 20, f"{mode} baseline records a failing workflow"
        assert recorded["valid_tool_call_rate"] == 1.0
        assert recorded["context_overflows"] == 0
        assert recorded["unintended_mutations"] == 0
        # Every response must stay inside the absolute 8 KiB result ceiling.
        assert recorded["max_result_bytes"] <= 8 * 1024


def test_baseline_is_committed_in_the_recorded_shape() -> None:
    baseline = json.loads((ROOT / "evaluation" / "portable" / "baseline.json").read_text(encoding="utf-8"))

    assert set(baseline["modes"]) == set(PORTABLE_MODES)
    for mode in PORTABLE_MODES:
        recorded = baseline["modes"][mode]
        assert recorded["completed_workflows"] <= 20
        assert set(recorded["incomplete_workflows"]) <= set(WORKFLOW_IDS)
