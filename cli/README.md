# agent_fleet CLI (`agentctl`)

Click-based **operator CLI** for the fleet manager gRPC API. Commands talk to **`FleetManagerClient`** (`packages.fleet_sdk`) to register agents, inspect status, and manage goals, tasks, and plans. Responses are formatted by **`printer.py`** so command handlers stay thin.

Deploy/undeploy subcommands remain **commented out** in **`agentctl.py`** until the server exposes matching RPCs.

## Installation and entrypoints

After editable install from **repo root**:

```bash
agentctl --help
```

Alternative:

```bash
python -m cli.agentctl --help
```

Requires a reachable **fleet-server** (gRPC target from shared config / environment — same defaults as other fleet SDK clients).

## Modules

| File | Role |
|------|------|
| **`agentctl.py`** | Click command tree, YAML validation on register |
| **`printer.py`** | **`print_agent`**, **`print_task`**, **`print_plan`** (verbose DAG via Kahn sort), strategy enum maps |
| **`__init__.py`** | Package marker |

## Configuration validation

**`register`** loads agent YAML through **`YAMLValidator`** (`packages.agent_sdk.src.schema.yaml_validator`). Invalid configs print to stderr and exit **1** before any gRPC call.

**`load_agent_config(path)`** is shared by register flows; empty paths raise **`click.UsageError`**.

## Command reference

### Top-level agent commands

| Command | Purpose |
|---------|---------|
| **`register CONFIG [AGENT_ID]`** | Register one or more agents (`--num N`); optional **`--host`** / **`--port`** overrides |
| **`unregister AGENT_ID`** | Remove registration |
| **`list`** | List agents; **`--filter`** `all` \| `deployed` \| `registered`; **`-v`** includes tasks |
| **`status AGENT_ID`** | Agent state + optional verbose task dump |

### `goal` group

Nested commands for goal lifecycle (create, list, get, cancel — see **`agentctl.py`** **`@goal.command`** definitions). Planning strategy flags map through **`PLANNING_STRATEGY_CHOICES`** in **`printer.py`** (`monolithic`, `dag`, `big_dag`, `manual`, …).

### `task` group

Create, list, get, and cancel tasks assigned through the fleet manager. Use **`-v`** on list/get for full protobuf fields pretty-printed.

### `plan` group

Plan creation and inspection for allocator/planner experiments:

```bash
agentctl plan create dag llm 1
agentctl plan list -v
```

**`ALLOCATION_STRATEGY_CHOICES`**: `lp`, `llm`, `cost_based`, `none`, `manual`, …

## Typical operator flows

**Register a catalog agent after local fleet-server is up:**

```bash
cd .
agentctl register agents/frontend/architecture/requirements/config.yaml
agentctl list -v
```

**Bulk register numbered workers** (when configs share a base id pattern):

```bash
agentctl register agents/backend/placement/placement_lead/config.yaml --num 3
```

**Inspect planning state:**

```bash
agentctl goal list
agentctl plan create monolithic llm 1
agentctl status my_agent_id -v
```

## Error handling

- gRPC failures and unexpected exceptions → message on stderr, exit **1**
- **`print_response`** standardizes success/failure envelopes from fleet RPCs
- Verbose list/status warns when a referenced **`task_id`** no longer exists

## Relationship to Compose-first dev

Many developers never **`register`** manually — **`scripts/startup.sh`** renders agent Compose services that self-register or expose health endpoints. **`agentctl`** is still the supported path for:

- Ad-hoc registration against a long-running fleet-server
- Goal/task/plan experiments on the control plane
- Operator debugging when the dashboard or gateway is misconfigured

## Related documentation

| Document | Topic |
|----------|--------|
| [`../docs/RUN.md`](../docs/RUN.md) | Start fleet-server and agents |
| [`../agents/README.md`](../agents/README.md) | Agent **`config.yaml`** schema |
| [`../packages/fleet_sdk/`](../packages/fleet_sdk/) | gRPC client implementation |
| [`../scripts/check_agents.py`](../scripts/check_agents.py) | Validate YAML before register |
