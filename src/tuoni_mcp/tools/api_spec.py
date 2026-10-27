"""Live OpenAPI spec introspection from the connected Tuoni server."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from tuoni_mcp.config import ALL_PROFILES, Settings
from tuoni_mcp.connection import call_with_relogin
from tuoni_mcp.pagination import (
    bounded_text,
    compact_json,
    decode_cursor,
    encode_cursor,
    page_coverage,
)
from tuoni_mcp.protocol import (
    DETAIL_RESULT_BUDGET,
    LIST_RESULT_BUDGET,
    would_fit_success,
)
from tuoni_mcp.registry import (
    Effect,
    InvocationContext,
    ToolInput,
    ToolRegistry,
    ToolSpec,
    ToolSuccess,
)


_HTTP_METHODS = frozenset({"get", "post", "put", "delete", "patch"})
_TOOL_NAME = "tuoni_api_spec"
_MAX_REF_DEPTH = 8


class ApiSpecInput(ToolInput):
    filter: Annotated[
        str,
        Field(
            default="",
            max_length=256,
            description=(
                "Case-insensitive search text. "
                "Empty returns a paginated list of every endpoint. "
                "An exact path (e.g. '/api/v1/agents') returns that endpoint's "
                "full schema with component references resolved. "
                "Otherwise lists endpoints whose path, tag, or summary contain the text."
            ),
        ),
    ] = ""
    cursor: Annotated[
        str | None,
        Field(
            default=None,
            description="Continuation cursor from a previous call.",
        ),
    ] = None


def _resolve_refs(node: Any, components: dict[str, Any], depth: int = 0) -> Any:
    """Recursively resolve $ref pointers from the components section."""
    if depth > _MAX_REF_DEPTH:
        return node
    if isinstance(node, dict):
        if "$ref" in node:
            ref_path = node["$ref"]
            if ref_path.startswith("#/components/"):
                parts = ref_path.removeprefix("#/components/").split("/")
                target: Any = components
                for part in parts:
                    if isinstance(target, dict):
                        target = target.get(part)
                    else:
                        return node
                if target is not None:
                    return _resolve_refs(target, components, depth + 1)
            return node
        return {k: _resolve_refs(v, components, depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, components, depth + 1) for item in node]
    return node


def _endpoint_lines(paths: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    """Extract (path, method, tag, summary) tuples sorted by path then method."""
    lines: list[tuple[str, str, str, str]] = []
    for path in sorted(paths):
        for method, operation in sorted(paths[path].items()):
            if method not in _HTTP_METHODS:
                continue
            tag = (operation.get("tags") or [""])[0]
            summary = operation.get("summary", "")
            lines.append((path, method, tag, summary))
    return lines


def register_specs(registry: ToolRegistry, _cfg: Settings) -> None:
    async def api_spec(invocation: InvocationContext, arguments: ApiSpecInput) -> ToolSuccess:
        """Fetch and filter the live OpenAPI spec from the connected server."""
        sctx = invocation.server
        data = await call_with_relogin(sctx, sctx.c2.request_get, "/docs/api")
        if data is None:
            return ToolSuccess("Server returned no data for /docs/api.")

        paths: dict = data.get("paths", {})
        components: dict = data.get("components", {})
        version = data.get("info", {}).get("version", "?")
        query = arguments.filter.strip().lower()

        # ── Exact path match: full schema with resolved $refs ───────────
        if query:
            path_lower_map = {p.lower(): p for p in paths}
            if query in path_lower_map:
                real_path = path_lower_map[query]
                resolved = _resolve_refs(paths[real_path], components)
                detail = {real_path: resolved}
                result_data: dict[str, Any] = {
                    "version": version,
                    "path": real_path,
                    "schema": detail,
                }
                if would_fit_success(result_data, budget=DETAIL_RESULT_BUDGET):
                    return ToolSuccess(result_data, redact_output=False)
                # Oversized: return compact JSON with truncation.
                result_data["schema"] = bounded_text(
                    compact_json(detail), DETAIL_RESULT_BUDGET - 512,
                )
                result_data["truncated"] = True
                result_data["hint"] = (
                    "Schema truncated to fit result budget. "
                    "Narrow with a specific HTTP method path or nested sub-path."
                )
                return ToolSuccess(result_data, redact_output=False)

        # ── List mode: paginated endpoint index ─────────────────────────
        all_lines = _endpoint_lines(paths)
        if query:
            all_lines = [
                line for line in all_lines
                if any(query in text.lower() for text in line)
            ]

        total = len(all_lines)
        offset = 0
        if arguments.cursor:
            state = decode_cursor(arguments.cursor, tool=_TOOL_NAME)
            offset = int(state.get("offset", 0))

        items: list[str] = []
        consumed = offset
        for i in range(offset, total):
            path, method, _tag, summary = all_lines[i]
            line = f"{method.upper():6} {path}  — {summary}"
            candidate_items = [*items, line]
            next_offset = i + 1
            has_more = next_offset < total

            if has_more:
                curs: str | None = encode_cursor(
                    {"tool": _TOOL_NAME, "offset": next_offset},
                )
                ncall: dict[str, Any] | None = {
                    "name": _TOOL_NAME,
                    "arguments": {"filter": arguments.filter, "cursor": curs},
                }
            else:
                curs, ncall = None, None

            candidate_data: dict[str, Any] = {
                "version": version,
                "endpoints": candidate_items,
                "coverage": page_coverage(
                    offset=offset, returned=len(candidate_items),
                    total=total, has_more=has_more,
                ),
            }
            if query:
                candidate_data["filter"] = arguments.filter.strip()

            if not would_fit_success(
                candidate_data,
                next_cursor=curs,
                next_call=ncall,
                budget=LIST_RESULT_BUDGET,
            ):
                break
            items = candidate_items
            consumed = next_offset

        if not items and offset == 0:
            return ToolSuccess({
                "version": version,
                "endpoints": [],
                "coverage": page_coverage(
                    offset=0, returned=0, total=total, has_more=False,
                ),
                "message": "No match. Call with empty filter to list all.",
            })

        has_more = consumed < total
        if has_more:
            final_cursor: str | None = encode_cursor(
                {"tool": _TOOL_NAME, "offset": consumed},
            )
            final_next: dict[str, Any] | None = {
                "name": _TOOL_NAME,
                "arguments": {"filter": arguments.filter, "cursor": final_cursor},
            }
        else:
            final_cursor, final_next = None, None

        result: dict[str, Any] = {
            "version": version,
            "endpoints": items,
            "coverage": page_coverage(
                offset=offset, returned=len(items),
                total=total, has_more=has_more,
            ),
        }
        if query:
            result["filter"] = arguments.filter.strip()

        return ToolSuccess(
            result,
            next_cursor=final_cursor,
            next_call=final_next,
            redact_output=False,
        )

    registry.add(ToolSpec(
        name=_TOOL_NAME,
        description=(
            "Fetch the live OpenAPI specification from the connected Tuoni server. "
            "Always reflects the exact version you are connected to. "
            "Empty filter returns a paginated endpoint index; a path returns its full "
            "schema with component references resolved; text narrows by path, tag, or summary."
        ),
        input_model=ApiSpecInput,
        handler=api_spec,
        profiles=ALL_PROFILES,
        budget=DETAIL_RESULT_BUDGET,
        effect=Effect.READ,
        keywords=(
            "openapi", "swagger", "spec", "specification", "api", "endpoints",
            "schema", "documentation", "reference", "introspection",
        ),
    ))
