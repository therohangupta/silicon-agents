"""Tools for the Verification Lead in the EDA chip-design agent fleet.

This module is the stable operation contract for the frontend verification
lead. Each decorated function is a skill the LLM (or orchestrator) may invoke
while closing coverage on one pinned RTL revision. The bodies do not call a
simulator, formal engine, or OpenROAD directly: they assemble a typed payload
and return ``tool_observation(...)``, which records the intended operation.

Until a framework adapter is bound, observations typically surface status
``not_run`` and never invoke OpenROAD, Yosys, OpenSTA, a licensed EDA tool, or
a UVM simulator. Skill ids here must stay aligned with ``config.yaml``
``capabilities`` / ``skills`` entries so the AgentService can dispatch by name.

EDA meaning of this surface:
- Workflow tools open child tasks (UVM env, ref model, formal, stimulus,
  regression, reproduction, independent gate).
- Read tools inspect contracts, coverage, failure clusters, and regression
  status for planning.
- Publish / escalate tools write findings back into engineering memory.
- Human-decision tools never approve waivers; they only request a human.
"""

from __future__ import annotations  # Allow modern typing (dict | None) without runtime eval cost.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.adapters import tool_observation  # Builds the standard observation dict (status, payload, agent_id).


@tool(description='Emit the closure workflow for this RTL revision.')
def build_verification_plan(
    objective: str = "",  # Natural-language outcome the child workflow must achieve.
    parent_task_id: str = "",  # Orchestrator task that owns this workflow; empty if top-level.
    scope_block: str = "",  # Hierarchical block name; empty means the task's current block.
    params: dict | None = None,  # Optional extra fields merged into the observation payload.
) -> dict:
    """Emit the verification closure workflow for the pinned RTL revision.

    Purpose:
        Ask the framework to materialize the lead's plan graph (UVM, formal,
        stimulus, regression, coverage, triage, reproduction, validator) as a
        concrete workflow for this candidate.

    Arguments:
        objective: Outcome string the child workflow must achieve.
        parent_task_id: Owning task id for lineage in the journal.
        scope_block: Block scope; empty inherits the current task block.
        params: Optional dict merged over the base payload keys.

    Returns:
        A ``tool_observation`` dict for skill ``build_verification_plan`` tagged
        with ``agent_id='verification_lead'``.

    Side effects:
        None locally. The adapter may create workflow records when bound.

    Failure behavior:
        Unbound adapters return ``not_run``. Invalid params are still forwarded
        in the payload for the adapter to reject.
    """
    # Base fields the create_workflow action expects for every lead-opened child plan.
    payload = {
        'objective': objective,  # What success looks like for this closure plan.
        'parent_task_id': parent_task_id,  # Journal parent for dependency tracking.
        'scope_block': scope_block  # Which RTL block the plan covers.
    }
    if params:
        # Caller-supplied extras win on key collision so adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'build_verification_plan',  # Skill id; must match config.yaml skills[].callable.
        payload,  # Structured arguments for the create_workflow action.
        agent_id='verification_lead',  # Attribution in telemetry and journal entries.
    )


@tool(description='Open a task to build or update the UVM environment.')
def request_uvm_environment(
    objective: str = "",  # Desired UVM env outcome (e.g. drivers/monitors for AXI).
    parent_task_id: str = "",  # Parent task that requested environment work.
    scope_block: str = "",  # Block whose interfaces need UVM agents.
    params: dict | None = None,  # Optional adapter-specific extensions.
) -> dict:
    """Open a delegated task for the UVM Environment specialist.

    Purpose:
        Kick off construction or update of drivers, monitors, scoreboards, and
        sequences for the block under verification—without the lead writing UVM
        SystemVerilog itself.

    Arguments:
        objective: Outcome the uvm_environment agent must achieve.
        parent_task_id: Owning task id for the child workflow.
        scope_block: Block the environment applies to.
        params: Optional extra payload fields.

    Returns:
        Observation for ``request_uvm_environment`` from verification_lead.

    Side effects:
        May enqueue a child workflow when the adapter is bound.

    Failure behavior:
        Returns ``not_run`` until a framework adapter performs the create.
    """
    payload = {
        'objective': objective,  # Handed to uvm_environment as its task objective.
        'parent_task_id': parent_task_id,  # Keeps delegation lineage under the lead.
        'scope_block': scope_block  # Ensures the env matches the DUT block hierarchy.
    }
    if params:
        payload.update(params)  # Merge optional fields after the required keys.
    return tool_observation(
        'request_uvm_environment',  # Maps to plan step agent: uvm_environment.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Open a task to build the behavioral reference model.')
def request_reference_model(
    objective: str = "",  # Desired reference-model outcome from the specification.
    parent_task_id: str = "",  # Parent task id for journal linkage.
    scope_block: str = "",  # Block the behavioral model must encode.
    params: dict | None = None,  # Optional extras for the adapter.
) -> dict:
    """Open a delegated task for the Reference Model specialist.

    Purpose:
        Request a behavioral golden model that encodes the specification so the
        UVM scoreboard can compare DUT outputs against expected transactions.

    Arguments:
        objective: Outcome for the reference_model agent.
        parent_task_id: Owning task id.
        scope_block: Block scope for the model.
        params: Optional payload extensions.

    Returns:
        Observation for ``request_reference_model``.

    Side effects:
        May create a child workflow when bound.

    Failure behavior:
        ``not_run`` until the adapter creates the task.
    """
    payload = {
        'objective': objective,  # Spec-encoding goal for the reference model.
        'parent_task_id': parent_task_id,
        'scope_block': scope_block
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_reference_model',  # Delegates to reference_model agent in the plan.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Open a formal proof task for the named properties.')
def request_formal_campaign(
    objective: str = "",  # Which properties / requirements to prove.
    parent_task_id: str = "",  # Parent task for the formal campaign.
    scope_block: str = "",  # Block the SVA/bind targets.
    params: dict | None = None,  # Optional extras (property ids, engine hints).
) -> dict:
    """Open a formal assertion campaign via the Assertion/Formal specialist.

    Purpose:
        Launch property generation, assumptions, cover properties, and formal
        engine submission for named requirements—complementary to simulation.

    Arguments:
        objective: Formal campaign outcome string.
        parent_task_id: Owning task id.
        scope_block: Block under formal proof.
        params: Optional extra fields.

    Returns:
        Observation for ``request_formal_campaign``.

    Side effects:
        May enqueue assertion_formal work when bound.

    Failure behavior:
        ``not_run`` with no formal-engine invocation until bound.
    """
    payload = {
        'objective': objective,  # Names properties / proof goals for assertion_formal.
        'parent_task_id': parent_task_id,
        'scope_block': scope_block
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_formal_campaign',  # Plan step: assertion_formal.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Open stimulus work aimed at the listed coverage holes.')
def request_stimulus_for_holes(
    objective: str = "",  # Stimulus goal (directed/random toward holes).
    parent_task_id: str = "",  # Parent task id.
    scope_block: str = "",  # Block whose coverpoints need stimulus.
    hole_ids: str = "",  # Comma-separated coverage hole ids from the coverage agent.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Open stimulus generation targeted at listed coverage holes.

    Purpose:
        After coverage analysis lists uncovered bins/requirements, ask the
        stimulus agent to write directed or constrained-random tests that hit
        those holes—core of coverage-driven verification closure.

    Arguments:
        objective: Outcome for the stimulus agent.
        parent_task_id: Owning task id.
        scope_block: Block scope.
        hole_ids: Comma-separated hole identifiers to target.
        params: Optional payload extensions.

    Returns:
        Observation for ``request_stimulus_for_holes``.

    Side effects:
        May create a stimulus child workflow when bound.

    Failure behavior:
        Empty ``hole_ids`` is still forwarded; the adapter decides validity.
    """
    payload = {
        'objective': objective,
        'parent_task_id': parent_task_id,
        'scope_block': scope_block,
        'hole_ids': hole_ids  # Explicit hole list so stimulus is not blind random.
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_stimulus_for_holes',  # Plan step: stimulus (depends on uvm_environment).
        payload,
        agent_id='verification_lead',
    )


@tool(description='Open a regression for the current test manifest.')
def request_regression_campaign(
    objective: str = "",  # Regression campaign goal (seed list, suite name).
    parent_task_id: str = "",  # Parent task id.
    scope_block: str = "",  # Block under regression.
    params: dict | None = None,  # Optional extras (seed ranges, farm tags).
) -> dict:
    """Open a regression campaign over the current test manifest.

    Purpose:
        Ask the regression agent to compile, schedule, and collect simulation
        results for the active suite—feeding coverage merge and failure triage.

    Arguments:
        objective: Campaign outcome string.
        parent_task_id: Owning task id.
        scope_block: Block scope.
        params: Optional extras.

    Returns:
        Observation for ``request_regression_campaign``.

    Side effects:
        May schedule farm jobs when the adapter is bound.

    Failure behavior:
        No simulator launch until a framework adapter is configured.
    """
    payload = {
        'objective': objective,
        'parent_task_id': parent_task_id,
        'scope_block': scope_block
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_regression_campaign',  # Plan step: regression.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Open minimization for one failure cluster.')
def request_failure_reproduction(
    objective: str = "",  # Reproduction / minimize goal for the cluster.
    parent_task_id: str = "",  # Parent task id.
    scope_block: str = "",  # Block where the failure was observed.
    cluster_id: str = "",  # Failure cluster id from failure_triage.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Open failure reproduction/minimization for one triage cluster.

    Purpose:
        After failure_triage groups signatures, ask reproduction to shrink the
        seed/waveform to a minimal failing test that RTL or TB owners can debug.

    Arguments:
        objective: Outcome for the reproduction agent.
        parent_task_id: Owning task id.
        scope_block: Block scope.
        cluster_id: Cluster identifier to minimize.
        params: Optional extras.

    Returns:
        Observation for ``request_failure_reproduction``.

    Side effects:
        May enqueue reproduction work when bound.

    Failure behavior:
        Empty ``cluster_id`` is forwarded; adapter validates.
    """
    payload = {
        'objective': objective,
        'parent_task_id': parent_task_id,
        'scope_block': scope_block,
        'cluster_id': cluster_id  # Ties the request to one triage cluster.
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_failure_reproduction',  # Plan step: reproduction (depends on failure_triage).
        payload,
        agent_id='verification_lead',
    )


@tool(description='Hand the pinned candidate to the verification validator.')
def request_independent_verification_gate(
    objective: str = "",  # Gate objective (pass/fail the verification contract).
    parent_task_id: str = "",  # Parent task id.
    scope_block: str = "",  # Block being graded independently.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Hand the pinned candidate to the independent Verification Validator.

    Purpose:
        The lead must not grade its own closure. This opens the validator gate
        that re-reads primary reports, checks provenance, and emits pass/fail.

    Arguments:
        objective: Validator outcome string.
        parent_task_id: Owning task id.
        scope_block: Block scope.
        params: Optional extras.

    Returns:
        Observation for ``request_independent_verification_gate``.

    Side effects:
        May start verification_validator when bound.

    Failure behavior:
        ``not_run`` until the adapter creates the gate task.
    """
    payload = {
        'objective': objective,
        'parent_task_id': parent_task_id,
        'scope_block': scope_block
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_independent_verification_gate',  # Plan step: verification_validator.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Read the requirements, exclusions, and required checks for this candidate.')
def read_verification_contract(
    candidate_ref: str = "",  # Artifact/URI of the RTL candidate under verification.
    report_ref: str = "",  # Optional report URI; empty means latest for the candidate.
    corner: str = "",  # PVT corner filter; empty reads all available corners.
    mode: str = "",  # Mode filter (e.g. functional); empty reads all modes.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Read the verification contract for the candidate.

    Purpose:
        Load requirements, exclusions, and required checks so the lead can plan
        closure and know what the independent gate will enforce.

    Arguments:
        candidate_ref: Candidate identity whose contract is read.
        report_ref: Specific report URI or empty for latest.
        corner: Corner filter or empty for all.
        mode: Mode filter or empty for all.
        params: Optional extras.

    Returns:
        Observation for ``read_verification_contract`` (action: read_reports).

    Side effects:
        None locally; adapter may fetch artifacts from the silicon store.

    Failure behavior:
        Missing candidate typically yields empty/not_run from the adapter.
    """
    payload = {
        'candidate_ref': candidate_ref,  # Which RTL revision's contract to load.
        'report_ref': report_ref,  # Pin a report or take the latest.
        'corner': corner,  # Timing/process corner relevance for mixed-signoff flows.
        'mode': mode  # Operating mode slice of the contract.
    }
    if params:
        payload.update(params)
    return tool_observation(
        'read_verification_contract',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Read code, functional, and assertion coverage for the current regression.')
def read_coverage_summary(
    candidate_ref: str = "",  # Candidate whose coverage database was merged.
    report_ref: str = "",  # Coverage report URI or empty for latest.
    corner: str = "",  # Corner filter.
    mode: str = "",  # Mode filter.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Read the merged coverage summary for the current regression.

    Purpose:
        Inspect code, functional (covergroup), and assertion coverage so the
        lead can open stimulus toward holes or escalate closure gaps.

    Arguments:
        candidate_ref: Candidate identity.
        report_ref: Report URI or empty for latest.
        corner: Corner filter.
        mode: Mode filter.
        params: Optional extras.

    Returns:
        Observation for ``read_coverage_summary``.

    Side effects:
        Read-only artifact fetch when bound.

    Failure behavior:
        Missing merge DB → adapter reports not_run / missing input.
    """
    payload = {
        'candidate_ref': candidate_ref,
        'report_ref': report_ref,
        'corner': corner,
        'mode': mode
    }
    if params:
        payload.update(params)
    return tool_observation(
        'read_coverage_summary',  # Consumes coverage agent outputs.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Read clustered failures and their likely owners.')
def read_failure_clusters(
    candidate_ref: str = "",  # Candidate whose failing sims were triaged.
    report_ref: str = "",  # Cluster report URI or empty for latest.
    corner: str = "",  # Corner filter.
    mode: str = "",  # Mode filter.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Read failure clusters and likely owners from triage.

    Purpose:
        Use clustered signatures to decide which clusters need reproduction and
        which can be routed to RTL, TB, or infrastructure owners.

    Arguments:
        candidate_ref: Candidate identity.
        report_ref: Report URI or empty for latest.
        corner: Corner filter.
        mode: Mode filter.
        params: Optional extras.

    Returns:
        Observation for ``read_failure_clusters``.

    Side effects:
        Read-only when bound.

    Failure behavior:
        No triage yet → empty/not_run from adapter.
    """
    payload = {
        'candidate_ref': candidate_ref,
        'report_ref': report_ref,
        'corner': corner,
        'mode': mode
    }
    if params:
        payload.update(params)
    return tool_observation(
        'read_failure_clusters',  # Consumes failure_triage publish_failure_cluster outputs.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Read pass, fail, and infrastructure-error counts for the campaign.')
def read_regression_status(
    candidate_ref: str = "",  # Candidate whose regression was scheduled.
    report_ref: str = "",  # Status report URI or empty for latest.
    corner: str = "",  # Corner filter.
    mode: str = "",  # Mode filter.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Read pass/fail/infrastructure counts for the regression campaign.

    Purpose:
        Give the lead a campaign health snapshot before deciding to re-run,
        triage, or escalate infrastructure (license/timeout/compile) issues.

    Arguments:
        candidate_ref: Candidate identity.
        report_ref: Report URI or empty for latest.
        corner: Corner filter.
        mode: Mode filter.
        params: Optional extras.

    Returns:
        Observation for ``read_regression_status``.

    Side effects:
        Read-only when bound.

    Failure behavior:
        Campaign not started → not_run / empty counts from adapter.
    """
    payload = {
        'candidate_ref': candidate_ref,
        'report_ref': report_ref,
        'corner': corner,
        'mode': mode
    }
    if params:
        payload.update(params)
    return tool_observation(
        'read_regression_status',  # Consumes regression agent status artifacts.
        payload,
        agent_id='verification_lead',
    )


@tool(description='Publish holes that the current strategy has not closed.')
def publish_coverage_closure_gap(
    summary: str = "",  # One-sentence description of the unclosed holes.
    evidence_refs: str = "",  # Comma-separated artifact URIs supporting the finding.
    severity: str = "",  # low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act (often stimulus or human).
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Publish a finding that coverage closure has plateaued with open holes.

    Purpose:
        Record strategy failure in engineering memory so stimulus, humans, or
        RTL owners can react—without the lead waiving requirements itself.

    Arguments:
        summary: One-sentence finding.
        evidence_refs: Supporting artifact URIs.
        severity: Severity label.
        recommended_recipient: Suggested next owner agent id.
        params: Optional extras.

    Returns:
        Observation for ``publish_coverage_closure_gap`` (publish_finding).

    Side effects:
        May write a finding into shared silicon memory when bound.

    Failure behavior:
        Unbound → not_run; finding is not silently approved as a waiver.
    """
    payload = {
        'summary': summary,
        'evidence_refs': evidence_refs,
        'severity': severity,
        'recommended_recipient': recommended_recipient
    }
    if params:
        payload.update(params)
    return tool_observation(
        'publish_coverage_closure_gap',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Publish a finding when RTL and specification disagree.')
def escalate_spec_ambiguity(
    summary: str = "",  # Description of the RTL vs spec disagreement.
    evidence_refs: str = "",  # Supporting URIs (waves, clauses, RTL snippets).
    severity: str = "",  # Severity of the ambiguity for schedule impact.
    recommended_recipient: str = "",  # Often architecture/requirements or RTL lead.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Escalate when RTL behavior and the specification disagree.

    Purpose:
        Verification cannot close if the golden intent is ambiguous. This
        finding requests upstream clarification (UPSTREAM_CHANGE_REQUIRED path)
        rather than inventing a waiver.

    Arguments:
        summary: One-sentence ambiguity statement.
        evidence_refs: Supporting artifacts.
        severity: Severity label.
        recommended_recipient: Agent that should resolve the ambiguity.
        params: Optional extras.

    Returns:
        Observation for ``escalate_spec_ambiguity``.

    Side effects:
        May publish a finding when bound.

    Failure behavior:
        Does not modify RTL or approve a new interpretation unilaterally.
    """
    payload = {
        'summary': summary,
        'evidence_refs': evidence_refs,
        'severity': severity,
        'recommended_recipient': recommended_recipient
    }
    if params:
        payload.update(params)
    return tool_observation(
        'escalate_spec_ambiguity',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Route a reproduced functional defect back to the RTL lead.')
def request_rtl_fix(
    summary: str = "",  # Defect summary for the RTL owner.
    evidence_refs: str = "",  # Minimal seed / waveform / scoreboard mismatch URIs.
    severity: str = "",  # Defect severity.
    recommended_recipient: str = "",  # Typically the RTL lead agent id.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Route a reproduced functional defect to the RTL lead.

    Purpose:
        After reproduction minimizes a failing seed, hand a clear bug package
        upstream. The verification lead does not patch canonical RTL.

    Arguments:
        summary: One-sentence defect description.
        evidence_refs: Supporting artifact URIs.
        severity: Severity label.
        recommended_recipient: RTL owner agent id.
        params: Optional extras.

    Returns:
        Observation for ``request_rtl_fix``.

    Side effects:
        May publish a finding / open RTL work when bound.

    Failure behavior:
        Never edits RTL files from this skill.
    """
    payload = {
        'summary': summary,
        'evidence_refs': evidence_refs,
        'severity': severity,
        'recommended_recipient': recommended_recipient
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_rtl_fix',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Record a change in how closure is searched after a plateau.')
def record_verification_strategy_change(
    summary: str = "",  # What changed in the search strategy.
    evidence_refs: str = "",  # Evidence that the prior strategy plateaued.
    severity: str = "",  # Impact of the strategy change.
    recommended_recipient: str = "",  # Who should acknowledge the change.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Record a verification strategy change after a coverage/debug plateau.

    Purpose:
        Make search-policy shifts auditable (e.g. more formal, new constrained
        random knobs) so later reviewers understand why the plan graph mutated.

    Arguments:
        summary: Strategy-change description.
        evidence_refs: Supporting URIs.
        severity: Severity label.
        recommended_recipient: Optional recipient.
        params: Optional extras.

    Returns:
        Observation for ``record_verification_strategy_change``.

    Side effects:
        May publish a finding when bound.

    Failure behavior:
        Recording is advisory; it does not auto-approve exclusions.
    """
    payload = {
        'summary': summary,
        'evidence_refs': evidence_refs,
        'severity': severity,
        'recommended_recipient': recommended_recipient
    }
    if params:
        payload.update(params)
    return tool_observation(
        'record_verification_strategy_change',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Ask a human to approve or reject a verification exclusion. This agent cannot approve it.')
def request_verification_waiver(
    decision: str = "",  # The choice the human must make (approve/reject exclusion).
    options: str = "",  # Comma-separated feasible options.
    evidence_refs: str = "",  # Artifacts justifying why a waiver is even proposed.
    deadline: str = "",  # ISO-8601 time after which schedule is blocked.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Request a human decision on a verification waiver/exclusion.

    Purpose:
        Hard requirements cannot be waived by the lead. This skill only opens a
        human-decision ticket; approval authority stays with humans.

    Arguments:
        decision: Prompt describing the choice.
        options: Feasible options list.
        evidence_refs: Supporting artifacts.
        deadline: Blocking deadline in ISO-8601.
        params: Optional extras.

    Returns:
        Observation for ``request_verification_waiver`` (request_human_decision).

    Side effects:
        May create a human-decision record when bound.

    Failure behavior:
        The agent cannot approve the waiver via this or any other skill.
    """
    payload = {
        'decision': decision,
        'options': options,
        'evidence_refs': evidence_refs,
        'deadline': deadline
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_verification_waiver',
        payload,
        agent_id='verification_lead',
    )


@tool(description='Ask a human whether an unreachable coverpoint may be excluded.')
def request_exclusion_decision(
    decision: str = "",  # Human choice: exclude unreachable coverpoint or keep it open.
    options: str = "",  # Feasible options.
    evidence_refs: str = "",  # Unreachability evidence (formal, structural).
    deadline: str = "",  # ISO-8601 blocking deadline.
    params: dict | None = None,  # Optional extras.
) -> dict:
    """Request a human decision on excluding an unreachable coverpoint.

    Purpose:
        Suspected-unreachable coverpoints must not be auto-excluded to inflate
        coverage scores. A human reviews evidence before exclusion.

    Arguments:
        decision: Choice prompt for the human.
        options: Feasible options.
        evidence_refs: Unreachability evidence URIs.
        deadline: Blocking deadline.
        params: Optional extras.

    Returns:
        Observation for ``request_exclusion_decision``.

    Side effects:
        May open a human-decision ticket when bound.

    Failure behavior:
        No exclusion is applied by this skill itself.
    """
    payload = {
        'decision': decision,
        'options': options,
        'evidence_refs': evidence_refs,
        'deadline': deadline
    }
    if params:
        payload.update(params)
    return tool_observation(
        'request_exclusion_decision',
        payload,
        agent_id='verification_lead',
    )
