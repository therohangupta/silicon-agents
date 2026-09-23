"""
Plan Executor: dependency-aware parallel task dispatch for the Fleet Server.

``Executor`` is started by ``FleetManagerService.StartPlan`` as a background
asyncio Task after verifying the plan is fully allocated (every task has an
``agent_id``). It:

  1. Optionally enables durable NATS JetStream dispatch when
     ``DURABLE_TASK_DISPATCH=true`` (falls back to direct HTTP on connect failure).
  2. Marks the plan ``execution_status=executing`` and emits Gateway events.
  3. Builds an ``AllocatedDAGPlan`` from registry tasks.
  4. Topologically sorts the DAG (Kahn) and partitions into per-agent queues.
  5. Schedules ready tasks (deps complete + agent idle) in a 1s polling loop.
  6. On success: marks task completed, pops the agent queue, records execution facts.
  7. On failure: applies reliability ``on_failure`` (replan / skip / dead_letter /
     abort), optionally invoking ``Replanner``.
  8. On abort: fails remaining tasks and marks the plan failed; else completed.

Execution context for agents comes from ``ExecutionContext.snapshot()`` plus an
in-memory artifact manifest accumulated from prior ``artifact_refs``.
"""

# HTTP client for direct (non-durable) agent task execution.
from packages.agent_sdk.src.client.agent_client import AgentClient
# Request/result/context/reliability models for agent dispatch.
from packages.agent_sdk.src.config import ReliabilityConfig
from packages.agent_sdk.src.contracts import (
    AgentTaskRequest,
    ArtifactRef,
    ExecutionContextSnapshot,
    TaskSummary,
)
# Allocated DAG schemas built from registry tasks.
from ..formats.formats import AllocatedDAGNode, AllocatedDAGPlan
# Registry for plan/task/agent/execution persistence.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# Config: DB URL, agent host rewrite, workspace URI pieces.
from packages.config import DATABASE_URL, DEFAULT_AGENT_HOST, WORKSPACE_STORAGE_BACKEND, WORKSPACE_STORAGE_ROOT, WORKSPACE_S3_BUCKET
# Metrics wrapper for plan/task execution spans.
from packages.metrics import track_operation
# asyncio for locks, create_task, sleep, gather, wait_for.
import asyncio
# json.dumps for persisting structured results onto task rows.
import json
# logging throughout the scheduling loop.
import logging
# os.environ for DURABLE_TASK_DISPATCH flag.
import os
# Optional/Set typing for optional bus and terminal id sets.
from typing import Optional, Set
# ArgumentParser for the standalone __main__ harness.
from argparse import ArgumentParser
# SDK-owned replanner used when failure policy requests recovery planning.
from packages.fleet_sdk.src.planners.types.replanner.planner import Replanner
# Gateway events for task/plan status invalidation.
from packages.fleet_sdk.src.events import emit_plan_changed, emit_task_changed
# ORM PlanModel for reading existing server_logs.
from packages.fleet_sdk.src.models import PlanModel
# select() for loading prior plan logs.
from sqlalchemy import select
# Execution context snapshot builder for AgentTaskRequest.context.
from packages.fleet_sdk.src.execution_context import ExecutionContext
# Retry classification / backoff helpers.
from .reliability import backoff_delay, classify_failure, is_retryable
# Durable NATS delivery bus + deferred-ack container.
from .task_delivery import DeliveredTaskResult, TaskDeliveryBus

# Module logger.
logger = logging.getLogger(__name__)


class Executor:
    """
    Executes a fully allocated plan with dependency-aware parallelism.

    Maintains per-agent idle flags and task queues, a completed-task set, and
    abort/replan flags guarded by ``self.mutex`` where scheduling decisions
    race with task completion callbacks.
    """

    def __init__(self, plan_id: int, db_url: Optional[str] = None, registry: Optional[AgentInstanceRegistry] = None):
        """
        Bind registry/plan and initialize scheduling/reliability state.

        Args:
            plan_id: Plan to execute (must be fully allocated before start).
            db_url: Used only when ``registry`` is omitted.
            registry: Preferred shared registry from FleetManagerService.
        """
        # Shared or newly constructed registry for all DB operations.
        self.registry = registry or AgentInstanceRegistry(db_url or DATABASE_URL)
        # Mutex protects shared scheduling state across concurrent task tasks.
        self.mutex = asyncio.Lock()
        # agent_id → True when the agent can accept a new task.
        self.agent_to_idle_bool = {}
        # Set of task ids that have reached a terminal success/skip state.
        self.complete_task_ids = set()
        # When True, the main loop stops scheduling and fails the plan.
        self.abort = False
        # agent_id → ordered list of remaining task ids (topo-partitioned).
        self.agent_task_map = {}
        # Current plan id (may change after successful replan).
        self.plan_id = plan_id
        # When True, the loop rebuilds DAG/queues from the new plan_id.
        self.replan = False
        # Fallback execution-fact strings when ExecutionContext has no rows yet.
        self.previous_task_status_messages = []
        # Accumulated execution log lines persisted onto the plan row.
        self.execution_logs: list[str] = []
        # Task ids that reached a durable terminal outcome (idempotency).
        self._terminal_task_ids: Set[str] = set()
        # Feature flag for NATS durable dispatch path.
        self._use_durable_dispatch = os.environ.get("DURABLE_TASK_DISPATCH", "false").lower() == "true"
        # JetStream bus instance when durable mode is active.
        self._delivery_bus: Optional[TaskDeliveryBus] = None
        # Deferred ack handle for the in-flight durable delivery.
        self._pending_delivery_ack: Optional[DeliveredTaskResult] = None
        # Accumulated ArtifactRef list passed into subsequent task contexts.
        self._artifact_manifest: list[ArtifactRef] = []
        # Workspace URI embedded in every AgentTaskRequest for this plan.
        self._workspace_uri: str = self._build_workspace_uri()

    def _build_workspace_uri(self) -> str:
        """
        Construct the workspace URI agents should use for plan artifacts.

        Returns:
            ``s3://...`` URI when S3 backend is configured; otherwise a
            ``workspace://{plan_id}?root=...`` URI for local storage.
        """
        if WORKSPACE_STORAGE_BACKEND == "s3" and WORKSPACE_S3_BUCKET:
            # S3-backed shared workspace path scoped by plan id.
            return f"s3://{WORKSPACE_S3_BUCKET}/workspaces/{self.plan_id}"
        # Local/dev workspace scheme with configured root query param.
        return f"workspace://{self.plan_id}?root={WORKSPACE_STORAGE_ROOT}"

    async def _load_existing_plan_logs(self):
        """
        Load existing plan logs so execution events append instead of overwriting.

        Reads ``PlanModel.server_logs`` for ``self.plan_id`` and splits into
        non-empty lines stored on ``self.execution_logs``.
        """
        try:
            async with self.registry.async_session_factory() as session:
                # Select only the server_logs column for this plan.
                result = await session.execute(
                    select(PlanModel.server_logs).where(PlanModel.plan_id == self.plan_id)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    # Split persisted multi-line logs into a list of lines.
                    self.execution_logs = [line for line in str(existing).split("\n") if line.strip()]
                else:
                    # No prior logs — start empty.
                    self.execution_logs = []
        except Exception as e:
            # Soft-fail: continue execution with empty logs.
            logger.error("Failed to load existing logs for plan %s: %s", self.plan_id, e)
            self.execution_logs = []

    async def _append_execution_log(self, message: str):
        """
        Append and persist execution log lines on the plan record.

        Args:
            message: Single log line to append and flush to the DB.
        """
        # Keep an in-memory copy for subsequent appends.
        self.execution_logs.append(message)
        try:
            # Persist the full list so dashboards see live progress.
            await self.registry.update_plan(self.plan_id, server_logs=self.execution_logs)
        except Exception as e:
            # Logging persistence must not abort the plan.
            logger.error("Failed to persist execution logs for plan %s: %s", self.plan_id, e)

    async def _generate_dag(self) -> AllocatedDAGPlan:
        """
        Build an ``AllocatedDAGPlan`` from the plan's ordered task ids.

        Returns:
            AllocatedDAGPlan whose nodes carry task_id, agent_id, and deps.
        """
        # Load the plan to obtain the ordered task_ids list.
        plan = await self.registry.get_plan(self.plan_id)
        # Start with an empty node list and fill from registry tasks.
        dag = AllocatedDAGPlan(nodes=[])
        for task_id in plan.task_ids:
            # Fetch each task proto for description/agent/deps.
            task = await self.registry.get_task(task_id)
            node = AllocatedDAGNode(
                task_id=task_id,
                description=task.description,
                goal_id=task.goal_id,
                agent_id=task.agent_id,
                depends_on=[dep_id for dep_id in task.dependency_task_ids]
            )
            dag.nodes.append(node)
        return dag

    async def _get_agent_task_map(self, dag: AllocatedDAGPlan) -> dict:
        """
        For each agent, return task IDs in topological (dependency) order.

        Runs Kahn's algorithm on the full DAG, then partitions by agent while
        preserving that global ordering so each agent's queue respects deps.

        Args:
            dag: Allocated DAG with agent assignments on each node.

        Returns:
            Dict mapping agent_id → list of task ids in topo order.
        """
        # Adjacency inputs: task → dependency list.
        dep_map = {node.task_id: list(node.depends_on) for node in dag.nodes}
        all_ids = set(dep_map.keys())

        # Kahn structures: in-degree and children adjacency.
        in_degree: dict[int, int] = {tid: 0 for tid in all_ids}
        children: dict[int, list[int]] = {tid: [] for tid in all_ids}
        for tid, deps in dep_map.items():
            for d in deps:
                if d in all_ids:
                    # Edge d → tid increases tid's in-degree.
                    in_degree[tid] += 1
                    children[d].append(tid)

        # Seeds: nodes with no unmet dependencies (sorted for determinism).
        queue = sorted(tid for tid, deg in in_degree.items() if deg == 0)
        topo_order: list[int] = []
        while queue:
            # Pop the next ready node (FIFO within sorted resets).
            tid = queue.pop(0)
            topo_order.append(tid)
            for child in children[tid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
            # Re-sort after each expansion for stable scheduling.
            queue.sort()

        # Map each task to its assigned agent for partitioning.
        task_to_agent = {node.task_id: node.agent_id for node in dag.nodes}
        agent_task_map: dict[str, list[int]] = {}
        for tid in topo_order:
            rid = task_to_agent[tid]
            if rid not in agent_task_map:
                agent_task_map[rid] = []
            # Append in global topo order so agent queues stay consistent.
            agent_task_map[rid].append(tid)

        for agent_id, tasks in agent_task_map.items():
            logger.debug("Agent %s tasks (topo order): %s", agent_id, tasks)

        return agent_task_map

    async def _start_task(self, agent_id: int, task_id: int, task_description: str):
        """
        Wrap ``_start_task_inner`` with metrics tracking for one task.

        Args:
            agent_id: Agent instance id (typed historically as int; may be str).
            task_id: Database task id to execute.
            task_description: Human description passed to the agent.
        """
        async with track_operation(self.registry, "fleet_server", "task_execution", str(task_id)) as meta:
            # Attach correlating metadata for metrics backends.
            meta["agent_id"] = str(agent_id)
            meta["plan_id"] = self.plan_id
            # Perform the actual dispatch + status updates.
            await self._start_task_inner(agent_id, task_id, task_description)

    async def _load_reliability_policy(self, agent_client: AgentClient) -> ReliabilityConfig:
        """
        Load reliability policy from agent health, or return defaults.

        Args:
            agent_client: Connected client used to call ``health()``.

        Returns:
            Agent-provided ``ReliabilityConfig`` or a default instance.
        """
        try:
            health = await agent_client.health()
            if health.reliability:
                return health.reliability
        except Exception:
            # Soft-fail: proceed with defaults when health is unavailable.
            logger.debug("Could not load reliability from agent health", exc_info=True)
        return ReliabilityConfig()

    async def _reconcile_dispatched_rows(self) -> None:
        """
        Re-enqueue dispatched task rows that have no later terminal result.

        Used after connecting the durable bus so crash recovery can resume
        in-flight dispatches that never received a terminal execution row.
        """
        if not self._delivery_bus:
            return
        try:
            rows = await self.registry.list_task_executions(self.plan_id)
        except Exception:
            logger.debug("Could not load task executions for reconciliation", exc_info=True)
            return

        # Task ids that already have a non-dispatched (terminal-ish) result.
        terminal_task_ids = {
            str(row["task_id"])
            for row in rows
            if isinstance(row.get("result"), dict)
            and row["result"].get("dispatch_state") != "dispatched"
        }
        for row in rows:
            result = row.get("result") or {}
            task_id = str(row["task_id"])
            if not isinstance(result, dict):
                continue
            # Skip rows that are not stuck in dispatched, or already terminal.
            if result.get("dispatch_state") != "dispatched" or task_id in terminal_task_ids:
                continue
            try:
                # Reload task + agent to rebuild host/port/request.
                task = await self.registry.get_task(int(task_id))
                agent = await self.registry.get_agent(str(row["agent_id"]))
                if task is None or agent is None:
                    continue
                host = agent.task_server_info.host
                # Rewrite localhost when running in docker/compose networks.
                if DEFAULT_AGENT_HOST != "localhost" and host in ("localhost", "127.0.0.1"):
                    host = DEFAULT_AGENT_HOST
                request_data = (row.get("context_snapshot") or {}).get("request")
                request = (
                    AgentTaskRequest(**request_data)
                    if isinstance(request_data, dict)
                    else AgentTaskRequest(
                        task_id=task_id,
                        description=task.description,
                        plan_id=self.plan_id,
                    )
                )
                # Re-publish so a consumer can pick up the stuck dispatch.
                await self._delivery_bus.publish_dispatch(
                    str(row["agent_id"]),
                    host,
                    agent.task_server_info.port,
                    request,
                    self.plan_id,
                    int(task_id),
                )
                logger.info("Re-enqueued dispatched task %s", task_id)
            except Exception:
                logger.debug("Failed to re-enqueue dispatched task %s", task_id, exc_info=True)

    async def _dispatch_task(
        self,
        agent_client: AgentClient,
        request: AgentTaskRequest,
        policy: ReliabilityConfig,
        agent_id_str: str,
        host: str,
        port: int,
    ):
        """
        Dispatch a task with retries, optional durable delivery, and policies.

        Prefer durable JetStream on the first attempt when enabled; otherwise
        call ``agent_client.execute_task`` directly. Retries honor
        ``classify_failure`` / ``is_retryable`` / ``backoff_delay``.

        Args:
            agent_client: Direct HTTP client (also used on retry fallback).
            request: Fully built AgentTaskRequest including context.
            policy: Reliability config (timeouts, retries, on_failure).
            agent_id_str: Agent id string for durable subject naming.
            host: Agent host for durable payload.
            port: Agent port for durable payload.

        Returns:
            Final ``AgentTaskResult`` (success or non-retryable failure).

        Raises:
            Exception: When retries are exhausted with only exceptions, or a
                non-retryable exception occurs.
        """
        from packages.agent_sdk.src.contracts import AgentTaskResult

        # Idempotency: skip if this task already reached a terminal state.
        task_key = str(request.task_id)
        if task_key in self._terminal_task_ids:
            return AgentTaskResult(success=True, message="idempotent skip: already completed")

        # Completed ids for durable idempotent skip inside the bus.
        completed_ids = {str(tid) for tid in self.complete_task_ids} | self._terminal_task_ids
        attempt = 0
        last_exc: Optional[Exception] = None
        last_result: Optional[AgentTaskResult] = None
        used_durable = False

        # Retry loop inclusive of the initial attempt (attempt 0).
        while attempt <= policy.max_retries:
            try:
                if (
                    attempt == 0
                    and self._use_durable_dispatch
                    and self._delivery_bus
                    and self._pending_delivery_ack is None
                ):
                    # First attempt via durable bus when enabled and idle.
                    used_durable = True
                    delivered = await asyncio.wait_for(
                        self._delivery_bus.dispatch_and_deliver(
                            agent_id_str,
                            host,
                            port,
                            request,
                            self.plan_id,
                            int(request.task_id),
                            completed_ids,
                            receive_timeout_secs=policy.task_timeout_secs,
                        ),
                        timeout=policy.task_timeout_secs + 10,
                    )
                    # Stash for later ack once the Executor finalizes.
                    self._pending_delivery_ack = delivered
                    last_result = delivered.result
                else:
                    # Direct HTTP path (retries or durable disabled).
                    last_result = await asyncio.wait_for(
                        agent_client.execute_task(request),
                        timeout=policy.task_timeout_secs,
                    )
                # Clear exception state after a successful await.
                last_exc = None
                failure_type = classify_failure(None, last_result)
                # Return immediately on success or non-retryable failure result.
                if last_result.success or not is_retryable(failure_type, policy):
                    return last_result
            except Exception as exc:
                # Capture exception for potential re-raise after retries.
                last_exc = exc
                last_result = None
                failure_type = classify_failure(exc, None)
                if not is_retryable(failure_type, policy):
                    # Ack durable message before propagating non-retryable errors.
                    if used_durable and self._delivery_bus:
                        await self._delivery_bus.ack(self._pending_delivery_ack)
                        self._pending_delivery_ack = None
                    raise

            # Increment attempt and optionally sleep before retrying.
            attempt += 1
            if attempt <= policy.max_retries:
                await backoff_delay(attempt - 1, policy)

        # Exhausted retries: prefer returning last_result if we got one.
        if last_result is not None:
            return last_result
        # Durable path with only exceptions: ack then raise.
        if used_durable and self._delivery_bus:
            await self._delivery_bus.ack(self._pending_delivery_ack)
            self._pending_delivery_ack = None
        raise last_exc or RuntimeError("task dispatch failed")

    async def _finalize_delivery_ack(self, task_id: int, terminal: bool) -> None:
        """
        Optionally mark terminal and ack any pending durable delivery.

        Args:
            task_id: Task id that finished dispatch handling.
            terminal: If True, add task_id to ``_terminal_task_ids``.
        """
        if terminal:
            self._terminal_task_ids.add(str(task_id))
        if self._delivery_bus and self._pending_delivery_ack:
            await self._delivery_bus.ack(self._pending_delivery_ack)
            self._pending_delivery_ack = None

    async def _handle_task_failure(
        self,
        agent_id,
        task_id: int,
        result,
        policy: ReliabilityConfig,
    ) -> None:
        """
        Apply reliability ``on_failure`` policy after an unsuccessful result.

        Policies:
          - replan (or result.replan): mark failed, run Replanner, set replan flag.
          - skip: mark failed, treat as complete so dependents can proceed.
          - dead_letter: record dead_letter execution row, then skip-like complete.
          - default: mark failed and set abort to cascade-cancel the plan.

        Args:
            agent_id: Agent that ran the failing task.
            task_id: Failed task id.
            result: AgentTaskResult with message / replan flag.
            policy: ReliabilityConfig controlling on_failure behavior.
        """
        if result.replan or policy.on_failure == "replan":
            # Status 5 = TASK_FAILED in the fleet proto enum.
            await self.registry.update_task_status(task_id, 5)
            emit_task_changed(task_id, plan_id=self.plan_id, status="failed")
            await self._append_execution_log(
                f"Task {task_id} failed and triggered replanning: {result.message}"
            )
            # Build a recovery plan and switch self.plan_id to the new one.
            replanner = Replanner(registry=self.registry)
            self.plan_id = await replanner.replan(
                plan_id=self.plan_id,
                failed_task_id=task_id,
                failure_message=result.message,
                agent_task_assignments={
                    aid: self.agent_task_map[aid] for aid in self.agent_task_map.keys()
                },
            )
            # Signal the main loop to rebuild queues from the new plan.
            self.replan = True
            await self._finalize_delivery_ack(task_id, terminal=True)
            return

        if policy.on_failure == "skip":
            # Fail the task but allow the plan to continue past it.
            await self.registry.update_task_status(task_id, 5)
            emit_task_changed(task_id, plan_id=self.plan_id, status="failed")
            await self._finalize_delivery_ack(task_id, terminal=True)
            self.complete_task_ids.add(task_id)
            self.agent_to_idle_bool[agent_id] = True
            if self.agent_task_map.get(agent_id):
                self.agent_task_map[agent_id].pop(0)
            return

        if policy.on_failure == "dead_letter":
            # Persist a dead_letter execution marker for later inspection.
            await self.registry.update_task_status(task_id, 5)
            emit_task_changed(task_id, plan_id=self.plan_id, status="failed")
            await self.registry.record_task_execution(
                task_id=task_id,
                plan_id=self.plan_id,
                agent_id=str(agent_id),
                result={
                    "dispatch_state": "dead_letter",
                    "success": False,
                    "message": result.message,
                },
                context_snapshot={"dispatch_state": "dead_letter"},
            )
            await self._append_execution_log(f"Task {task_id} sent to dead letter: {result.message}")
            await self._finalize_delivery_ack(task_id, terminal=True)
            # Treat like skip for scheduling purposes.
            self.complete_task_ids.add(task_id)
            self.agent_to_idle_bool[agent_id] = True
            if self.agent_task_map.get(agent_id):
                self.agent_task_map[agent_id].pop(0)
            return

        # Default: abort the entire plan after this failure.
        await self.registry.update_task_status(task_id, 5)
        emit_task_changed(task_id, plan_id=self.plan_id, status="failed")
        await self._finalize_delivery_ack(task_id, terminal=True)
        self.abort = True
        await self._append_execution_log(f"Task {task_id} failed (abort): {result.message}")

    async def _start_task_inner(self, agent_id: int, task_id: int, task_description: str):
        """
        Execute one task end-to-end: status, context, dispatch, persistence.

        Args:
            agent_id: Assigned agent id.
            task_id: Task primary key.
            task_description: Description string for the agent request.
        """
        try:
            logger.info("Starting task %s for agent %s", task_description, agent_id)
            await self._append_execution_log(f"Task {task_id} started on agent {agent_id}")

            # TASK_IN_PROGRESS = 2
            await self.registry.update_task_status(task_id, 2)
            emit_task_changed(task_id, plan_id=self.plan_id, status="in_progress")

            # Resolve agent host/port for the task server.
            agent = await self.registry.get_agent(str(agent_id))
            host = agent.task_server_info.host
            if DEFAULT_AGENT_HOST != "localhost" and host in ("localhost", "127.0.0.1"):
                host = DEFAULT_AGENT_HOST
            port = agent.task_server_info.port
            agent_client = AgentClient(host, port)
            policy = await self._load_reliability_policy(agent_client)

            # Build execution context from prior task executions.
            context_snapshot = await ExecutionContext(self.registry, self.plan_id).snapshot()
            if not context_snapshot.completed_tasks and self.previous_task_status_messages:
                # Fallback when durable executions are empty but in-memory facts exist.
                context_snapshot = ExecutionContextSnapshot(
                    plan_summary=f"Executing plan {self.plan_id}",
                    completed_tasks=[
                        TaskSummary(
                            task_id=i + 1,
                            description="previous task",
                            result_summary=message,
                        )
                        for i, message in enumerate(self.previous_task_status_messages)
                    ],
                    execution_facts=list(self.previous_task_status_messages),
                )
            # Attach accumulated artifacts for downstream agents.
            context_snapshot.available_artifacts = list(self._artifact_manifest)
            request = AgentTaskRequest(
                task_id=str(task_id),
                description=task_description,
                plan_id=self.plan_id,
                workspace_uri=self._workspace_uri,
                context=context_snapshot,
            )

            # Record a dispatched row before the call (crash recovery marker).
            await self.registry.record_task_execution(
                task_id=task_id,
                plan_id=self.plan_id,
                agent_id=str(agent_id),
                result={"dispatch_state": "dispatched"},
                context_snapshot={
                    "dispatch_state": "dispatched",
                    "request": request.model_dump(mode="json"),
                    **(request.context.model_dump(mode="json") if request.context else {}),
                },
            )

            # Dispatch with retries / durable bus as configured.
            result = await self._dispatch_task(
                agent_client, request, policy, str(agent_id), host, port
            )
            await agent_client.close()
            logger.info("Task %s for agent %s completed with result: %s", task_description, agent_id, result)
            await self._append_execution_log(f"Task {task_id} completed on agent {agent_id}: {result.message}")

            # Accumulate artifact refs for subsequent tasks' contexts.
            if result.artifact_refs:
                self._artifact_manifest.extend(result.artifact_refs)

            # Persist the terminal structured result.
            structured_result = result.model_dump(mode="json")
            await self.registry.record_task_execution(
                task_id=task_id,
                plan_id=self.plan_id,
                agent_id=str(agent_id),
                result=structured_result,
                context_snapshot={
                    "dispatch_state": "completed" if result.success else "failed",
                    **(request.context.model_dump(mode="json") if request.context else {}),
                },
            )
            await self._finalize_delivery_ack(
                task_id,
                terminal=result.success or not result.replan,
            )
            # Also store a JSON string on the task row for API consumers.
            result_message = json.dumps(structured_result)
            await self.registry.update_task(task_id, result=result_message)

            # Update shared scheduling state under the mutex.
            async with self.mutex:
                if result.success and not result.replan:
                    # TASK_COMPLETED = 3
                    await self.registry.update_task_status(task_id, 3)
                    emit_task_changed(task_id, plan_id=self.plan_id, status="completed")

                    self.complete_task_ids.add(task_id)
                    self.agent_to_idle_bool[agent_id] = True
                    self.agent_task_map[agent_id].pop(0)
                    # Strip a legacy success prefix when building execution facts.
                    self.previous_task_status_messages.append(result.message.replace("Succeeded task!", ""))
                    return
                elif result.replan or not result.success:
                    await self._handle_task_failure(agent_id, task_id, result, policy)
                    return
        except Exception as e:
            # Crash path: mark failed and abort the plan.
            logger.error("Exception in _start_task for agent %s, task %s: %s", agent_id, task_id, e, exc_info=True)
            await self._append_execution_log(f"Task {task_id} crashed on agent {agent_id}: {str(e)}")
            await self._finalize_delivery_ack(task_id, terminal=True)
            try:
                await self.registry.update_task_status(task_id, 5)  # TASK_FAILED = 5
                await self.registry.update_task(task_id, result=f"Exception: {str(e)}")
                emit_task_changed(task_id, plan_id=self.plan_id, status="failed")
            except Exception as update_error:
                logger.error("Failed to update task status on exception: %s", update_error)
            async with self.mutex:
                self.abort = True
        finally:
            # Ensure we never leave a stale pending ack across tasks.
            self._pending_delivery_ack = None

    # main function that starts the full execution from DAG generation to sending tasks in a queue
    async def execute(self):
        """
        Public entry: wrap ``_execute_inner`` with a plan_execution metric span.
        """
        async with track_operation(self.registry, "fleet_server", "plan_execution", str(self.plan_id)):
            await self._execute_inner()

    async def _execute_inner(self):
        """
        Core scheduling loop: build DAG, dispatch ready tasks, handle terminal states.

        Polls every 1 second. Stops when all tasks complete or abort is set.
        On abort, waits for in-flight tasks then fails remaining pending ones.
        """
        # Optionally enable durable dispatch; soft-disable on NATS failure.
        if self._use_durable_dispatch:
            self._delivery_bus = TaskDeliveryBus()
            try:
                await self._delivery_bus.connect()
                await self._reconcile_dispatched_rows()
            except Exception:
                logger.warning("Durable dispatch disabled: NATS unavailable", exc_info=True)
                self._delivery_bus = None
                self._use_durable_dispatch = False

        # Preserve prior logs, mark plan executing, emit event.
        await self._load_existing_plan_logs()
        await self.registry.update_plan(self.plan_id, execution_status=1)  # 1 = executing
        emit_plan_changed(self.plan_id, status="executing")
        await self._append_execution_log(f"Plan {self.plan_id} execution started")

        # Build DAG + per-agent topo queues and idle flags.
        dag = await self._generate_dag()
        task_to_dependency_map = {node.task_id: node.depends_on for node in dag.nodes}
        self.agent_task_map = await self._get_agent_task_map(dag)
        self.agent_to_idle_bool = {agent_id: True for agent_id in self.agent_task_map}
        self.complete_task_ids = set()
        total_tasks = sum(len(tasks) for tasks in self.agent_task_map.values())
        tasks_in_progress: list[asyncio.Task] = []

        # Main loop until all tasks complete or abort.
        while len(self.complete_task_ids) < total_tasks:
            if self.abort:
                break

            async with self.mutex:
                for agent_id, tasks in self.agent_task_map.items():
                    if not tasks:
                        continue
                    # Peek at the agent's next task without popping yet.
                    next_task_id = tasks[0]

                    # Only start when all dependency task ids are complete.
                    dependencies_met = all(d in self.complete_task_ids for d in task_to_dependency_map.get(next_task_id, []))

                    start_task = await self.registry.get_task(next_task_id)
                    if start_task is None:
                        continue
                    if self.agent_to_idle_bool[agent_id] and dependencies_met:
                        # Spawn concurrent execution; mark agent busy.
                        t = asyncio.create_task(self._start_task(agent_id, next_task_id, start_task.description))
                        t.agent_id = agent_id
                        t.task_id = next_task_id
                        tasks_in_progress.append(t)
                        self.agent_to_idle_bool[agent_id] = False

            # Drop finished asyncio Tasks from the in-progress list.
            tasks_in_progress = [t for t in tasks_in_progress if not t.done()]
            # Polling interval for the scheduling loop.
            await asyncio.sleep(1)

            async with self.mutex:
                if self.replan:
                    # Rebuild everything against the new plan_id from Replanner.
                    dag = await self._generate_dag()
                    task_to_dependency_map = {node.task_id: node.depends_on for node in dag.nodes}
                    self.agent_task_map = await self._get_agent_task_map(dag)
                    self.agent_to_idle_bool = {agent_id: True for agent_id in self.agent_task_map}
                    self.complete_task_ids = set()
                    self.abort = False
                    total_tasks = sum(len(tasks) for tasks in self.agent_task_map.values())
                    self.replan = False

        if self.abort:
            # Wait for any in-flight tasks to finish before marking remaining as failed
            if tasks_in_progress:
                logger.info("Waiting for %d in-flight tasks to finish before cleanup", len(tasks_in_progress))
                await asyncio.gather(*tasks_in_progress, return_exceptions=True)

            # Mark all remaining pending tasks as failed
            for agent_id, remaining in self.agent_task_map.items():
                for tid in remaining:
                    try:
                        t = await self.registry.get_task(tid)
                        if t and t.status not in (3, 5):  # not completed or failed
                            await self.registry.update_task_status(tid, 5)
                            await self.registry.update_task(tid, result="Cancelled: plan aborted due to task failure")
                            emit_task_changed(tid, plan_id=self.plan_id, status="failed")
                    except Exception:
                        pass

            await self.registry.update_plan(self.plan_id, execution_status=3)  # 3 = failed
            emit_plan_changed(self.plan_id, status="failed")
            logger.info("Plan aborted — marked as failed")
            await self._append_execution_log(f"Plan {self.plan_id} execution failed")
        else:
            await self.registry.update_plan(self.plan_id, execution_status=2)  # 2 = completed
            emit_plan_changed(self.plan_id, status="completed")
            logger.info("Plan completed successfully")
            await self._append_execution_log(f"Plan {self.plan_id} execution completed successfully")

        # Always close the durable bus if it was opened.
        if self._delivery_bus:
            await self._delivery_bus.close()


async def main():
    """
    Standalone CLI harness: ``python -m ...executor <plan_id>``.

    Constructs an Executor with DATABASE_URL and runs ``execute()``.
    """
    executor = Executor(db_url=DATABASE_URL)
    parser = ArgumentParser()
    parser.add_argument("plan_id", type=int)
    args = parser.parse_args()
    executor.plan_id = int(args.plan_id)
    await executor.execute()

if __name__ == "__main__":
    # Drive the standalone harness when executed as a script.
    asyncio.run(main())
