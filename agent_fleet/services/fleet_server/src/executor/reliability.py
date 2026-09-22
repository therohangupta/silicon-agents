"""
Reliability helpers for Fleet Server task dispatch retries.

The Executor consults an agent's ``ReliabilityConfig`` (from agent health, or
defaults) when deciding whether a failed dispatch should be retried, how long
to wait between attempts, and how to classify the failure for policy matching.

Functions:
  * ``classify_failure`` — map an exception and/or ``AgentTaskResult`` to a
    failure-type string (``timeout``, ``transient_error``, ``validation_error``,
    ``success``).
  * ``is_retryable`` — consult ``policy.no_retry_on`` / ``policy.retry_on``
    (default: everything except ``validation_error`` is retryable).
  * ``backoff_delay`` — sleep using fixed or exponential backoff from
    ``policy.retry_backoff``.

These helpers are pure policy utilities; they do not talk to agents or the DB.
"""

# Postpone annotation evaluation for modern typing convenience.
from __future__ import annotations

# asyncio.TimeoutError detection and asyncio.sleep for backoff.
import asyncio
# logging retained for potential future diagnostics in helpers.
import logging
# Optional typing for exc/result parameters.
from typing import Any, Optional

# Agent result + reliability policy models from the agent SDK.
from packages.agent_sdk.src.models import AgentTaskResult, ReliabilityConfig

# Module logger (helpers currently return values without logging).
logger = logging.getLogger(__name__)


def classify_failure(exc: Optional[Exception], result: Optional[AgentTaskResult]) -> str:
    """
    Classify a dispatch outcome into a failure-type string for retry policy.

    Precedence:
      1. If ``exc`` is set → ``timeout`` for TimeoutError, else ``transient_error``.
      2. If ``result`` is None → ``transient_error``.
      3. If result.error mentions validation → ``validation_error``.
      4. If unsuccessful (with or without replan) → ``transient_error``.
      5. Otherwise → ``success``.

    Args:
        exc: Exception raised during dispatch, if any.
        result: AgentTaskResult returned by the agent, if any.

    Returns:
        One of ``timeout``, ``transient_error``, ``validation_error``, ``success``.
    """
    # Exception path takes priority over result inspection.
    if exc is not None:
        # Timeouts are called out so policies can treat them specially.
        if isinstance(exc, asyncio.TimeoutError):
            return "timeout"
        # All other exceptions are treated as transient by default.
        return "transient_error"
    # Missing result after a "successful" await is still treated as transient.
    if result is None:
        return "transient_error"
    # Validation-like errors are typically non-retryable.
    if result.error and "validation" in (result.error or "").lower():
        return "validation_error"
    # Unsuccessful results that request replan still classify as transient here;
    # the Executor decides whether to invoke Replanner separately.
    if not result.success and result.replan:
        return "transient_error"
    # Generic unsuccessful result.
    if not result.success:
        return "transient_error"
    # Happy path.
    return "success"


def is_retryable(failure_type: str, policy: ReliabilityConfig) -> bool:
    """
    Decide whether ``failure_type`` should trigger another dispatch attempt.

    Args:
        failure_type: String from ``classify_failure``.
        policy: Agent reliability configuration with retry allow/deny lists.

    Returns:
        True if another attempt should be made; False to stop retrying.
    """
    # Explicit denylist wins first.
    if failure_type in policy.no_retry_on:
        return False
    # If an allowlist is configured, require membership.
    if policy.retry_on:
        return failure_type in policy.retry_on
    # Default: retry everything except validation errors.
    return failure_type != "validation_error"


async def backoff_delay(attempt: int, policy: ReliabilityConfig) -> None:
    """
    Sleep for the configured backoff delay before the next retry attempt.

    Args:
        attempt: Zero-based retry attempt index (0 after first failure).
        policy: Reliability config containing ``retry_backoff`` settings.
    """
    # Convenience alias for the nested backoff config object.
    cfg = policy.retry_backoff
    if cfg.strategy == "fixed":
        # Fixed strategy: always wait base_secs.
        delay = cfg.base_secs
    else:
        # Exponential strategy: base * 2^attempt, capped at max_secs.
        delay = min(cfg.base_secs * (2 ** attempt), cfg.max_secs)
    # Actually sleep; caller awaits this between retries.
    await asyncio.sleep(delay)
