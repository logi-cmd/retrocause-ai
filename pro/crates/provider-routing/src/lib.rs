use retrocause_pro_domain::{
    CooldownKind, LedgerCategory, ProviderQuotaStatus, ProviderReadiness, ProviderStatusSnapshot,
    QuotaOwner, WorkspaceAccessGateDecision, WorkspaceAccessGateRequest, WorkspaceAccessGateStatus,
    WorkspaceAction, provider_status_snapshot, workspace_access_gate,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize)]
pub struct RoutingPreviewRequest {
    pub workspace_id: Option<String>,
    pub query: String,
    pub scenario: Option<RoutingScenario>,
    pub source_policy: Option<SourcePolicy>,
}

#[derive(Clone, Debug, Serialize)]
pub struct RoutingPreviewPlan {
    pub workspace_id: String,
    pub query: String,
    pub scenario: RoutingScenario,
    pub source_policy: SourcePolicy,
    pub mode: RoutingMode,
    pub execution_allowed: bool,
    pub selected_lane_id: Option<String>,
    pub steps: Vec<RoutingStep>,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderAdapterContract {
    pub mode: ProviderAdapterContractMode,
    pub execution_allowed: bool,
    pub request_fields: Vec<ProviderAdapterField>,
    pub result_fields: Vec<ProviderAdapterField>,
    pub degradation_states: Vec<ProviderAdapterDegradation>,
    pub quota_guards: Vec<String>,
    pub partial_result_rules: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct ProviderAdapterDryRunRequest {
    pub workspace_id: Option<String>,
    pub query: String,
    pub provider_lane_id: Option<String>,
    pub source_policy: Option<SourcePolicy>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderAdapterDryRunResult {
    pub workspace_id: String,
    pub query: String,
    pub provider_lane_id: String,
    pub source_policy: SourcePolicy,
    pub mode: ProviderAdapterDryRunMode,
    pub execution_allowed: bool,
    pub partial_result_available: bool,
    pub evidence_preview: Vec<ProviderAdapterEvidencePreview>,
    pub usage_ledger_preview: Vec<ProviderAdapterUsagePreview>,
    pub degradation_states: Vec<ProviderAdapterDegradation>,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderAdapterCandidateCatalog {
    pub mode: ProviderAdapterCandidateMode,
    pub execution_allowed: bool,
    pub candidates: Vec<ProviderAdapterCandidate>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderAdapterCandidate {
    pub id: &'static str,
    pub label: &'static str,
    pub provider_kind: &'static str,
    pub lane_id: &'static str,
    pub category: LedgerCategory,
    pub execution_allowed: bool,
    pub required_gates: Vec<ProviderAdapterGate>,
    pub description: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ProviderAdapterGate {
    pub id: &'static str,
    pub label: &'static str,
    pub owner: &'static str,
    pub status: ProviderAdapterGateStatus,
    pub description: &'static str,
}

#[derive(Clone, Debug, Deserialize)]
pub struct ProviderAdapterGateCheckRequest {
    pub workspace_id: Option<String>,
    pub candidate_id: Option<String>,
    pub dry_run_observed: bool,
    pub auth_context_observed: bool,
    pub quota_owner_confirmed: bool,
    pub event_timeline_observed: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderAdapterGateCheckResult {
    pub workspace_id: String,
    pub candidate_id: String,
    pub mode: ProviderAdapterGateCheckMode,
    pub execution_allowed: bool,
    pub gates: Vec<ProviderAdapterGate>,
    pub blocking_reasons: Vec<String>,
    pub warnings: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Deserialize)]
pub struct ExecutionReadinessRequest {
    pub workspace_id: Option<String>,
    pub run_id: Option<String>,
    pub candidate_id: Option<String>,
    pub dry_run_observed: bool,
    pub auth_context_observed: bool,
    pub quota_owner_confirmed: bool,
    pub event_timeline_observed: bool,
    pub work_order_observed: bool,
    pub commit_intent_observed: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionReadinessDecision {
    pub workspace_id: String,
    pub run_id: String,
    pub candidate_id: String,
    pub mode: ExecutionReadinessMode,
    pub status: ExecutionReadinessStatus,
    pub execution_allowed: bool,
    pub workspace_gate: WorkspaceAccessGateDecision,
    pub provider_gate: ProviderAdapterGateCheckResult,
    pub worker_commit_gate: WorkspaceAccessGateDecision,
    pub snapshot_persistence_gate: WorkspaceAccessGateDecision,
    pub preview_observations: Vec<ExecutionReadinessObservation>,
    pub blocking_reasons: Vec<String>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionReadinessObservation {
    pub id: &'static str,
    pub label: &'static str,
    pub observed: bool,
    pub required_before_live_execution: bool,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAdapterContractMode {
    DryContractOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAdapterDryRunMode {
    DryRunOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAdapterCandidateMode {
    GatedCandidateOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAdapterGateCheckMode {
    DeniedPreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionReadinessMode {
    ComposedPreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionReadinessStatus {
    DeniedRequiresHostedGates,
    DeniedUnknownWorkspace,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAdapterGateStatus {
    SatisfiedPreview,
    Blocked,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ProviderAdapterField {
    pub id: &'static str,
    pub owner: &'static str,
    pub required: bool,
    pub purpose: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ProviderAdapterDegradation {
    pub id: &'static str,
    pub status: &'static str,
    pub retry_policy: &'static str,
    pub preserves_partial_results: bool,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ProviderAdapterEvidencePreview {
    pub id: String,
    pub title: String,
    pub source: String,
    pub status: String,
    pub excerpt: String,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ProviderAdapterUsagePreview {
    pub lane_id: String,
    pub category: LedgerCategory,
    pub quota_owner: QuotaOwner,
    pub billable_units: u32,
    pub cooldown_retry_after_seconds: Option<u32>,
    pub note: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct RoutingStep {
    pub lane_id: String,
    pub label: String,
    pub category: LedgerCategory,
    pub quota_owner: QuotaOwner,
    pub readiness: ProviderReadiness,
    pub decision: RoutingDecision,
    pub action: RoutingAction,
    pub retry_after_seconds: Option<u32>,
    pub reason: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingScenario {
    Auto,
    Market,
    Policy,
    Postmortem,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SourcePolicy {
    Balanced,
    PrimaryOnly,
    UserEvidenceOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingMode {
    PreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingDecision {
    Selectable,
    CoolingDown,
    NotConfigured,
    Deferred,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingAction {
    UseUploadedEvidence,
    WaitForCooldown,
    ConfigureWorkspaceQuota,
    DeferHostedProvider,
}

#[derive(Debug)]
pub enum RoutingPreviewError {
    QueryRequired,
}

pub fn build_routing_preview(
    request: RoutingPreviewRequest,
) -> Result<RoutingPreviewPlan, RoutingPreviewError> {
    build_routing_preview_from_status(request, provider_status_snapshot())
}

pub fn provider_adapter_contract() -> ProviderAdapterContract {
    ProviderAdapterContract {
        mode: ProviderAdapterContractMode::DryContractOnly,
        execution_allowed: false,
        request_fields: vec![
            ProviderAdapterField {
                id: "workspace_id",
                owner: "api",
                required: true,
                purpose: "Tenant boundary used for quota, policy, storage, and audit scope.",
            },
            ProviderAdapterField {
                id: "job_id",
                owner: "queue",
                required: true,
                purpose: "Durable execution job identifier claimed by a worker lease.",
            },
            ProviderAdapterField {
                id: "provider_lane_id",
                owner: "provider_router",
                required: true,
                purpose: "Selected model/search/source lane with quota owner and credential policy.",
            },
            ProviderAdapterField {
                id: "source_policy",
                owner: "api",
                required: true,
                purpose: "Controls whether primary sources, balanced sources, or user evidence may be used.",
            },
            ProviderAdapterField {
                id: "evidence_context",
                owner: "worker_pool",
                required: false,
                purpose: "Optional uploaded or cached evidence that can support partial results.",
            },
        ],
        result_fields: vec![
            ProviderAdapterField {
                id: "evidence_items",
                owner: "provider_adapter",
                required: true,
                purpose: "Normalized evidence snippets with citation anchors and source status.",
            },
            ProviderAdapterField {
                id: "usage_ledger_rows",
                owner: "provider_adapter",
                required: true,
                purpose: "Quota owner, provider lane, billable units, and cooldown hints.",
            },
            ProviderAdapterField {
                id: "degraded_source_states",
                owner: "provider_adapter",
                required: true,
                purpose: "Machine-readable source/provider degradation state for reviewability.",
            },
            ProviderAdapterField {
                id: "partial_result",
                owner: "provider_adapter",
                required: false,
                purpose: "Inspectable evidence when at least one lane succeeds but another degrades.",
            },
        ],
        degradation_states: vec![
            ProviderAdapterDegradation {
                id: "provider_rate_limited",
                status: "retryable",
                retry_policy: "retry_after_cooldown_or_failover",
                preserves_partial_results: true,
            },
            ProviderAdapterDegradation {
                id: "provider_timeout",
                status: "retryable",
                retry_policy: "retry_with_backoff",
                preserves_partial_results: true,
            },
            ProviderAdapterDegradation {
                id: "provider_forbidden",
                status: "terminal_for_lane",
                retry_policy: "switch_lane_or_fix_credentials",
                preserves_partial_results: true,
            },
            ProviderAdapterDegradation {
                id: "source_limited",
                status: "reviewable_degraded",
                retry_policy: "continue_with_visible_gap",
                preserves_partial_results: true,
            },
            ProviderAdapterDegradation {
                id: "provider_empty_result",
                status: "reviewable_gap",
                retry_policy: "try_alternate_query_or_lane",
                preserves_partial_results: false,
            },
        ],
        quota_guards: vec![
            "quota_owner_must_be_explicit".to_string(),
            "cooldown_must_emit_retry_after_seconds".to_string(),
            "workspace_quota_must_not_use_managed_pool_silently".to_string(),
            "user_owned_quota_must_be_labeled_byok_later".to_string(),
            "adapter_results_must_emit_usage_ledger_rows".to_string(),
        ],
        partial_result_rules: vec![
            "preserve_successful_evidence_before_retry".to_string(),
            "surface_degraded_source_states_to_review_ui".to_string(),
            "never_upgrade_partial_results_to_ready_without_evidence".to_string(),
            "cite_provider_or_source_for_each_llm_claim".to_string(),
        ],
    }
}

pub fn provider_adapter_dry_run(
    request: ProviderAdapterDryRunRequest,
) -> Result<ProviderAdapterDryRunResult, RoutingPreviewError> {
    let source_policy = request.source_policy.unwrap_or(SourcePolicy::Balanced);
    let snapshot = provider_status_snapshot();
    let route_plan = build_routing_preview_from_status(
        RoutingPreviewRequest {
            workspace_id: request.workspace_id.clone(),
            query: request.query.clone(),
            scenario: None,
            source_policy: Some(source_policy),
        },
        snapshot,
    )?;

    let provider_lane_id = request
        .provider_lane_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string)
        .or_else(|| route_plan.selected_lane_id.clone())
        .unwrap_or_else(|| "no_selectable_lane".to_string());
    let route_step = route_plan
        .steps
        .iter()
        .find(|step| step.lane_id == provider_lane_id);
    let contract = provider_adapter_contract();
    let mut warnings = vec![
        "dry_run_only_no_provider_calls".to_string(),
        "provider_credentials_not_read".to_string(),
        "usage_ledger_preview_only".to_string(),
    ];
    warnings.extend(route_plan.warnings.clone());
    if route_step.is_none() {
        warnings.push("provider_lane_not_in_route_preview".to_string());
    }

    Ok(ProviderAdapterDryRunResult {
        workspace_id: route_plan.workspace_id,
        query: route_plan.query.clone(),
        provider_lane_id: provider_lane_id.clone(),
        source_policy,
        mode: ProviderAdapterDryRunMode::DryRunOnly,
        execution_allowed: false,
        partial_result_available: true,
        evidence_preview: vec![
            ProviderAdapterEvidencePreview {
                id: "dry_run_query".to_string(),
                title: "Operator question captured".to_string(),
                source: "operator_question".to_string(),
                status: "preview_only".to_string(),
                excerpt: format!("Dry-run captured query: {}", route_plan.query),
            },
            ProviderAdapterEvidencePreview {
                id: "dry_run_adapter_shape".to_string(),
                title: "Adapter evidence placeholder".to_string(),
                source: provider_lane_id.clone(),
                status: "not_executed".to_string(),
                excerpt: "Future adapters must return normalized evidence with source status before graph synthesis.".to_string(),
            },
        ],
        usage_ledger_preview: vec![ProviderAdapterUsagePreview {
            lane_id: provider_lane_id,
            category: route_step
                .map(|step| step.category)
                .unwrap_or(LedgerCategory::Search),
            quota_owner: route_step
                .map(|step| step.quota_owner)
                .unwrap_or(QuotaOwner::ManagedPro),
            billable_units: 0,
            cooldown_retry_after_seconds: route_step.and_then(|step| step.retry_after_seconds),
            note: "Dry run only; no provider calls, no credential reads, and no billable usage."
                .to_string(),
        }],
        degradation_states: contract
            .degradation_states
            .into_iter()
            .filter(|state| matches!(state.id, "provider_rate_limited" | "source_limited"))
            .collect(),
        warnings,
    })
}

pub fn provider_adapter_candidates() -> ProviderAdapterCandidateCatalog {
    ProviderAdapterCandidateCatalog {
        mode: ProviderAdapterCandidateMode::GatedCandidateOnly,
        execution_allowed: false,
        candidates: vec![ofoxai_model_candidate()],
        safeguards: vec![
            "candidate_registration_only_no_live_calls".to_string(),
            "auth_quota_dry_run_and_event_gates_required".to_string(),
            "credential_vault_not_connected".to_string(),
            "worker_execution_disabled".to_string(),
        ],
    }
}

pub fn provider_adapter_gate_check(
    request: ProviderAdapterGateCheckRequest,
) -> ProviderAdapterGateCheckResult {
    let workspace_id = request
        .workspace_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("workspace_demo")
        .to_string();
    let requested_candidate_id = request
        .candidate_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("ofoxai_model_candidate")
        .to_string();
    let candidate_registered = requested_candidate_id == "ofoxai_model_candidate";

    let gates = vec![
        gate(
            "adapter_dry_run_reviewed",
            "Adapter dry-run reviewed",
            "provider_router",
            preview_gate_status(request.dry_run_observed),
            "A dry-run result must be reviewed before any live adapter can be considered.",
        ),
        gate(
            "workspace_auth_context_reviewed",
            "Workspace auth context reviewed",
            "api",
            preview_gate_status(request.auth_context_observed),
            "The current preview auth context must be visible, but real enforcement is still required.",
        ),
        gate(
            "quota_owner_confirmed",
            "Quota owner confirmed",
            "provider_router",
            preview_gate_status(request.quota_owner_confirmed),
            "The candidate must have an explicit quota owner before execution.",
        ),
        gate(
            "run_event_timeline_seen",
            "Run event timeline seen",
            "api",
            preview_gate_status(request.event_timeline_observed),
            "The run status/event vocabulary must be visible before workers emit live status.",
        ),
        gate(
            "workspace_auth_enforced",
            "Workspace auth enforced",
            "auth_service_later",
            ProviderAdapterGateStatus::Blocked,
            "Real tenant and actor enforcement is not implemented yet.",
        ),
        gate(
            "credential_vault_connected",
            "Credential vault connected",
            "worker_boundary_later",
            ProviderAdapterGateStatus::Blocked,
            "Provider credentials must come from a vault-owned worker boundary later.",
        ),
        gate(
            "quota_ledger_connected",
            "Quota ledger connected",
            "billing_later",
            ProviderAdapterGateStatus::Blocked,
            "Billable usage and shared-pool limits are not connected yet.",
        ),
        gate(
            "worker_execution_enabled",
            "Worker execution enabled",
            "worker_pool_later",
            ProviderAdapterGateStatus::Blocked,
            "No worker process is allowed to execute provider calls in this slice.",
        ),
    ];

    let mut blocking_reasons = gates
        .iter()
        .filter(|gate| gate.status == ProviderAdapterGateStatus::Blocked)
        .map(|gate| gate.id.to_string())
        .collect::<Vec<String>>();
    if !candidate_registered {
        blocking_reasons.insert(0, "candidate_not_registered".to_string());
    }

    let mut warnings = vec![
        "live_provider_execution_denied".to_string(),
        "gate_check_is_preview_only".to_string(),
        "no_provider_credentials_read".to_string(),
    ];
    if !candidate_registered {
        warnings.push("requested_candidate_not_registered".to_string());
    }

    ProviderAdapterGateCheckResult {
        workspace_id,
        candidate_id: requested_candidate_id,
        mode: ProviderAdapterGateCheckMode::DeniedPreviewOnly,
        execution_allowed: false,
        gates,
        blocking_reasons,
        warnings,
        next_required_step:
            "Implement real tenant auth, credential vault reads, quota ledger enforcement, and worker execution before enabling any live adapter."
                .to_string(),
    }
}

pub fn execution_readiness_gate(request: ExecutionReadinessRequest) -> ExecutionReadinessDecision {
    let workspace_id = request
        .workspace_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("workspace_demo")
        .to_string();
    let run_id = request
        .run_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("run_semiconductor_controls_001")
        .to_string();
    let candidate_id = request
        .candidate_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("ofoxai_model_candidate")
        .to_string();

    let workspace_gate = workspace_access_gate(WorkspaceAccessGateRequest {
        workspace_id: Some(workspace_id.clone()),
        action: WorkspaceAction::ExecuteProviderCalls,
        resource: Some(candidate_id.clone()),
    });
    let provider_gate = provider_adapter_gate_check(ProviderAdapterGateCheckRequest {
        workspace_id: Some(workspace_id.clone()),
        candidate_id: Some(candidate_id.clone()),
        dry_run_observed: request.dry_run_observed,
        auth_context_observed: request.auth_context_observed,
        quota_owner_confirmed: request.quota_owner_confirmed,
        event_timeline_observed: request.event_timeline_observed,
    });
    let worker_commit_gate = workspace_access_gate(WorkspaceAccessGateRequest {
        workspace_id: Some(workspace_id.clone()),
        action: WorkspaceAction::CommitWorkerResult,
        resource: Some(run_id.clone()),
    });
    let snapshot_persistence_gate = workspace_access_gate(WorkspaceAccessGateRequest {
        workspace_id: Some(workspace_id.clone()),
        action: WorkspaceAction::PersistResultSnapshot,
        resource: Some(run_id.clone()),
    });

    let preview_observations = vec![
        readiness_observation(
            "adapter_dry_run_observed",
            "Adapter dry-run observed",
            request.dry_run_observed,
        ),
        readiness_observation(
            "workspace_access_context_observed",
            "Workspace access context observed",
            request.auth_context_observed,
        ),
        readiness_observation(
            "quota_owner_confirmed",
            "Quota owner confirmed",
            request.quota_owner_confirmed,
        ),
        readiness_observation(
            "run_event_timeline_observed",
            "Run event timeline observed",
            request.event_timeline_observed,
        ),
        readiness_observation(
            "worker_work_order_observed",
            "Worker work order observed",
            request.work_order_observed,
        ),
        readiness_observation(
            "worker_commit_intent_observed",
            "Worker commit intent observed",
            request.commit_intent_observed,
        ),
    ];

    let mut blocking_reasons = Vec::new();
    if workspace_gate.status == WorkspaceAccessGateStatus::DeniedUnknownWorkspace {
        blocking_reasons.push("workspace_gate_denied_unknown_workspace".to_string());
    }
    blocking_reasons.extend(
        workspace_gate
            .blocking_reasons
            .iter()
            .map(|reason| format!("workspace_gate:{reason}")),
    );
    blocking_reasons.extend(
        provider_gate
            .blocking_reasons
            .iter()
            .map(|reason| format!("provider_gate:{reason}")),
    );
    blocking_reasons.extend(
        worker_commit_gate
            .blocking_reasons
            .iter()
            .map(|reason| format!("worker_commit_gate:{reason}")),
    );
    blocking_reasons.extend(
        snapshot_persistence_gate
            .blocking_reasons
            .iter()
            .map(|reason| format!("snapshot_gate:{reason}")),
    );
    for observation in &preview_observations {
        if !observation.observed {
            blocking_reasons.push(format!("missing_preview_observation:{}", observation.id));
        }
    }
    blocking_reasons = dedupe_strings(blocking_reasons);

    let status = if workspace_gate.status == WorkspaceAccessGateStatus::DeniedUnknownWorkspace {
        ExecutionReadinessStatus::DeniedUnknownWorkspace
    } else {
        ExecutionReadinessStatus::DeniedRequiresHostedGates
    };

    ExecutionReadinessDecision {
        workspace_id,
        run_id,
        candidate_id,
        mode: ExecutionReadinessMode::ComposedPreviewOnly,
        status,
        execution_allowed: false,
        workspace_gate,
        provider_gate,
        worker_commit_gate,
        snapshot_persistence_gate,
        preview_observations,
        blocking_reasons,
        safeguards: vec![
            "execution_readiness_is_preview_only".to_string(),
            "workspace_access_gate_checked_before_execution".to_string(),
            "provider_gate_checked_before_execution".to_string(),
            "worker_and_result_commit_gates_checked_before_execution".to_string(),
            "no_provider_calls".to_string(),
            "no_credential_reads".to_string(),
            "no_quota_or_billing_mutation".to_string(),
            "no_worker_execution_or_result_writes".to_string(),
        ],
        next_required_step:
            "Implement hosted auth, vault handles, quota reservations, worker leases, and idempotent result-event writes before enabling execution."
                .to_string(),
    }
}

pub fn build_routing_preview_from_status(
    request: RoutingPreviewRequest,
    snapshot: ProviderStatusSnapshot,
) -> Result<RoutingPreviewPlan, RoutingPreviewError> {
    let query = request.query.trim();
    if query.is_empty() {
        return Err(RoutingPreviewError::QueryRequired);
    }

    let scenario = request.scenario.unwrap_or(RoutingScenario::Auto);
    let source_policy = request.source_policy.unwrap_or(SourcePolicy::Balanced);
    let workspace_id = request
        .workspace_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or(snapshot.workspace_id.as_str())
        .to_string();

    let steps = snapshot
        .entries
        .iter()
        .map(|entry| routing_step_for(entry, source_policy))
        .collect::<Vec<RoutingStep>>();
    let selected_lane_id = steps
        .iter()
        .find(|step| matches!(step.decision, RoutingDecision::Selectable))
        .map(|step| step.lane_id.clone());

    Ok(RoutingPreviewPlan {
        workspace_id,
        query: query.to_string(),
        scenario,
        source_policy,
        mode: RoutingMode::PreviewOnly,
        execution_allowed: false,
        selected_lane_id,
        steps,
        warnings: vec![
            "preview_only_no_provider_calls".to_string(),
            "hosted_provider_execution_deferred".to_string(),
        ],
    })
}

fn routing_step_for(entry: &ProviderQuotaStatus, source_policy: SourcePolicy) -> RoutingStep {
    let (decision, action, reason) = match entry.readiness {
        ProviderReadiness::Ready => {
            if source_policy == SourcePolicy::PrimaryOnly
                && matches!(entry.category, LedgerCategory::Evidence)
            {
                (
                    RoutingDecision::Deferred,
                    RoutingAction::DeferHostedProvider,
                    "Primary-only routing needs hosted source adapters that are not connected yet.",
                )
            } else {
                (
                    RoutingDecision::Selectable,
                    RoutingAction::UseUploadedEvidence,
                    "User-provided evidence is locally usable without provider credentials.",
                )
            }
        }
        ProviderReadiness::CoolingDown => (
            RoutingDecision::CoolingDown,
            RoutingAction::WaitForCooldown,
            "Shared provider lane is cooling down; future executor should queue or use another lane.",
        ),
        ProviderReadiness::NotConfigured => (
            RoutingDecision::NotConfigured,
            RoutingAction::ConfigureWorkspaceQuota,
            "Workspace-managed quota is not configured.",
        ),
        ProviderReadiness::Deferred => (
            RoutingDecision::Deferred,
            RoutingAction::DeferHostedProvider,
            "Hosted provider execution is planned but not implemented in this keyless slice.",
        ),
    };

    RoutingStep {
        lane_id: entry.id.clone(),
        label: entry.label.clone(),
        category: entry.category,
        quota_owner: entry.quota_owner,
        readiness: entry.readiness,
        decision,
        action,
        retry_after_seconds: match entry.cooldown.state {
            CooldownKind::CoolingDown => entry.cooldown.retry_after_seconds,
            CooldownKind::Clear | CooldownKind::NotApplicable => None,
        },
        reason: reason.to_string(),
    }
}

fn ofoxai_model_candidate() -> ProviderAdapterCandidate {
    ProviderAdapterCandidate {
        id: "ofoxai_model_candidate",
        label: "OfoxAI model adapter candidate",
        provider_kind: "hosted_model",
        lane_id: "managed_model_pool",
        category: LedgerCategory::Model,
        execution_allowed: false,
        required_gates: vec![
            gate(
                "adapter_dry_run_reviewed",
                "Adapter dry-run reviewed",
                "provider_router",
                ProviderAdapterGateStatus::Blocked,
                "Dry-run request/result shape must be reviewed before live execution.",
            ),
            gate(
                "workspace_auth_enforced",
                "Workspace auth enforced",
                "auth_service_later",
                ProviderAdapterGateStatus::Blocked,
                "Tenant and actor enforcement must exist before provider execution.",
            ),
            gate(
                "quota_ledger_connected",
                "Quota ledger connected",
                "billing_later",
                ProviderAdapterGateStatus::Blocked,
                "Managed provider usage must be metered before live calls.",
            ),
            gate(
                "run_event_timeline_seen",
                "Run event timeline seen",
                "api",
                ProviderAdapterGateStatus::Blocked,
                "Live workers need visible status/event vocabulary before execution.",
            ),
        ],
        description: "First future managed-model candidate for extraction and graph synthesis after all live gates exist.",
    }
}

fn preview_gate_status(observed: bool) -> ProviderAdapterGateStatus {
    if observed {
        ProviderAdapterGateStatus::SatisfiedPreview
    } else {
        ProviderAdapterGateStatus::Blocked
    }
}

fn readiness_observation(
    id: &'static str,
    label: &'static str,
    observed: bool,
) -> ExecutionReadinessObservation {
    ExecutionReadinessObservation {
        id,
        label,
        observed,
        required_before_live_execution: true,
    }
}

fn gate(
    id: &'static str,
    label: &'static str,
    owner: &'static str,
    status: ProviderAdapterGateStatus,
    description: &'static str,
) -> ProviderAdapterGate {
    ProviderAdapterGate {
        id,
        label,
        owner,
        status,
        description,
    }
}

fn dedupe_strings(items: Vec<String>) -> Vec<String> {
    let mut deduped = Vec::new();
    for item in items {
        if !deduped.contains(&item) {
            deduped.push(item);
        }
    }
    deduped
}

impl std::fmt::Display for RoutingPreviewError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::QueryRequired => write!(formatter, "query_required"),
        }
    }
}

impl std::error::Error for RoutingPreviewError {}

#[cfg(test)]
mod tests {
    use super::{
        ExecutionReadinessMode, ExecutionReadinessRequest, ExecutionReadinessStatus,
        ProviderAdapterCandidateMode, ProviderAdapterContractMode, ProviderAdapterDryRunMode,
        ProviderAdapterDryRunRequest, ProviderAdapterGateCheckMode,
        ProviderAdapterGateCheckRequest, ProviderAdapterGateStatus, RoutingDecision,
        RoutingPreviewError, RoutingPreviewRequest, RoutingScenario, SourcePolicy,
        build_routing_preview, execution_readiness_gate, provider_adapter_candidates,
        provider_adapter_contract, provider_adapter_dry_run, provider_adapter_gate_check,
    };

    #[test]
    fn preview_selects_user_evidence_without_allowing_execution() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: Some(" workspace_alpha ".to_string()),
            query: "Why did renewal conversion drop?".to_string(),
            scenario: Some(RoutingScenario::Postmortem),
            source_policy: Some(SourcePolicy::Balanced),
        })
        .expect("routing preview should build");

        assert_eq!(plan.workspace_id, "workspace_alpha");
        assert_eq!(plan.scenario, RoutingScenario::Postmortem);
        assert!(!plan.execution_allowed);
        assert_eq!(
            plan.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );
        assert!(
            plan.warnings
                .contains(&"preview_only_no_provider_calls".to_string())
        );
    }

    #[test]
    fn preview_surfaces_cooling_down_lanes() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "Why did chip stocks move?".to_string(),
            scenario: Some(RoutingScenario::Market),
            source_policy: None,
        })
        .expect("routing preview should build");

        let cooldown = plan
            .steps
            .iter()
            .find(|step| step.lane_id == "market_search_cooldown")
            .expect("cooldown lane should be present");

        assert_eq!(cooldown.decision, RoutingDecision::CoolingDown);
        assert_eq!(cooldown.retry_after_seconds, Some(900));
    }

    #[test]
    fn primary_only_policy_does_not_select_uploaded_evidence_lane() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "Why did a policy update matter?".to_string(),
            scenario: None,
            source_policy: Some(SourcePolicy::PrimaryOnly),
        })
        .expect("routing preview should build");

        assert_eq!(plan.source_policy, SourcePolicy::PrimaryOnly);
        assert_eq!(plan.selected_lane_id, None);
    }

    #[test]
    fn blank_query_is_rejected() {
        let error = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "   ".to_string(),
            scenario: None,
            source_policy: None,
        })
        .expect_err("blank query should fail");

        assert!(matches!(error, RoutingPreviewError::QueryRequired));
        assert_eq!(error.to_string(), "query_required");
    }

    #[test]
    fn adapter_contract_keeps_provider_execution_disabled_and_reviewable() {
        let contract = provider_adapter_contract();

        assert_eq!(contract.mode, ProviderAdapterContractMode::DryContractOnly);
        assert!(!contract.execution_allowed);
        assert!(
            contract
                .request_fields
                .iter()
                .any(|field| field.id == "workspace_id" && field.required)
        );
        assert!(
            contract
                .degradation_states
                .iter()
                .any(|state| state.id == "provider_rate_limited" && state.preserves_partial_results)
        );
        assert!(
            contract
                .quota_guards
                .contains(&"quota_owner_must_be_explicit".to_string())
        );
        assert!(
            contract
                .partial_result_rules
                .contains(&"surface_degraded_source_states_to_review_ui".to_string())
        );
    }

    #[test]
    fn adapter_dry_run_returns_zero_billable_preview_without_execution() {
        let result = provider_adapter_dry_run(ProviderAdapterDryRunRequest {
            workspace_id: Some(" workspace_alpha ".to_string()),
            query: "Why did AI infrastructure names move?".to_string(),
            provider_lane_id: Some("uploaded_evidence_lane".to_string()),
            source_policy: Some(SourcePolicy::Balanced),
        })
        .expect("dry run should build");

        assert_eq!(result.workspace_id, "workspace_alpha");
        assert_eq!(result.provider_lane_id, "uploaded_evidence_lane");
        assert_eq!(result.mode, ProviderAdapterDryRunMode::DryRunOnly);
        assert!(!result.execution_allowed);
        assert!(result.partial_result_available);
        assert_eq!(result.usage_ledger_preview[0].billable_units, 0);
        assert_eq!(
            result.usage_ledger_preview[0].quota_owner,
            retrocause_pro_domain::QuotaOwner::UserProvided
        );
        assert!(
            result
                .warnings
                .contains(&"dry_run_only_no_provider_calls".to_string())
        );
        assert!(
            result
                .degradation_states
                .iter()
                .any(|state| state.id == "provider_rate_limited")
        );
    }

    #[test]
    fn adapter_dry_run_rejects_blank_query() {
        let error = provider_adapter_dry_run(ProviderAdapterDryRunRequest {
            workspace_id: None,
            query: "   ".to_string(),
            provider_lane_id: None,
            source_policy: None,
        })
        .expect_err("blank query should fail");

        assert!(matches!(error, RoutingPreviewError::QueryRequired));
    }

    #[test]
    fn adapter_candidates_register_ofoxai_without_execution() {
        let catalog = provider_adapter_candidates();

        assert_eq!(
            catalog.mode,
            ProviderAdapterCandidateMode::GatedCandidateOnly
        );
        assert!(!catalog.execution_allowed);
        assert!(catalog.candidates.iter().any(|candidate| {
            candidate.id == "ofoxai_model_candidate"
                && candidate.lane_id == "managed_model_pool"
                && !candidate.execution_allowed
        }));
        assert!(
            catalog
                .safeguards
                .contains(&"credential_vault_not_connected".to_string())
        );
    }

    #[test]
    fn adapter_gate_check_denies_execution_even_when_preview_gates_are_seen() {
        let result = provider_adapter_gate_check(ProviderAdapterGateCheckRequest {
            workspace_id: Some(" workspace_alpha ".to_string()),
            candidate_id: Some("ofoxai_model_candidate".to_string()),
            dry_run_observed: true,
            auth_context_observed: true,
            quota_owner_confirmed: true,
            event_timeline_observed: true,
        });

        assert_eq!(result.workspace_id, "workspace_alpha");
        assert_eq!(result.candidate_id, "ofoxai_model_candidate");
        assert_eq!(result.mode, ProviderAdapterGateCheckMode::DeniedPreviewOnly);
        assert!(!result.execution_allowed);
        assert!(
            result
                .blocking_reasons
                .contains(&"workspace_auth_enforced".to_string())
        );
        assert!(
            result
                .blocking_reasons
                .contains(&"credential_vault_connected".to_string())
        );
        assert!(result.gates.iter().any(|gate| {
            gate.id == "adapter_dry_run_reviewed"
                && gate.status == ProviderAdapterGateStatus::SatisfiedPreview
        }));
    }

    #[test]
    fn adapter_gate_check_reports_missing_preview_gates() {
        let result = provider_adapter_gate_check(ProviderAdapterGateCheckRequest {
            workspace_id: None,
            candidate_id: Some("missing_candidate".to_string()),
            dry_run_observed: false,
            auth_context_observed: false,
            quota_owner_confirmed: false,
            event_timeline_observed: false,
        });

        assert!(!result.execution_allowed);
        assert!(
            result
                .blocking_reasons
                .contains(&"candidate_not_registered".to_string())
        );
        assert!(
            result
                .blocking_reasons
                .contains(&"adapter_dry_run_reviewed".to_string())
        );
        assert!(
            result
                .warnings
                .contains(&"requested_candidate_not_registered".to_string())
        );
    }

    #[test]
    fn execution_readiness_composes_workspace_provider_and_worker_gates() {
        let decision = execution_readiness_gate(ExecutionReadinessRequest {
            workspace_id: Some(" workspace_demo ".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            candidate_id: Some("ofoxai_model_candidate".to_string()),
            dry_run_observed: true,
            auth_context_observed: true,
            quota_owner_confirmed: true,
            event_timeline_observed: true,
            work_order_observed: true,
            commit_intent_observed: true,
        });

        assert_eq!(decision.workspace_id, "workspace_demo");
        assert_eq!(decision.candidate_id, "ofoxai_model_candidate");
        assert_eq!(decision.mode, ExecutionReadinessMode::ComposedPreviewOnly);
        assert_eq!(
            decision.status,
            ExecutionReadinessStatus::DeniedRequiresHostedGates
        );
        assert!(!decision.execution_allowed);
        assert!(!decision.workspace_gate.allowed);
        assert!(!decision.provider_gate.execution_allowed);
        assert!(!decision.worker_commit_gate.allowed);
        assert!(!decision.snapshot_persistence_gate.allowed);
        assert!(
            decision
                .preview_observations
                .iter()
                .all(|item| item.observed)
        );
        assert!(
            decision
                .blocking_reasons
                .contains(&"provider_gate:workspace_auth_enforced".to_string())
        );
        assert!(
            decision
                .blocking_reasons
                .contains(&"worker_commit_gate:idempotent_event_store_write_required".to_string())
        );
        assert!(
            decision
                .safeguards
                .contains(&"no_provider_calls".to_string())
        );
    }

    #[test]
    fn execution_readiness_reports_missing_preview_observations_and_unknown_workspace() {
        let decision = execution_readiness_gate(ExecutionReadinessRequest {
            workspace_id: Some("workspace_other".to_string()),
            run_id: None,
            candidate_id: Some("missing_candidate".to_string()),
            dry_run_observed: false,
            auth_context_observed: false,
            quota_owner_confirmed: false,
            event_timeline_observed: false,
            work_order_observed: false,
            commit_intent_observed: false,
        });

        assert_eq!(
            decision.status,
            ExecutionReadinessStatus::DeniedUnknownWorkspace
        );
        assert!(!decision.execution_allowed);
        assert!(
            decision
                .blocking_reasons
                .contains(&"workspace_gate_denied_unknown_workspace".to_string())
        );
        assert!(
            decision
                .blocking_reasons
                .contains(&"provider_gate:candidate_not_registered".to_string())
        );
        assert!(
            decision
                .blocking_reasons
                .contains(&"missing_preview_observation:adapter_dry_run_observed".to_string())
        );
        let combined = format!(
            "{:?} {:?} {:?}",
            decision.blocking_reasons, decision.safeguards, decision.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
    }
}
