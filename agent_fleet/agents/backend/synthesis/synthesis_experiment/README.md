# Synthesis Experiment Worker

This directory is the complete microservice package for the **Synthesis Experiment Worker** agent in the backend `synthesis` stage of the EDA agent fleet.

## EDA responsibility

Isolated RTL-to-netlist compile with QoR proxies; Yosys/licensed synthesizer adapter target.

Worker under synthesis_lead. Each task is one candidate; it does not rank or promote.

The agent role is `worker`, and the default HTTP port from `config.yaml` is `8234`. This agent is a specialist worker and does not declare nested delegates_to children of its own.

## How the process boots

The runtime path is intentionally linear so every agent in the fleet starts the same way.

1. Container or developer shell executes `python server.py` (see the Docker `CMD`).
2. `server.py` places this directory on `sys.path`, imports `SynthesisExperimentAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, SynthesisExperimentAgent)`.
3. Importing `agent.py` constructs `SynthesisExperimentAgent(EdaAgent)` and assigns `spec = EdaAgent.read_spec(<this directory>)`, which loads `config.yaml`.
4. `config.yaml` supplies identity, boundary may/may_not rules, connection host and port `8234`, capabilities, skills (module and callable pairs into `tools.py`), memory, telemetry, deployment, and context policy.
5. When a task arrives on `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context, journals start and finish, and either proposes child workflows or calls the matching callable in `tools.py`.
6. Each `tools.py` function returns `tool_observation(...)`. Until an EDA framework adapter is bound through `EDA_FRAMEWORK` / `backend.type`, that observation reports status `not_run` and does not invoke Yosys, OpenROAD, OpenSTA, or a licensed engine.

## Files in this directory

`server.py` is the HTTP and ASGI bootstrap. It constructs `AgentService`, exports `app` for uvicorn, and calls `server.run()` when launched as the main program.

`agent.py` defines `SynthesisExperimentAgent` as a thin `EdaAgent` subclass. Its only class body responsibility is loading the sibling `config.yaml` into `spec`.

`config.yaml` is the Agent manifest (`apiVersion: agentfleet/v1`). It is the source of truth for skills, boundaries, port `8234`, and context assembly.

`tools.py` holds the stable operation contracts for this agent's EDA work. Every skill listed in `config.yaml` maps to one callable here.

`__init__.py` re-exports `SynthesisExperimentAgent` so package-style imports expose a single public agent class.

`Dockerfile` builds a `python:3.11-slim` image, installs the fleet package editable, sets `WORKDIR` to this agent directory, exposes port `8234`, and runs `python server.py`.

`requirements.txt` pins the HTTP surface dependencies: FastAPI, uvicorn with standard extras, pydantic, and PyYAML.

`README.md` is this file. It documents boot order, every sibling file, and each tool.

## Tools

**`write_synthesis_script`.** Write the versioned Yosys/synth script (or licensed-tool script) for this hypothesis.

**`write_compile_directives`.** Write compile, boundary optimization, and effort directives that define the experiment.

**`preserve_hierarchy`.** Mark modules that must remain hierarchical for DFT, floorplan, or debug boundaries.

**`flatten_hierarchy`.** Mark modules this experiment may flatten for better cross-boundary optimization.

**`read_synthesis_libraries`.** Read liberty (.lib) libraries this compile will link for mapping and timing proxies.

**`submit_synthesis`.** Run one synthesis job for this candidate; adapter target yosys synth or bound synthesizer.

**`read_synthesis_log`.** Read the raw synthesis log for warnings, errors, and mapping messages.

**`summarize_qor`.** Return area, timing proxy, runtime, and warning counts for the lead's comparison table.

**`report_area`.** Report cell area and estimated utilization from the mapped netlist.

**`report_cell_counts`.** Report cell counts by class (combo, seq, clock, buffer) for structural insight.

**`report_timing_proxy`.** Report the synthesizer's timing estimate; this is not signoff static timing analysis.

**`report_synthesis_runtime`.** Report wall time and peak memory so expensive knobs can be weighed against QoR.

**`report_synthesis_warnings`.** List black boxes, inferred latches, and unmapped cells called out in the log.

**`diff_qor_against_baseline`.** Compare area, cell counts, and timing proxy versus the recorded baseline netlist.

**`emit_netlist`.** Write the gate-level Verilog/netlist artifact for downstream equivalence and floorplan.

**`check_blackboxes`.** List modules left as black boxes (missing RTL or intentionally empty).

**`check_inferred_latches`.** List inferred latches, often a sign of incomplete RTL assignments.

**`check_combinational_loops`.** List combinational loops in the netlist that break timing and DFT assumptions.

**`record_synthesis_tool_version`.** Record synthesizer binary, version, script hash, and library set for provenance.

## Related packages

The parent stage package lives at `agent_fleet/agents/backend/synthesis/` and groups all `synthesis` agents under one README.
