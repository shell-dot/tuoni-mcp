# Tool reference

Generated from `ToolRegistry`; edit the source definitions, then run:

```bash
uv run python scripts/generate_tool_reference.py
uv run python scripts/generate_tool_reference.py --check
```

This reference describes static MCP tools, not the connected server's dynamic command catalog. Schemas below are the exact advertised input schemas. No backend is contacted to generate this file.

## Entry points

The default profile is `agent-ops`. `TUONI_MCP_MODE` selects native or dispatch; `TUONI_MCP_READ_ONLY=true` removes preparation and state-changing operations.

| Mode | Read-only | Exposed default entrypoints |
| --- | --- | --- |
| Native | No | `tuoni_agents_list`, `tuoni_agent_get`, `tuoni_commands_search`, `tuoni_command_describe`, `tuoni_command_prepare`, `tuoni_command_update_prepare`, `tuoni_command_stop_prepare`, `tuoni_operation_execute`, `tuoni_command_get`, `tuoni_commands_list`, `tuoni_capabilities`, `tuoni_api_spec` |
| Native | Yes | `tuoni_agents_list`, `tuoni_agent_get`, `tuoni_commands_search`, `tuoni_command_describe`, `tuoni_command_get`, `tuoni_commands_list`, `tuoni_capabilities`, `tuoni_api_spec` |
| Dispatch | No | `tuoni_find_tool`, `tuoni_tool_schema`, `tuoni_call`, `tuoni_operation_execute` |
| Dispatch | Yes | `tuoni_find_tool`, `tuoni_tool_schema`, `tuoni_call` |

Native mode exposes each selected tool directly. Dispatch mode discovers the selected tools through `tuoni_find_tool`, retrieves one schema with `tuoni_tool_schema`, and routes calls through `tuoni_call`. Mutations submitted through `tuoni_call` produce preparations; `tuoni_operation_execute` executes them. Follow returned continuations exactly.

## Profiles

Set `TUONI_MCP_PROFILES` to comma-separated profile names. `all` expands to `agent-ops`, `access`, `artifacts`, `discovery`, `administration`, `authoring`, `events`. It excludes `raw`, which requires explicit selection and native mode.

Read-only availability below means exposure when `TUONI_MCP_READ_ONLY=true`, not a guarantee of upstream account permissions. Native effects are `read`, `prepare` (local validation/preparation), `execute` (a prepared operation), or `mutate` (immediate remote change).

| Profile | Native tools | Read-only native tools | Included in `all` |
| --- | ---: | ---: | --- |
| `agent-ops` | 12 | 8 | Yes |
| `access` | 20 | 12 | Yes |
| `artifacts` | 10 | 6 | Yes |
| `discovery` | 14 | 5 | Yes |
| `administration` | 21 | 7 | Yes |
| `authoring` | 11 | 8 | Yes |
| `events` | 3 | 3 | Yes |
| `raw` | 3 | 2 | No |

## Dispatch entrypoint schemas

### `tuoni_find_tool`

Find MCP tools by purpose. Matches include input_schema or an exact schema call.

Effect: `read`. Read-only mode: **yes**.

Required arguments: `query`. Response budget: 2,048 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string"
    },
    "limit": {
      "default": 8,
      "maximum": 100,
      "minimum": 1,
      "type": "integer"
    },
    "query": {
      "maxLength": 200,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "query"
  ],
  "type": "object"
}
```

</details>

### `tuoni_tool_schema`

Get an MCP tool's input schema. Agent command templates use tuoni_command_describe.

Effect: `read`. Read-only mode: **yes**.

Required arguments: `name` or `tool_name`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "anyOf": [
    {
      "required": [
        "name"
      ]
    },
    {
      "required": [
        "tool_name"
      ]
    }
  ],
  "properties": {
    "name": {
      "maxLength": 200,
      "minLength": 1,
      "type": "string"
    },
    "tool_name": {
      "maxLength": 200,
      "minLength": 1,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_call`

Call a discovered MCP name with its shown input_schema; otherwise load schema first. Mutations are only prepared.

Effect: `prepare`; `read` in read-only mode. Read-only mode: **yes**.

Required arguments: `name`. Response budget: 8,192 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "additionalProperties": true,
      "type": "object"
    },
    "name": {
      "maxLength": 200,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "name"
  ],
  "type": "object"
}
```

</details>

### `tuoni_operation_execute`

Execute one reviewed operation using its complete opaque preparation ID exactly once. Receipt replay is safe; never create a second command after an ambiguous outcome.

Effect: `execute`. Read-only mode: **no**.

Required arguments: `preparation_id`. Response budget: 8,192 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "preparation_id": {
      "description": "Copy the complete preparation_id from prepare next. Never alter it.",
      "examples": [
        "AbCdEfGhIjKlMnOpQrStUvWxYz012345"
      ],
      "maxLength": 128,
      "minLength": 16,
      "type": "string"
    }
  },
  "required": [
    "preparation_id"
  ],
  "type": "object"
}
```

</details>

## `agent-ops` tools

### `tuoni_agent_get`

Get one agent's platform, status and capability count by guid. Returns no command schemas; use command search for those.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `agent_guid`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_agents_list`

List or search active agents. An agent is a program running on a target machine. Copy a returned guid to work with that agent. Follow next for more pages, even when a search page has no matches.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "default": true,
      "type": "boolean"
    },
    "cursor": {
      "type": "string"
    },
    "inactive": {
      "default": false,
      "type": "boolean"
    },
    "limit": {
      "default": 10,
      "maximum": 25,
      "minimum": 1,
      "type": "integer"
    },
    "process_name": {
      "description": "Exact process basename, case-insensitive.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "query": {
      "description": "Match all case-insensitive words across hostname, process, user, GUID or IP. Each call scans at most 100 agents.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "search": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_command_describe`

Describe a template returned by commands_search, including fields and a complete prepare example. Copy one returned name or ID into template; MCP tool names are not command templates.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `agent_guid`; `template` or `command_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "anyOf": [
    {
      "required": [
        "template"
      ]
    },
    {
      "required": [
        "command_id"
      ]
    }
  ],
  "properties": {
    "agent_guid": {
      "description": "Exact ID from agents_list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "command_id": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "cursor": {
      "type": "string"
    },
    "limit": {
      "default": 8,
      "maximum": 20,
      "minimum": 1,
      "type": "integer"
    },
    "template": {
      "description": "Copy a name or ID returned by commands_search.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_get`

Poll a command's status, list its result parts, or read one text window. Omit part_index for status and the part list. Add part_index with offset_chars and max_chars to read text. Follow next exactly.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `command_id`. Response budget: 8,192 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "command_id": {
      "anyOf": [
        {
          "minimum": 0,
          "type": "integer"
        },
        {
          "not": {
            "pattern": "[^0-9]"
          },
          "pattern": "^(0|[1-9][0-9]{0,17})$",
          "type": "string"
        }
      ]
    },
    "cursor": {
      "description": "Manifest only; copy next_cursor.",
      "type": "string"
    },
    "limit": {
      "default": 20,
      "description": "Manifest part count; omit with part_index.",
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "max_chars": {
      "default": 4096,
      "description": "Text characters; requires part_index.",
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    },
    "offset_chars": {
      "default": 0,
      "description": "Text only; requires part_index.",
      "minimum": 0,
      "type": "integer"
    },
    "part_index": {
      "description": "Text only: exact manifest part_index. Omit for status/manifest.",
      "minimum": 0,
      "type": "integer"
    },
    "result_version": {
      "description": "Text snapshot: copy from manifest or next.",
      "pattern": "^[0-9a-f]{64}$",
      "type": "string"
    },
    "wait_seconds": {
      "default": 0,
      "description": "Status/manifest only: total read wait.",
      "maximum": 30,
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "command_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_prepare`

Validate a command and hold it. Nothing reaches the agent until you execute it. Copy every prepare_arguments_example field, including template. Fill shell_command if shown; otherwise use its exact configuration fields. Execute the returned ID once.

Profiles: `agent-ops`. Native effect: `prepare`. Read-only mode: **no**. Dispatch: called through `tuoni_call`.

Required arguments: `agent_guid`, `template`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "$defs": {
    "Attachment": {
      "additionalProperties": false,
      "properties": {
        "content_base64": {
          "description": "Inline base64; max 4 KiB decoded total.",
          "maxLength": 8192,
          "type": "string"
        },
        "field": {
          "description": "Exact attachment field from describe.",
          "maxLength": 128,
          "minLength": 1,
          "type": "string"
        },
        "file_id": {
          "description": "Existing C2 artifact ID; do not combine with inline data.",
          "maxLength": 256,
          "type": "string"
        },
        "filename": {
          "description": "Required filename for a small inline attachment.",
          "maxLength": 256,
          "type": "string"
        }
      },
      "required": [
        "field"
      ],
      "type": "object"
    },
    "Existing": {
      "additionalProperties": false,
      "properties": {
        "execType": {
          "const": "EXISTING",
          "type": "string"
        },
        "execUnitType": {
          "description": "Optional describe-listed format.",
          "enum": [
            "SHELLCODE_NATIVE",
            "DOTNET_EXE",
            "DOTNET_DLL",
            "NATIVE_LIB"
          ],
          "type": "string"
        },
        "pid": {
          "minimum": 1,
          "type": "integer"
        }
      },
      "required": [
        "execType",
        "pid"
      ],
      "type": "object"
    },
    "New": {
      "additionalProperties": false,
      "properties": {
        "execType": {
          "const": "NEW",
          "type": "string"
        },
        "execUnitType": {
          "description": "Optional describe-listed format.",
          "enum": [
            "SHELLCODE_NATIVE",
            "DOTNET_EXE",
            "DOTNET_DLL",
            "NATIVE_LIB"
          ],
          "type": "string"
        },
        "executable": {
          "maxLength": 1024,
          "minLength": 1,
          "type": "string"
        },
        "password": {
          "maxLength": 1024,
          "minLength": 1,
          "type": "string"
        },
        "ppid": {
          "minimum": 0,
          "type": "integer"
        },
        "suspended": {
          "type": "boolean"
        },
        "username": {
          "maxLength": 512,
          "minLength": 1,
          "type": "string"
        }
      },
      "required": [
        "execType",
        "executable"
      ],
      "type": "object"
    },
    "Self": {
      "additionalProperties": false,
      "properties": {
        "execType": {
          "const": "SELF",
          "type": "string"
        },
        "execUnitType": {
          "description": "Optional describe-listed format.",
          "enum": [
            "SHELLCODE_NATIVE",
            "DOTNET_EXE",
            "DOTNET_DLL",
            "NATIVE_LIB"
          ],
          "type": "string"
        }
      },
      "required": [
        "execType"
      ],
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "description": "Exact ID from agents_list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "attachments": {
      "items": {
        "$ref": "#/$defs/Attachment"
      },
      "maxItems": 32,
      "type": "array"
    },
    "configuration": {
      "additionalProperties": true,
      "description": "Exact describe-listed fields for non-shell templates; never generic args.",
      "type": "object"
    },
    "execution": {
      "description": "Optional plugin execution object with execType SELF, NEW+executable, or EXISTING+pid. Omit for embedded/native commands.",
      "discriminator": {
        "mapping": {
          "EXISTING": "#/$defs/Existing",
          "NEW": "#/$defs/New",
          "SELF": "#/$defs/Self"
        },
        "propertyName": "execType"
      },
      "oneOf": [
        {
          "$ref": "#/$defs/Self"
        },
        {
          "$ref": "#/$defs/New"
        },
        {
          "$ref": "#/$defs/Existing"
        }
      ]
    },
    "shell_command": {
      "description": "Flat shell text when describe's example offers this field.",
      "maxLength": 65536,
      "minLength": 1,
      "type": "string"
    },
    "template": {
      "description": "Copy a name or ID returned by commands_search.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid",
    "template"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_stop_prepare`

Validate stopping or cancelling one command that has not finished. Nothing changes until you execute the returned preparation id.

Profiles: `agent-ops`. Native effect: `prepare`. Read-only mode: **no**. Dispatch: called through `tuoni_call`.

Required arguments: `command_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "command_id": {
      "description": "Exact returned command ID.",
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "command_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_update_prepare`

Validate an update for a command that is still running, such as more stdin. Nothing is sent until you execute the returned preparation id.

Profiles: `agent-ops`. Native effect: `prepare`. Read-only mode: **no**. Dispatch: called through `tuoni_call`.

Required arguments: `command_id`, `configuration`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "$defs": {
    "Attachment": {
      "additionalProperties": false,
      "properties": {
        "content_base64": {
          "description": "Inline base64; max 4 KiB decoded total.",
          "maxLength": 8192,
          "type": "string"
        },
        "field": {
          "description": "Exact attachment field from describe.",
          "maxLength": 128,
          "minLength": 1,
          "type": "string"
        },
        "file_id": {
          "description": "Existing C2 artifact ID; do not combine with inline data.",
          "maxLength": 256,
          "type": "string"
        },
        "filename": {
          "description": "Required filename for a small inline attachment.",
          "maxLength": 256,
          "type": "string"
        }
      },
      "required": [
        "field"
      ],
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "attachments": {
      "items": {
        "$ref": "#/$defs/Attachment"
      },
      "maxItems": 32,
      "type": "array"
    },
    "command_id": {
      "description": "Exact returned command ID.",
      "minimum": 0,
      "type": "integer"
    },
    "configuration": {
      "additionalProperties": true,
      "description": "Exact describe-listed update fields; interactive input is commonly {'stdin':['text']}. Never guess create fields.",
      "type": "object"
    },
    "persistence_type": {
      "default": "TRANSIENT",
      "enum": [
        "TRANSIENT",
        "PERSISTENT"
      ],
      "type": "string"
    }
  },
  "required": [
    "command_id",
    "configuration"
  ],
  "type": "object"
}
```

</details>

### `tuoni_commands_list`

List a page of command history, newest IDs first. Status counts describe only returned records. coverage.complete means the full filtered inventory is in this response. Follow next; restart and deduplicate IDs if history changes.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
      "type": "string"
    },
    "cursor": {
      "maxLength": 2048,
      "minLength": 1,
      "type": "string"
    },
    "limit": {
      "default": 10,
      "maximum": 25,
      "minimum": 1,
      "type": "integer"
    },
    "status": {
      "enum": [
        "CREATED",
        "SENT",
        "ONGOING",
        "CANCELED",
        "FAILED",
        "COMPLETE"
      ],
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_commands_search`

Find an agent's command templates by intent or exact name. Omit agent_guid to select an agent first. Returns short names; describe one before preparing it.

Profiles: `agent-ops`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "description": "Exact ID from agents_list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "cursor": {
      "type": "string"
    },
    "limit": {
      "default": 8,
      "maximum": 20,
      "minimum": 1,
      "type": "integer"
    },
    "query": {
      "default": "",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_operation_execute`

Execute one reviewed operation using its complete opaque preparation ID exactly once. Receipt replay is safe; never create a second command after an ambiguous outcome.

Profiles: `agent-ops`. Native effect: `execute`. Read-only mode: **no**. Dispatch: execute entrypoint.

Required arguments: `preparation_id`. Response budget: 8,192 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "preparation_id": {
      "description": "Copy the complete preparation_id from prepare next. Never alter it.",
      "examples": [
        "AbCdEfGhIjKlMnOpQrStUvWxYz012345"
      ],
      "maxLength": 128,
      "minLength": 16,
      "type": "string"
    }
  },
  "required": [
    "preparation_id"
  ],
  "type": "object"
}
```

</details>

## `access` tools

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_listener_create`

Create a new listener. Describe a tuoni_listener_plugins_list ID with tuoni_listener_plugin_get first. `configuration` matches the plugin's configuration_schema. `files` is optional multipart attachments [{name, filename, content_base64}].

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `plugin_id`, `configuration`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "additionalProperties": true,
      "type": "object"
    },
    "files": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array"
    },
    "name": {
      "type": "string"
    },
    "plugin_id": {
      "type": "string"
    }
  },
  "required": [
    "plugin_id",
    "configuration"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_delete`

Delete a listener.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `listener_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "listener_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_get`

Fetch a single listener by id.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `listener_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "listener_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_plugin_get`

Read one listener-plugin configuration schema/examples. Large details use value_json windows: follow next, concatenate, then parse JSON. DETAIL_CHANGED requires restarting.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `plugin_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "max_chars": {
      "default": 4096,
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    },
    "plugin_id": {
      "maxLength": 512,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "required": [
    "plugin_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_plugins_list`

List compact listener-plugin summaries; follow detail for the configuration schema and examples. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_listener_start`

Start a stopped listener.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `listener_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "listener_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_stop`

Stop a running listener.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `listener_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "listener_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listener_update`

Update an existing listener's name and/or configuration.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `listener_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "additionalProperties": true,
      "type": "object"
    },
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    },
    "name": {
      "type": "string"
    }
  },
  "required": [
    "listener_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_listeners_list`

List all listeners (communication channels for agent callbacks). Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_payload_create`

Create a new payload. `template` is a payload template id (e.g. from tuoni_payload_plugin_templates_list). Describe it with tuoni_payload_template_get first. `listener_id` ties the payload to a callback listener. `configuration` matches the template's configuration_schema. Returns the new payload id.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `template`, `listener_id`, `configuration`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "additionalProperties": true,
      "type": "object"
    },
    "encrypted": {
      "default": true,
      "type": "boolean"
    },
    "listener_id": {
      "minimum": 1,
      "type": "integer"
    },
    "name": {
      "type": "string"
    },
    "template": {
      "type": "string"
    }
  },
  "required": [
    "template",
    "listener_id",
    "configuration"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_delete`

Delete a payload.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `payload_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "payload_id": {
      "description": "Exact payload ID returned by tuoni_payloads_list or creation.",
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "payload_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_download`

Return bounded payload metadata and an authenticated HTTP download reference. This tool never builds, fetches, or embeds the payload binary in model context.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `payload_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "payload_id": {
      "description": "Exact payload ID returned by tuoni_payloads_list or creation.",
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "payload_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_get`

Fetch a single payload by id.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `payload_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "payload_id": {
      "description": "Exact payload ID returned by tuoni_payloads_list or creation.",
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "payload_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_plugin_templates_list`

List compact templates for one payload plugin; follow detail for configuration fields and examples. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `plugin_id`. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "plugin_id": {
      "maxLength": 512,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "required": [
    "plugin_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_plugins_list`

List compact payload-plugin summaries. Follow detail to list templates, then describe one before creating a payload. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_payload_rename`

Rename a payload.

Profiles: `access`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `payload_id`, `new_name`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "new_name": {
      "type": "string"
    },
    "payload_id": {
      "description": "Exact payload ID returned by tuoni_payloads_list or creation.",
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "payload_id",
    "new_name"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payload_template_get`

Read one payload template's configuration schema/examples. Large details use value_json windows: follow next, concatenate, then parse JSON. On DETAIL_CHANGED, discard windows and restart without cursor.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `template_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "max_chars": {
      "default": 4096,
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    },
    "template_id": {
      "maxLength": 512,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "required": [
    "template_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_payloads_list`

List generated payloads. Set include_non_active=true to also see archived ones. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `access`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "include_non_active": {
      "default": false,
      "type": "boolean"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

## `artifacts` tools

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_command_file_download`

Save one command-result file to the configured local download directory. Copy command_id and file part_index from command_get; then read local_path.

Profiles: `artifacts`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `command_id`, `part_index`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "command_id": {
      "description": "Exact returned command ID.",
      "minimum": 0,
      "type": "integer"
    },
    "part_index": {
      "description": "Exact file part_index from command_get manifest.",
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "command_id",
    "part_index"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_delete`

Delete a hosted file by its file_id (GUID).

Profiles: `artifacts`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `file_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "file_id": {
      "description": "Exact hosted-file ID from the hosted-file list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "file_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_delete_by_path`

Delete a hosted file by its hosted path (e.g. '/payloads/agent.exe').

Profiles: `artifacts`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `path`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "path": {
      "description": "Exact hosted path.",
      "maxLength": 2048,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "path"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_download`

Return an HTTP reference for an already-hosted C2 file; do not use for an agent command-result file. This tool never fetches or embeds the body.

Profiles: `artifacts`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `file_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "file_id": {
      "description": "Exact hosted-file ID from the hosted-file list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "file_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_get_by_path`

Fetch a hosted file's metadata by its hosted path (e.g. '/payloads/agent.exe').

Profiles: `artifacts`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `path`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "path": {
      "description": "Exact hosted path.",
      "maxLength": 2048,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "path"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_replace`

Replace a hosted file using exactly one of content_base64 or a staged local_path on the MCP server.

Profiles: `artifacts`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `file_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "content_base64": {
      "type": "string"
    },
    "file_id": {
      "description": "Exact hosted-file ID from the hosted-file list.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "local_path": {
      "description": "File under TUONI_MCP_UPLOAD_DIR on the MCP server; relative paths start there.",
      "maxLength": 4096,
      "minLength": 1,
      "type": "string"
    },
    "original_filename": {
      "type": "string"
    }
  },
  "required": [
    "file_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_file_upload`

Upload a file to the C2's hosted-files store. `hosted_path` is where the C2 will host it (e.g. '/artifacts/report.txt'). Provide exactly one of content_base64 or local_path under the configured MCP-server staging directory; original_filename defaults to the source basename.

Profiles: `artifacts`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `hosted_path`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "content_base64": {
      "type": "string"
    },
    "hosted_path": {
      "description": "Exact hosted path.",
      "maxLength": 2048,
      "minLength": 1,
      "type": "string"
    },
    "local_path": {
      "description": "File under TUONI_MCP_UPLOAD_DIR on the MCP server; relative paths start there.",
      "maxLength": 4096,
      "minLength": 1,
      "type": "string"
    },
    "original_filename": {
      "type": "string"
    }
  },
  "required": [
    "hosted_path"
  ],
  "type": "object"
}
```

</details>

### `tuoni_files_list`

List hosted files (uploaded artifacts the C2 can serve to agents/listeners). Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `artifacts`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

## `discovery` tools

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_credential_add`

Add a credential entry to the discovery data model.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `username`, `password`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "host": {
      "default": "",
      "type": "string"
    },
    "note": {
      "default": "",
      "type": "string"
    },
    "password": {
      "type": "string"
    },
    "realm": {
      "default": "",
      "type": "string"
    },
    "source": {
      "default": "",
      "type": "string"
    },
    "username": {
      "type": "string"
    }
  },
  "required": [
    "username",
    "password"
  ],
  "type": "object"
}
```

</details>

### `tuoni_credential_archive`

Archive a credential entry.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `credential_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "credential_id": {
      "type": "string"
    }
  },
  "required": [
    "credential_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_credential_update`

Update source/note for a credential.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `credential_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "credential_id": {
      "type": "string"
    },
    "note": {
      "type": "string"
    },
    "source": {
      "type": "string"
    }
  },
  "required": [
    "credential_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_credentials_list`

List Tuoni's stored credential records with backend filters and redacted secrets. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `discovery`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "filter": {
      "description": "URL-encoded backend query; cannot be combined with typed filters.",
      "type": "string"
    },
    "host": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "include_archived": {
      "description": "Include archived records; omitted means active records only.",
      "type": "boolean"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "page": {
      "default": 0,
      "description": "Zero-based page index.",
      "minimum": 0,
      "type": "integer"
    },
    "page_size": {
      "default": 20,
      "description": "Rows per page (1-1000).",
      "maximum": 1000,
      "minimum": 1,
      "type": "integer"
    },
    "realm": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "search": {
      "description": "Substring to find across the stored record's searchable fields.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "source": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "username": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_host_add`

Add a host entry to the discovery data model.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `address`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "address": {
      "type": "string"
    },
    "name": {
      "default": "",
      "type": "string"
    },
    "note": {
      "default": "",
      "type": "string"
    }
  },
  "required": [
    "address"
  ],
  "type": "object"
}
```

</details>

### `tuoni_host_archive`

Archive a host entry.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `host_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "host_id": {
      "type": "string"
    }
  },
  "required": [
    "host_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_host_update`

Update name/note for an existing host.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `host_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "host_id": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "note": {
      "type": "string"
    }
  },
  "required": [
    "host_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_hosts_list`

List Tuoni's stored host records with backend filters; this does not scan hosts. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `discovery`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "address": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "filter": {
      "description": "URL-encoded backend query; cannot be combined with typed filters.",
      "type": "string"
    },
    "include_archived": {
      "description": "Include archived records; omitted means active records only.",
      "type": "boolean"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "name": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "page": {
      "default": 0,
      "description": "Zero-based page index.",
      "minimum": 0,
      "type": "integer"
    },
    "page_size": {
      "default": 20,
      "description": "Rows per page (1-1000).",
      "maximum": 1000,
      "minimum": 1,
      "type": "integer"
    },
    "search": {
      "description": "Substring to find across the stored record's searchable fields.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_service_add`

Add a service entry to the discovery data model.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `address`, `port`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "address": {
      "type": "string"
    },
    "banner": {
      "default": "",
      "type": "string"
    },
    "note": {
      "default": "",
      "type": "string"
    },
    "port": {
      "type": "integer"
    },
    "protocol": {
      "default": "",
      "type": "string"
    }
  },
  "required": [
    "address",
    "port"
  ],
  "type": "object"
}
```

</details>

### `tuoni_service_archive`

Archive a service entry.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `service_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "service_id": {
      "type": "string"
    }
  },
  "required": [
    "service_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_service_update`

Update protocol/banner/note for a service.

Profiles: `discovery`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `service_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "banner": {
      "type": "string"
    },
    "note": {
      "type": "string"
    },
    "protocol": {
      "type": "string"
    },
    "service_id": {
      "type": "string"
    }
  },
  "required": [
    "service_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_services_list`

List Tuoni's stored service records with backend filters; this does not probe services. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `discovery`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "address": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "filter": {
      "description": "URL-encoded backend query; cannot be combined with typed filters.",
      "type": "string"
    },
    "include_archived": {
      "description": "Include archived records; omitted means active records only.",
      "type": "boolean"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "page": {
      "default": 0,
      "description": "Zero-based page index.",
      "minimum": 0,
      "type": "integer"
    },
    "page_size": {
      "default": 20,
      "description": "Rows per page (1-1000).",
      "maximum": 1000,
      "minimum": 1,
      "type": "integer"
    },
    "port": {
      "description": "Exact service port.",
      "maximum": 65535,
      "minimum": 0,
      "type": "integer"
    },
    "protocol": {
      "description": "Exact match; use * at either end for a partial match.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "search": {
      "description": "Substring to find across the stored record's searchable fields.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

## `administration` tools

### `tuoni_agent_block`

Block an agent.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `agent_guid`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_agent_clear_queue`

Clear an agent's pending command queue.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `agent_guid`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_agent_restore`

Restore a blocked agent.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `agent_guid`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_agent_set_custom_property`

Set or remove one agent custom property.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `agent_guid`, `name`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "name": {
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "value": {}
  },
  "required": [
    "agent_guid",
    "name"
  ],
  "type": "object"
}
```

</details>

### `tuoni_agent_set_inactive`

Mark an agent inactive.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `agent_guid`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "agent_guid": {
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "agent_guid"
  ],
  "type": "object"
}
```

</details>

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_job_get`

Read one job including messages/resources. Large details use value_json windows: follow next, concatenate, then parse JSON. DETAIL_CHANGED requires restarting.

Profiles: `administration`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `job_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "job_id": {
      "minimum": 1,
      "type": "integer"
    },
    "max_chars": {
      "default": 4096,
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "job_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_job_pause`

Pause a running job.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `job_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "job_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "job_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_job_restart`

Restart a persistent job.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `job_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "job_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "job_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_job_resume`

Resume a paused job.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `job_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "job_id": {
      "minimum": 1,
      "type": "integer"
    }
  },
  "required": [
    "job_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_jobs_list`

List compact background-job summaries; follow detail for messages/resources. include_inactive includes finished/stopped jobs. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `administration`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "include_inactive": {
      "default": false,
      "type": "boolean"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "page": {
      "default": 0,
      "description": "Zero-based page index.",
      "minimum": 0,
      "type": "integer"
    },
    "page_size": {
      "default": 20,
      "description": "Rows per page (1-1000).",
      "maximum": 1000,
      "minimum": 1,
      "type": "integer"
    },
    "sort_col": {
      "default": "id",
      "type": "string"
    },
    "sort_order": {
      "default": "asc",
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_setting_get`

Retrieve one setting by exact key. Small values retain their native response shape. Oversized values return reconstructable, redacted JSON text windows; follow the opaque cursor until next is null, concatenate value_json, then parse JSON.

Profiles: `administration`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `key`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Opaque continuation cursor.",
      "maxLength": 2048,
      "type": "string"
    },
    "key": {
      "description": "Exact Tuoni setting key.",
      "maxLength": 512,
      "minLength": 1,
      "type": "string"
    },
    "max_chars": {
      "default": 4096,
      "description": "Maximum JSON characters requested.",
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    },
    "offset_chars": {
      "default": 0,
      "description": "Character offset for an initial JSON value window.",
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "key"
  ],
  "type": "object"
}
```

</details>

### `tuoni_setting_update`

Update a single setting by key. `value` must be JSON-serialisable.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `key`, `value`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "key": {
      "type": "string"
    },
    "value": {}
  },
  "required": [
    "key",
    "value"
  ],
  "type": "object"
}
```

</details>

### `tuoni_settings_get_all`

Retrieve all server settings (both core 'server' and 'plugin' sections). Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `administration`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_settings_update_bulk`

Bulk-update multiple settings in one call. `settings` follows Tuoni's AllSettingsUpdateRequest schema (a mapping of setting key to new value).

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `settings`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "settings": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  "required": [
    "settings"
  ],
  "type": "object"
}
```

</details>

### `tuoni_user_create`

Create a new Tuoni user. `authorities` is a list of permissions such as ['MANAGE_LISTENERS','MANAGE_USERS','SEND_COMMANDS','MANAGE_PAYLOADS','MODIFY_FILES','VIEW_RESOURCES','MANAGE_AGENTS','MANAGE_DISCOVERY','MANAGE_JOBS'].

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `username`, `password`, `authorities`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "authorities": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "password": {
      "type": "string"
    },
    "username": {
      "type": "string"
    }
  },
  "required": [
    "username",
    "password",
    "authorities"
  ],
  "type": "object"
}
```

</details>

### `tuoni_user_set_authorities`

Replace a user's permission set.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `username`, `authorities`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "authorities": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "username": {
      "type": "string"
    }
  },
  "required": [
    "username",
    "authorities"
  ],
  "type": "object"
}
```

</details>

### `tuoni_user_set_enabled`

Enable or disable a user.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `username`, `enabled`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "username": {
      "type": "string"
    }
  },
  "required": [
    "username",
    "enabled"
  ],
  "type": "object"
}
```

</details>

### `tuoni_user_set_password`

Set a new password for a user.

Profiles: `administration`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `username`, `new_password`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "new_password": {
      "type": "string"
    },
    "username": {
      "type": "string"
    }
  },
  "required": [
    "username",
    "new_password"
  ],
  "type": "object"
}
```

</details>

### `tuoni_users_list`

List all users defined on the Tuoni server. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `administration`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

## `authoring` tools

### `tuoni_alias_create`

Create a new command alias on top of an existing base template. `command_type` is a template id (UUID) or its short name (e.g. 'ls', 'bof'). `configuration` becomes the alias's fixed configuration. `files` is optional multipart attachments [{name, filename, content_base64}].

Profiles: `authoring`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `name`, `description`, `command_type`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "command_type": {
      "type": "string"
    },
    "configuration": {
      "additionalProperties": true,
      "type": "object"
    },
    "description": {
      "type": "string"
    },
    "files": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array"
    },
    "name": {
      "type": "string"
    }
  },
  "required": [
    "name",
    "description",
    "command_type"
  ],
  "type": "object"
}
```

</details>

### `tuoni_alias_delete`

Archive a command alias by alias_id (UUID). Idempotent; archived aliases stay retrievable by id.

Profiles: `authoring`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `alias_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "alias_id": {
      "type": "string"
    }
  },
  "required": [
    "alias_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_alias_download_file`

Return an authenticated HTTP reference for an alias configuration file. This tool never fetches or embeds the file body in model context.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `alias_id`, `file_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "alias_id": {
      "description": "Exact command-alias ID.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    },
    "file_id": {
      "description": "Exact configuration-file ID from the alias metadata.",
      "maxLength": 256,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "alias_id",
    "file_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_alias_get`

Fetch a single command alias by id (works for ACTIVE and ARCHIVED aliases). Note: editing an alias archives the previous version and creates a new one, so old ids continue to resolve via this endpoint.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `alias_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "alias_id": {
      "type": "string"
    }
  },
  "required": [
    "alias_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_alias_update`

Edit an alias's description and/or fixed configuration. Description-only edits update in place (same id). Changing the fixed configuration triggers an archive-then-create: the original is archived and a new alias (same name, fresh id) takes its place - the response then includes a 'previous_alias_id' for the archived entry. Both fields are optional and merge with the current state. Existing files are preserved; configuration must contain JSON fields without @files metadata. The name cannot be changed via this endpoint - delete and recreate to rename.

Profiles: `authoring`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: prepared through `tuoni_call`.

Required arguments: `alias_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "alias_id": {
      "type": "string"
    },
    "configuration": {
      "additionalProperties": true,
      "type": "object"
    },
    "description": {
      "type": "string"
    }
  },
  "required": [
    "alias_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_aliases_list`

List ACTIVE command aliases (shortcuts to base templates with fixed configuration). Archived aliases are excluded; fetch one by id with tuoni_alias_get. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_command_plugin_command_get`

Read one installed command template's schema/examples without an agent. Large details use value_json windows: follow next, concatenate, then parse JSON. On DETAIL_CHANGED, discard windows and restart without cursor.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `plugin_id`, `template_id`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "max_chars": {
      "default": 4096,
      "maximum": 16384,
      "minimum": 1,
      "type": "integer"
    },
    "plugin_id": {
      "description": "Exact command-plugin ID returned by tuoni_command_plugins_list.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    },
    "template_id": {
      "maxLength": 512,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "required": [
    "plugin_id",
    "template_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_plugin_commands_list`

List compact templates for one command plugin. Copy plugin_id exactly; follow detail for the configuration schema and examples. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: `plugin_id`. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "plugin_id": {
      "description": "Exact command-plugin ID returned by tuoni_command_plugins_list.",
      "maxLength": 256,
      "minLength": 1,
      "pattern": "\\S",
      "type": "string"
    }
  },
  "required": [
    "plugin_id"
  ],
  "type": "object"
}
```

</details>

### `tuoni_command_plugins_list`

List compact installed command-plugin summaries. Use tuoni_command_plugin_commands_list with one exact plugin_id to inspect its template summaries; follow their detail calls for configuration schemas. Follow next until null. coverage describes this response only; complete means the whole inventory is in this response, and total:null means unknown.

Profiles: `authoring`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

</details>

## `events` tools

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_events_poll`

Poll before an action to subscribe from now; use start:earliest after an action to replay retained events. The topics input enumerates every supported source URI. Default first poll skips earlier events. Empty events does not mean an empty buffer: inspect earliest_sequence/latest_sequence. Replay is bounded process-local history. Follow next unchanged; start is only for a first poll.

Profiles: `events`. Native effect: `read`. Read-only mode: **yes**. Dispatch: called through `tuoni_call`.

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Opaque cursor returned by the preceding poll; omit to start now.",
      "maxLength": 2048,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "maximum": 50,
      "minimum": 1,
      "type": "integer"
    },
    "start": {
      "description": "First poll only: now (default) subscribes before an action; earliest replays retained events after an action. Omit when following a cursor. Retention is process-local and bounded.",
      "enum": [
        "now",
        "earliest"
      ],
      "type": "string"
    },
    "topics": {
      "description": "Optional event source URIs from this schema's enum; omit for all sources.",
      "items": {
        "enum": [
          "tuoni://events/agents/new",
          "tuoni://events/agents/heartbeat",
          "tuoni://events/agents/active",
          "tuoni://events/agents/metadata",
          "tuoni://events/commands/sent",
          "tuoni://events/commands/results",
          "tuoni://events/listeners/new",
          "tuoni://events/listeners/modified",
          "tuoni://events/listeners/removed",
          "tuoni://events/payloads/new",
          "tuoni://events/payloads/archived",
          "tuoni://events/users/new",
          "tuoni://events/users/modified",
          "tuoni://events/command-templates/new",
          "tuoni://events/command-templates/removed"
        ],
        "type": "string"
      },
      "maxItems": 15,
      "type": "array"
    }
  },
  "type": "object"
}
```

</details>

## `raw` tools

### `tuoni_api_spec`

Fetch the live OpenAPI specification from the connected Tuoni server. Always reflects the exact version you are connected to. Empty filter returns a paginated endpoint index; a path returns its full schema with component references resolved; text narrows by path, tag, or summary.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "Continuation cursor from a previous call.",
      "type": "string"
    },
    "filter": {
      "default": "",
      "description": "Case-insensitive search text. Empty returns a paginated list of every endpoint. An exact path (e.g. '/api/v1/agents') returns that endpoint's full schema with component references resolved. Otherwise lists endpoints whose path, tag, or summary contain the text.",
      "maxLength": 256,
      "type": "string"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_capabilities`

Show enabled profiles, limits, and missing-capability reasons. Optionally check backend version and identity.

Profiles: `access`, `administration`, `agent-ops`, `artifacts`, `authoring`, `discovery`, `events`, `raw`. Native effect: `read`. Read-only mode: **yes**. Dispatch: unavailable (raw is native-only).

Required arguments: None. Response budget: 4,096 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "check_connection": {
      "default": false,
      "type": "boolean"
    }
  },
  "type": "object"
}
```

</details>

### `tuoni_raw_request`

Advanced escape hatch: send an arbitrary HTTP request to the Tuoni server. Prefer profile-scoped typed tools when they exist. Large responses fail the global 8 KiB result ceiling; narrow the server query instead of requesting bulk data. method = GET|POST|PUT|PATCH|DELETE. uri starts with '/' (e.g. '/api/v1/agents'). When read_only mode is enabled, only GET is permitted.

Profiles: `raw`. Native effect: `mutate`. Read-only mode: **no**. Dispatch: unavailable (raw is native-only).

Required arguments: `method`, `uri`. Response budget: 6,144 bytes.

<details>
<summary>Exact input schema</summary>

```json
{
  "additionalProperties": false,
  "properties": {
    "files": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array"
    },
    "json_body": {
      "additionalProperties": true,
      "type": "object"
    },
    "method": {
      "type": "string"
    },
    "uri": {
      "type": "string"
    }
  },
  "required": [
    "method",
    "uri"
  ],
  "type": "object"
}
```

</details>
