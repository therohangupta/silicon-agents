"""Artifact reference schema: pointers to versioned files outside the envelope.

Engineering memory stores metadata and JSON payloads. Large binaries (logs,
GDS snippets, reports, waveforms) live in artifact storage (object store or
equivalent). ``ArtifactRef`` is the versioned pointer agents attach as
evidence on findings, experiments, and task results.

``to_fleet_ref`` converts into the generic SDK ``ArtifactRef`` so fleet
``AgentTaskResult.artifact_refs`` can carry the same URIs without depending
on EDA-specific fields the executor does not understand.
"""

from __future__ import annotations

# Literal type for the fixed schema_name discriminator.
from typing import Literal

# Pydantic model base and Field (Field unused here but kept for consistency).
from pydantic import BaseModel, Field

# Fleet-facing artifact pointer used on AgentTaskResult.
from packages.agent_sdk.src.models import ArtifactRef as FleetArtifactRef


class ArtifactRef(BaseModel):
    """Pointer to a versioned file. The bytes stay in artifact storage.

    Agents and memory services exchange this model when they need to cite
    evidence without embedding file contents in the JSON envelope. Optional
    provenance fields (tool, versions, digests) help auditors reproduce the
    environment that produced the bytes.

    Attributes:
        schema_name: Fixed discriminator ``eda.artifact-ref/v1``.
        uri: Storage URI where the bytes can be fetched.
        sha256: Optional content hash for integrity checks.
        type: Logical artifact type label (e.g. report format).
        producer_task: Task id that created the artifact.
        source_baseline: Design baseline the artifact was produced against.
        tool: Producing tool name.
        tool_version: Producing tool version string.
        environment_digest: Hash of the execution environment.
        complete: Whether the artifact is finalized vs still streaming.
    """

    # Schema discriminator for versioned EDA artifact pointers.
    schema_name: Literal["eda.artifact-ref/v1"] = "eda.artifact-ref/v1"
    # Location of the bytes in artifact storage.
    uri: str
    # Optional hex digest of the artifact contents.
    sha256: str = ""
    # Logical type label used as the fleet ref name when present.
    type: str = ""
    # Task that produced this artifact, when known.
    producer_task: str = ""
    # Baseline revision the producer ran against.
    source_baseline: str = ""
    # Tool name that wrote the bytes.
    tool: str = ""
    # Tool version string for reproducibility.
    tool_version: str = ""
    # Digest of the environment (containers, PDKs, etc.).
    environment_digest: str = ""
    # False while the producer is still writing; True when finalized.
    complete: bool = False

    def to_fleet_ref(self) -> FleetArtifactRef:
        """Convert this EDA pointer into the generic SDK artifact ref.

        Returns:
            A ``FleetArtifactRef`` with uri, name/format/description derived
            from ``type`` or ``uri``, and ``producer_task_id`` from
            ``producer_task``.

        Side effects:
            None.

        Failures:
            None beyond construction of the fleet model.
        """
        # Map EDA fields onto the thinner fleet artifact contract.
        return FleetArtifactRef(
            uri=self.uri,
            # Prefer the logical type as the display name; fall back to uri.
            name=self.type or self.uri,
            # Fleet format is fixed to json for these refs today.
            format="json",
            # Description mirrors the type label for operators.
            description=self.type,
            # Preserve producer lineage for the executor.
            producer_task_id=self.producer_task,
        )
