"""
In-memory heartbeat store.

Stores the last N heartbeats per agent and derives health summaries for the
gateway. Thread-safe via a single ``threading.Lock`` so the FastAPI async
routes and any sync helpers can call into the same singleton. Designed so a
future Redis-backed store can preserve ``record_heartbeat`` /
``get_health`` / ``get_all_health`` / ``check_timeouts`` without changing
routers.
"""

# wall-clock timestamps for last_seen and effective-reachable age checks.
import time
# Lock protects _agents and _host_port_to_agent_id maps.
import threading
# deque with maxlen implements the per-agent ring buffer.
from collections import deque
# dataclasses keep Heartbeat / AgentHealthState terse and typed.
from dataclasses import dataclass, field
# Typing for maps and optional busy flags.
from typing import Dict, Optional, List

# Ring size and reachability age threshold from shared config.
from .config import MAX_HEARTBEATS_PER_AGENT, HEARTBEAT_REACHABLE_THRESHOLD_SECS


@dataclass
class Heartbeat:
    """One recorded heartbeat sample stored in the per-agent ring buffer.

    ``ts`` is the sample time (producer-supplied or server ``time.time()``).
    ``reachable`` is the agent-reported flag; effective reachability also
    requires freshness against the threshold. ``busy`` is optional workload
    hint for the UI.
    """

    # Unix timestamp for this sample.
    ts: float
    # Agent-reported reachability at sample time.
    reachable: bool
    # Optional busy flag; None means "unknown / unchanged".
    busy: Optional[bool] = None


@dataclass
class AgentHealthState:
    """Mutable per-agent state: history ring plus last_* summary fields.

    ``history`` is a maxlen deque of ``Heartbeat``. ``last_seen`` / 
    ``last_reachable`` / ``last_busy`` are denormalized for O(1) summaries.
    """

    # Ring buffer; factory closes over MAX_HEARTBEATS_PER_AGENT at class define time.
    history: deque = field(default_factory=lambda: deque(maxlen=MAX_HEARTBEATS_PER_AGENT))
    # 0.0 means never seen; used by _effective_reachable.
    last_seen: float = 0.0
    # Last agent-reported reachable (also cleared by timeout scanner).
    last_reachable: bool = False
    # Last known busy, or None if never reported.
    last_busy: Optional[bool] = None


class HeartbeatStore:
    """
    Thread-safe in-memory store for agent heartbeats.

    - Stores the last N heartbeats per agent in a ring buffer.
    - Derives effective "reachable" based on last_seen vs threshold and last_reachable.
    - Tracks whether effective reachable changed (for event triggering).
    - Indexes by ``host:port`` when heartbeats include host/port so the gateway
      can match registered agents by connection endpoint.
    """

    def __init__(self, max_heartbeats: int = MAX_HEARTBEATS_PER_AGENT, threshold_secs: float = HEARTBEAT_REACHABLE_THRESHOLD_SECS):
        """Initialize empty maps and remember ring size / threshold.

        Args:
            max_heartbeats: maxlen for new agents' history deques.
            threshold_secs: max age of last_seen for effective reachable=True.
        """
        # Primary map: agent_id (often "host:port") -> state.
        self._agents: Dict[str, AgentHealthState] = {}
        # Secondary index: "host:port" -> agent_id for gateway matching.
        self._host_port_to_agent_id: Dict[str, str] = {}
        # One lock for all mutating/read methods.
        self._lock = threading.Lock()
        # Stored so new AgentHealthState deques use the instance value.
        self._max_heartbeats = max_heartbeats
        # Age threshold used by _effective_reachable.
        self._threshold_secs = threshold_secs

    def record_heartbeat(
        self,
        agent_id: str,
        reachable: bool,
        busy: Optional[bool],
        ts: Optional[float],
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> bool:
        """
        Record a heartbeat for an agent and return whether effective reachable flipped.

        Args:
            agent_id: The agent's identifier (ingest uses ``host:port`` as id).
            reachable: Whether the agent reported itself reachable.
            busy: Whether the agent is busy (optional; None leaves last_busy).
            ts: Timestamp of the heartbeat; uses current time if None.
            host: Task server host (optional); used to index by host:port.
            port: Task server port (optional); used to index by host:port.

        Returns:
            True if effective "reachable" status changed (for event triggering),
            False otherwise.
        """
        # Prefer producer timestamp; else stamp with server now.
        now = ts if ts is not None else time.time()
        # Immutable sample for the ring buffer.
        hb = Heartbeat(ts=now, reachable=reachable, busy=busy)

        # Serialize all map updates.
        with self._lock:
            # Look up existing state or create a fresh one.
            state = self._agents.get(agent_id)
            if state is None:
                # New agent: empty state with correctly sized deque.
                state = AgentHealthState()
                # Override default factory maxlen with instance setting.
                state.history = deque(maxlen=self._max_heartbeats)
                # Register in the primary map.
                self._agents[agent_id] = state

            # Snapshot effective reachable before mutation for change detection.
            prev_effective = self._effective_reachable(state)

            # Append sample (drops oldest when maxlen exceeded).
            state.history.append(hb)
            # Update denormalized last_seen for threshold checks.
            state.last_seen = now
            # Remember last reported reachable flag.
            state.last_reachable = reachable
            # Only overwrite busy when the producer sent a value.
            if busy is not None:
                state.last_busy = busy

            # Maintain host:port secondary index when both are present.
            if host is not None and port is not None:
                self._host_port_to_agent_id[f"{host}:{port}"] = agent_id

            # Recompute effective reachable after updates.
            new_effective = self._effective_reachable(state)
            # True only when the boolean flipped (gateway should be notified).
            return prev_effective != new_effective

    def get_health(self, agent_id: str) -> Optional[Dict]:
        """
        Get health summary for a single agent.

        Returns None if the agent is unknown (never heartbeated). Summary
        dict keys: agent_id, last_seen, reachable (effective), busy.
        """
        with self._lock:
            # Missing key => caller should 404.
            state = self._agents.get(agent_id)
            if state is None:
                return None
            # Build the public summary under the lock for consistency.
            return self._state_to_summary(agent_id, state)

    def get_all_health(self) -> Dict[str, Dict]:
        """
        Get health summary for all known agents.

        Returns a dict keyed by agent_id and also by ``host:port`` when that
        index was populated, so the gateway can match registered agents
        (user-chosen name + host/port) by connection endpoint as well as id.
        """
        with self._lock:
            # Primary keys: every known agent_id.
            out = {rid: self._state_to_summary(rid, st) for rid, st in self._agents.items()}
            # Duplicate summaries under host:port keys when still valid.
            for hp_key, rid in self._host_port_to_agent_id.items():
                if rid in self._agents:
                    out[hp_key] = self._state_to_summary(rid, self._agents[rid])
            return out

    def check_timeouts(self) -> List[str]:
        """
        Scan all agents and return IDs whose effective reachable just became False.

        Detects the transition from "was reporting reachable with a last_seen"
        to "threshold expired or last_reachable cleared". Mutates
        ``state.last_reachable`` to False on timeout so the next scan does not
        re-emit the same agents. Called periodically from the app lifespan
        background task.
        """
        # Accumulate ids that flipped unreachable this pass.
        timed_out: List[str] = []
        with self._lock:
            # Inspect every known agent under the lock.
            for rid, state in self._agents.items():
                # "Was reachable" means last report said so and we have a timestamp.
                was_reachable = state.last_reachable and state.last_seen != 0.0
                # Current effective may be False due to age even if last_reachable True.
                now_effective = self._effective_reachable(state)
                # Only fire when we transition from believed-up to down.
                if was_reachable and not now_effective:
                    # Clear so we do not re-notify every scanner tick.
                    state.last_reachable = False
                    timed_out.append(rid)
        return timed_out

    def _effective_reachable(self, state: AgentHealthState) -> bool:
        """Derive effective reachable from last_seen age and last_reachable flag.

        Never-seen agents (last_seen == 0) are unreachable. Otherwise require
        both a fresh timestamp within ``_threshold_secs`` and a True
        last_reachable bit.
        """
        # Zero timestamp means no heartbeat has been recorded yet.
        if state.last_seen == 0.0:
            return False
        # Age check AND last reported flag must both hold.
        return (time.time() - state.last_seen) <= self._threshold_secs and state.last_reachable

    def _state_to_summary(self, agent_id: str, state: AgentHealthState) -> Dict:
        """Build the public health dict for API responses from internal state."""
        return {
            # Echo the lookup key (agent_id or host:port alias).
            "agent_id": agent_id,
            # Raw last heartbeat time for UI freshness displays.
            "last_seen": state.last_seen,
            # Derived reachable (threshold + flag), not just last report.
            "reachable": self._effective_reachable(state),
            # May be None if busy was never reported.
            "busy": state.last_busy,
        }


# Module-level singleton instance; None until get_heartbeat_store().
_store: Optional[HeartbeatStore] = None


def get_heartbeat_store() -> HeartbeatStore:
    """Get or create the singleton HeartbeatStore instance.

    All routers and the timeout scanner share one store so health reads see
    the same heartbeats ingest wrote. Tests may reset ``_store`` to None
    between cases for isolation.
    """
    global _store
    # Lazy construct with config defaults.
    if _store is None:
        _store = HeartbeatStore()
    return _store
