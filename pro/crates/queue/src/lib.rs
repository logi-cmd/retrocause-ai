use retrocause_pro_domain::{
    ExecutionAdmissionDecision, ExecutionAdmissionRequest, ExecutionPreflightBoundary,
    ResultCommitBoundary, WorkspaceAction, execution_admission, execution_preflight_boundary,
    result_commit_boundary,
};
use retrocause_pro_provider_routing::{
    RoutingPreviewError, RoutingPreviewPlan, RoutingPreviewRequest, RoutingStep,
    build_routing_preview,
};
use serde::Serialize;
use std::sync::{Arc, RwLock};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Default)]
pub struct ExecutionQueue {
    state: Arc<RwLock<QueueState>>,
}

#[derive(Clone, Debug, Default)]
struct QueueState {
    next_sequence: u64,
    jobs: Vec<ExecutionJob>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionJob {
    pub id: String,
    pub workspace_id: String,
    pub query: String,
    pub status: ExecutionJobStatus,
    pub execution_allowed: bool,
    pub selected_lane_id: Option<String>,
    pub route_plan: RoutingPreviewPlan,
    pub created_at_epoch_seconds: u64,
    pub updated_at_epoch_seconds: u64,
    pub note: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionJobSummary {
    pub id: String,
    pub workspace_id: String,
    pub query: String,
    pub status: ExecutionJobStatus,
    pub execution_allowed: bool,
    pub selected_lane_id: Option<String>,
    pub created_at_epoch_seconds: u64,
    pub updated_at_epoch_seconds: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionWorkOrder {
    pub job_id: String,
    pub workspace_id: String,
    pub query: String,
    pub mode: ExecutionWorkOrderMode,
    pub execution_allowed: bool,
    pub selected_lane_id: Option<String>,
    pub route_steps: Vec<RoutingStep>,
    pub routing_warnings: Vec<String>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionHandoffPreview {
    pub job_id: String,
    pub workspace_id: String,
    pub query: String,
    pub mode: ExecutionHandoffMode,
    pub execution_allowed: bool,
    pub work_order: ExecutionWorkOrder,
    pub preflight: ExecutionPreflightBoundary,
    pub blocking_reasons: Vec<String>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionIntentPreview {
    pub job_id: String,
    pub workspace_id: String,
    pub query: String,
    pub mode: ExecutionIntentMode,
    pub intent_id_preview: String,
    pub idempotency_key_preview: String,
    pub intent_creation_allowed: bool,
    pub execution_allowed: bool,
    pub handoff: ExecutionHandoffPreview,
    pub worker_lease_boundary: WorkerLeaseBoundary,
    pub blocking_reasons: Vec<String>,
    pub required_capabilities: Vec<String>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionIntentCreateRequestPreview {
    pub workspace_id: String,
    pub run_id: Option<String>,
    pub job_id: Option<String>,
    pub action: WorkspaceAction,
    pub mode: ExecutionIntentCreateRequestMode,
    pub status: ExecutionIntentCreateRequestStatus,
    pub create_request_allowed: bool,
    pub intent_persistence_allowed: bool,
    pub execution_allowed: bool,
    pub durable_intent_id_issued: bool,
    pub intent_id_preview: Option<String>,
    pub idempotency_key_preview: String,
    pub admission_token_required: bool,
    pub vault_handle_required: bool,
    pub quota_reservation_required: bool,
    pub request_fields: Vec<ExecutionIntentCreateRequestField>,
    pub write_plan: Vec<ExecutionIntentCreateRequestWriteStep>,
    pub admission: ExecutionAdmissionDecision,
    pub intent_store: ExecutionIntentStoreBoundary,
    pub worker_lease_boundary: WorkerLeaseBoundary,
    pub blocking_reasons: Vec<String>,
    pub required_capabilities: Vec<String>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionIntentDurabilityGate {
    pub workspace_id: String,
    pub run_id: Option<String>,
    pub job_id: Option<String>,
    pub action: WorkspaceAction,
    pub mode: ExecutionIntentDurabilityGateMode,
    pub status: ExecutionIntentDurabilityGateStatus,
    pub durability_allowed: bool,
    pub hosted_store_connection_allowed: bool,
    pub execution_allowed: bool,
    pub create_request: ExecutionIntentCreateRequestPreview,
    pub result_commit_boundary: ResultCommitBoundary,
    pub prerequisites: Vec<ExecutionIntentDurabilityPrerequisite>,
    pub blocking_reasons: Vec<String>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentDurabilityPrerequisite {
    pub id: &'static str,
    pub label: &'static str,
    pub status: ExecutionIntentDurabilityPrerequisiteStatus,
    pub satisfied: bool,
    pub blocks_durability: bool,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentCreateRequestField {
    pub id: &'static str,
    pub source: &'static str,
    pub accepted_now: bool,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentCreateRequestWriteStep {
    pub id: &'static str,
    pub target: &'static str,
    pub allowed_now: bool,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentStoreBoundary {
    pub mode: ExecutionIntentStoreMode,
    pub intent_store_connected: bool,
    pub persistence_allowed: bool,
    pub replay_required_before_claim: bool,
    pub transition_rules: Vec<ExecutionIntentTransitionRule>,
    pub idempotency_rules: Vec<ExecutionIntentStoreIdempotencyRule>,
    pub retention_rules: Vec<ExecutionIntentStoreRetentionRule>,
    pub safeguards: Vec<String>,
    pub next_required_step: String,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentTransitionRule {
    pub id: &'static str,
    pub from_status: &'static str,
    pub to_status: &'static str,
    pub allowed_now: bool,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentStoreIdempotencyRule {
    pub id: &'static str,
    pub key_scope: &'static str,
    pub requirement: &'static str,
    pub status: ExecutionIntentStoreRuleStatus,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionIntentStoreRetentionRule {
    pub id: &'static str,
    pub store: &'static str,
    pub requirement: &'static str,
    pub status: ExecutionIntentStoreRuleStatus,
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionLifecycleSpec {
    pub mode: ExecutionLifecycleMode,
    pub execution_allowed: bool,
    pub stages: Vec<ExecutionLifecycleStage>,
    pub failure_states: Vec<ExecutionFailureState>,
    pub transition_guards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkerLeaseBoundary {
    pub mode: WorkerLeaseMode,
    pub lease_store_connected: bool,
    pub retry_scheduler_enabled: bool,
    pub execution_allowed: bool,
    pub lease_rules: Vec<WorkerLeaseRule>,
    pub retry_rules: Vec<RetrySchedulerRule>,
    pub idempotency_rules: Vec<WorkerIdempotencyRule>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkerLeaseRule {
    pub id: &'static str,
    pub actor: &'static str,
    pub status: WorkerLeaseRuleStatus,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct RetrySchedulerRule {
    pub id: &'static str,
    pub failure_state: &'static str,
    pub retry_policy: &'static str,
    pub max_attempts: u8,
    pub preserves_partial_results: bool,
    pub status: RetrySchedulerStatus,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkerIdempotencyRule {
    pub id: &'static str,
    pub key_scope: &'static str,
    pub requirement: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionLifecycleStage {
    pub id: &'static str,
    pub label: &'static str,
    pub phase: &'static str,
    pub purpose: &'static str,
    pub enters_when: &'static str,
    pub exits_when: &'static str,
    pub visible_to_user: bool,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct ExecutionFailureState {
    pub id: &'static str,
    pub label: &'static str,
    pub retry_policy: &'static str,
    pub user_message: &'static str,
    pub terminal: bool,
    pub preserves_partial_results: bool,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionJobStatus {
    PreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionWorkOrderMode {
    PreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionHandoffMode {
    PreviewOnlyDenied,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentMode {
    PreviewOnlyRejected,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentCreateRequestMode {
    PreviewOnlyRejected,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentCreateRequestStatus {
    RejectedRequiresAdmissionAndStore,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentDurabilityGateMode {
    PreviewOnlyRejected,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentDurabilityGateStatus {
    RejectedMissingHostedDurability,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentDurabilityPrerequisiteStatus {
    SatisfiedPreviewOnly,
    MissingHostedGate,
    NotConnected,
    Disabled,
    FutureRequired,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentStoreMode {
    PlannedNoPersistence,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionIntentStoreRuleStatus {
    FutureRequired,
    NotConnected,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionLifecycleMode {
    HostedWorkerPlanned,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerLeaseMode {
    PlannedNoWorkers,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerLeaseRuleStatus {
    FutureRequired,
    NotConnected,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RetrySchedulerStatus {
    FutureRequired,
    PreviewOnly,
}

#[derive(Debug)]
pub enum ExecutionQueueError {
    RoutingPreview(RoutingPreviewError),
    LockPoisoned,
}

pub fn execution_lifecycle_spec() -> ExecutionLifecycleSpec {
    ExecutionLifecycleSpec {
        mode: ExecutionLifecycleMode::HostedWorkerPlanned,
        execution_allowed: false,
        stages: vec![
            ExecutionLifecycleStage {
                id: "accepted",
                label: "Accepted",
                phase: "intake",
                purpose: "Persist the requested run and assign a durable job id.",
                enters_when: "A user or schedule submits a run request.",
                exits_when: "The request validates and can be routed.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "routed",
                label: "Routed",
                phase: "routing",
                purpose: "Choose provider/source lanes from quota, policy, and source availability.",
                enters_when: "A valid job has workspace, scenario, and source policy context.",
                exits_when: "At least one lane is selected or a no-runnable-lane failure is recorded.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "waiting_for_quota",
                label: "Waiting for quota",
                phase: "queueing",
                purpose: "Hold the job until managed, workspace, or user-owned quota is available.",
                enters_when: "A selected lane is cooling down or rate-limited.",
                exits_when: "Cooldown expires, an alternate lane is selected, or the job is cancelled.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "waiting_for_worker",
                label: "Waiting for worker",
                phase: "queueing",
                purpose: "Make the work order claimable by a hosted worker without exposing secrets to routes.",
                enters_when: "Routing is complete and execution is allowed by policy.",
                exits_when: "A worker claims the job and records a lease.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "executing_provider_calls",
                label: "Executing provider calls",
                phase: "execution",
                purpose: "Call model/search providers through adapter-owned credentials and budgets.",
                enters_when: "A worker holds a valid lease and provider lane.",
                exits_when: "Provider calls return, timeout, or fail with a classified provider state.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "normalizing_evidence",
                label: "Normalizing evidence",
                phase: "assembly",
                purpose: "Deduplicate source results, preserve citations, and classify degraded source states.",
                enters_when: "Provider/search adapters return raw evidence candidates.",
                exits_when: "Evidence anchors are ready for graph synthesis or partial-result reporting.",
                visible_to_user: false,
            },
            ExecutionLifecycleStage {
                id: "synthesizing_graph",
                label: "Synthesizing graph",
                phase: "assembly",
                purpose: "Build causal nodes, edges, challenge checks, uncertainty, and reviewable brief output.",
                enters_when: "Evidence candidates are normalized and anchored.",
                exits_when: "A graph payload and report payload are ready for review.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "awaiting_review",
                label: "Awaiting review",
                phase: "review",
                purpose: "Expose the result, gaps, degraded sources, and challenge checks before trust.",
                enters_when: "A synthesized graph is stored.",
                exits_when: "The user marks the run reviewed, exports it, or starts a follow-up run.",
                visible_to_user: true,
            },
            ExecutionLifecycleStage {
                id: "completed",
                label: "Completed",
                phase: "terminal",
                purpose: "Mark the run as done while keeping evidence, usage, and audit metadata inspectable.",
                enters_when: "A reviewable result is available and no retry is pending.",
                exits_when: "Terminal state; later changes create a new run or revision.",
                visible_to_user: true,
            },
        ],
        failure_states: vec![
            ExecutionFailureState {
                id: "validation_rejected",
                label: "Validation rejected",
                retry_policy: "fix_input",
                user_message: "The request is missing required fields or violates workspace policy.",
                terminal: true,
                preserves_partial_results: false,
            },
            ExecutionFailureState {
                id: "no_runnable_lane",
                label: "No runnable lane",
                retry_policy: "change_source_policy_or_add_evidence",
                user_message: "No provider, search, or uploaded-evidence lane can run under the current policy.",
                terminal: true,
                preserves_partial_results: false,
            },
            ExecutionFailureState {
                id: "quota_limited",
                label: "Quota limited",
                retry_policy: "retry_after_cooldown",
                user_message: "The selected lane is cooling down or out of workspace quota.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "credential_unavailable",
                label: "Credential unavailable",
                retry_policy: "configure_workspace_or_user_key",
                user_message: "The selected lane needs credentials that are not available to the worker.",
                terminal: true,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "provider_rate_limited",
                label: "Provider rate limited",
                retry_policy: "retry_with_backoff_or_alt_lane",
                user_message: "The provider rejected the call because the lane exceeded its rate limit.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "provider_timeout",
                label: "Provider timeout",
                retry_policy: "retry_with_backoff",
                user_message: "The provider did not respond before the worker timeout.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "provider_error",
                label: "Provider error",
                retry_policy: "retry_or_failover",
                user_message: "The provider returned an error that must be classified before retry.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "partial_results_only",
                label: "Partial results only",
                retry_policy: "allow_review_or_continue",
                user_message: "Enough evidence exists to inspect, but at least one selected lane degraded.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "worker_interrupted",
                label: "Worker interrupted",
                retry_policy: "requeue_after_lease_expiry",
                user_message: "A worker lost its lease before completing the job.",
                terminal: false,
                preserves_partial_results: true,
            },
            ExecutionFailureState {
                id: "cancelled",
                label: "Cancelled",
                retry_policy: "start_new_run",
                user_message: "The run was cancelled before completion.",
                terminal: true,
                preserves_partial_results: true,
            },
        ],
        transition_guards: vec![
            "worker_requires_tenant_auth".to_string(),
            "worker_reads_credentials_from_vault_only".to_string(),
            "provider_execution_requires_billable_quota".to_string(),
            "partial_results_preserve_source_status".to_string(),
            "routes_never_receive_raw_provider_secrets".to_string(),
        ],
    }
}

pub fn worker_lease_boundary() -> WorkerLeaseBoundary {
    WorkerLeaseBoundary {
        mode: WorkerLeaseMode::PlannedNoWorkers,
        lease_store_connected: false,
        retry_scheduler_enabled: false,
        execution_allowed: false,
        lease_rules: vec![
            WorkerLeaseRule {
                id: "claim_requires_durable_job",
                actor: "worker_pool_later",
                status: WorkerLeaseRuleStatus::FutureRequired,
                requirement: "A worker may claim only a durable queued job with tenant, quota, and route context.",
            },
            WorkerLeaseRule {
                id: "lease_requires_auth_and_vault_scope",
                actor: "worker_pool_later",
                status: WorkerLeaseRuleStatus::FutureRequired,
                requirement: "The worker lease must be tenant-scoped and may receive vault handles, never raw secrets.",
            },
            WorkerLeaseRule {
                id: "routes_cannot_claim_work",
                actor: "api_routes",
                status: WorkerLeaseRuleStatus::NotConnected,
                requirement: "API routes can expose preview work orders but must not claim leases or execute jobs.",
            },
        ],
        retry_rules: vec![
            RetrySchedulerRule {
                id: "provider_rate_limited_retry",
                failure_state: "provider_rate_limited",
                retry_policy: "retry_after_or_failover_lane",
                max_attempts: 3,
                preserves_partial_results: true,
                status: RetrySchedulerStatus::FutureRequired,
            },
            RetrySchedulerRule {
                id: "provider_timeout_retry",
                failure_state: "provider_timeout",
                retry_policy: "bounded_exponential_backoff",
                max_attempts: 2,
                preserves_partial_results: true,
                status: RetrySchedulerStatus::FutureRequired,
            },
            RetrySchedulerRule {
                id: "worker_interrupted_requeue",
                failure_state: "worker_interrupted",
                retry_policy: "requeue_after_lease_expiry",
                max_attempts: 1,
                preserves_partial_results: true,
                status: RetrySchedulerStatus::PreviewOnly,
            },
        ],
        idempotency_rules: vec![
            WorkerIdempotencyRule {
                id: "job_claim_key",
                key_scope: "workspace_id:job_id:lease_generation",
                requirement: "Duplicate claims must not execute the same provider call twice.",
            },
            WorkerIdempotencyRule {
                id: "provider_call_key",
                key_scope: "workspace_id:job_id:provider_lane_id:attempt",
                requirement: "Retries must reuse attempt keys so partial evidence and usage rows can be reconciled.",
            },
            WorkerIdempotencyRule {
                id: "result_commit_key",
                key_scope: "workspace_id:run_id:graph_revision",
                requirement: "Final graph writes must be compare-and-swap style, not route-owned mutation.",
            },
        ],
        safeguards: vec![
            "no_worker_process_started".to_string(),
            "no_lease_store_connection_in_this_slice".to_string(),
            "no_retry_scheduler_enabled".to_string(),
            "no_provider_execution_or_secret_access".to_string(),
            "no_quota_or_billing_mutation".to_string(),
        ],
    }
}

pub fn execution_intent_store_boundary() -> ExecutionIntentStoreBoundary {
    ExecutionIntentStoreBoundary {
        mode: ExecutionIntentStoreMode::PlannedNoPersistence,
        intent_store_connected: false,
        persistence_allowed: false,
        replay_required_before_claim: true,
        transition_rules: vec![
            ExecutionIntentTransitionRule {
                id: "accepted_to_ready_for_lease",
                from_status: "accepted",
                to_status: "ready_for_lease",
                allowed_now: false,
                requirement: "Persist a tenant-scoped intent row only after auth, vault handle, quota reservation, and route plan checks pass.",
            },
            ExecutionIntentTransitionRule {
                id: "ready_for_lease_to_claimed",
                from_status: "ready_for_lease",
                to_status: "claimed",
                allowed_now: false,
                requirement: "A worker may claim only through a durable lease-store compare-and-swap operation.",
            },
            ExecutionIntentTransitionRule {
                id: "claimed_to_retry_wait",
                from_status: "claimed",
                to_status: "retry_wait",
                allowed_now: false,
                requirement: "Retries require scheduler-owned attempt keys that preserve partial evidence and degraded-source state.",
            },
            ExecutionIntentTransitionRule {
                id: "claimed_to_committing",
                from_status: "claimed",
                to_status: "committing",
                allowed_now: false,
                requirement: "Provider output must be attached to the intent through worker-owned result metadata, never API-route mutation.",
            },
            ExecutionIntentTransitionRule {
                id: "committing_to_completed",
                from_status: "committing",
                to_status: "completed",
                allowed_now: false,
                requirement: "Final completion requires idempotent result-event append, snapshot reconciliation, and quota ledger reconciliation.",
            },
        ],
        idempotency_rules: vec![
            ExecutionIntentStoreIdempotencyRule {
                id: "intent_create_key",
                key_scope: "workspace_id:job_id:route_plan_revision",
                requirement: "Duplicate create requests must return the same intent envelope without starting provider execution.",
                status: ExecutionIntentStoreRuleStatus::FutureRequired,
            },
            ExecutionIntentStoreIdempotencyRule {
                id: "lease_claim_key",
                key_scope: "workspace_id:intent_id:lease_generation",
                requirement: "Duplicate worker claims must not run the same provider lane twice.",
                status: ExecutionIntentStoreRuleStatus::NotConnected,
            },
            ExecutionIntentStoreIdempotencyRule {
                id: "provider_attempt_key",
                key_scope: "workspace_id:intent_id:provider_lane_id:attempt",
                requirement: "Retries must reconcile partial evidence, degraded-source status, and usage ledger rows under one attempt key.",
                status: ExecutionIntentStoreRuleStatus::FutureRequired,
            },
            ExecutionIntentStoreIdempotencyRule {
                id: "result_commit_key",
                key_scope: "workspace_id:intent_id:run_id:graph_revision",
                requirement: "Result commits must be idempotent and compare-and-swap guarded before graph snapshots are published.",
                status: ExecutionIntentStoreRuleStatus::FutureRequired,
            },
        ],
        retention_rules: vec![
            ExecutionIntentStoreRetentionRule {
                id: "intent_rows",
                store: "postgres_execution_intents_later",
                requirement: "Retain status, blockers, route summary, actor, and timestamps without raw provider secrets.",
                status: ExecutionIntentStoreRuleStatus::FutureRequired,
            },
            ExecutionIntentStoreRetentionRule {
                id: "lease_rows",
                store: "redis_or_postgres_leases_later",
                requirement: "Retain lease generation, worker id, expiry, and retry visibility without credential values.",
                status: ExecutionIntentStoreRuleStatus::NotConnected,
            },
            ExecutionIntentStoreRetentionRule {
                id: "result_event_links",
                store: "event_store_later",
                requirement: "Retain event ids linking partial and final result commits for replay and review comparison.",
                status: ExecutionIntentStoreRuleStatus::FutureRequired,
            },
        ],
        safeguards: vec![
            "no_intent_store_connection_in_this_slice".to_string(),
            "no_intent_persistence".to_string(),
            "no_worker_lease_claimed".to_string(),
            "no_retry_scheduler_started".to_string(),
            "no_provider_execution_or_secret_access".to_string(),
            "no_quota_or_billing_mutation".to_string(),
            "api_routes_do_not_write_execution_intents".to_string(),
        ],
        next_required_step: "Connect a tenant-scoped hosted intent store only after auth, vault handles, quota reservations, worker leases, retry scheduling, and idempotent result commits exist."
            .to_string(),
    }
}

pub fn execution_intent_create_request_preview(
    request: ExecutionAdmissionRequest,
) -> ExecutionIntentCreateRequestPreview {
    let admission = execution_admission(request);
    let intent_store = execution_intent_store_boundary();
    let worker_lease_boundary = worker_lease_boundary();

    let mut blocking_reasons = admission.blocking_reasons.clone();
    if !admission.admitted {
        push_unique_string(&mut blocking_reasons, "execution_admission_denied");
    }
    if !admission.admission_token_issued {
        push_unique_string(
            &mut blocking_reasons,
            "admission_token_required_before_intent_create",
        );
    }
    if !admission.vault_handle_issued {
        push_unique_string(
            &mut blocking_reasons,
            "vault_handle_required_before_intent_create",
        );
    }
    if !admission.quota_reserved {
        push_unique_string(
            &mut blocking_reasons,
            "quota_reservation_required_before_intent_create",
        );
    }
    if !intent_store.intent_store_connected {
        push_unique_string(&mut blocking_reasons, "intent_store_not_connected");
    }
    if !intent_store.persistence_allowed {
        push_unique_string(&mut blocking_reasons, "intent_persistence_disabled");
    }
    if !worker_lease_boundary.lease_store_connected {
        push_unique_string(&mut blocking_reasons, "worker_lease_store_not_connected");
    }
    if !worker_lease_boundary.execution_allowed {
        push_unique_string(&mut blocking_reasons, "worker_execution_disabled");
    }

    let mut safeguards = admission.safeguards.clone();
    push_unique_string(
        &mut safeguards,
        "create_request_preview_only_no_persistence",
    );
    push_unique_string(&mut safeguards, "no_durable_intent_id_issued");
    push_unique_string(
        &mut safeguards,
        "no_admission_token_or_vault_handle_returned",
    );
    safeguards.extend(intent_store.safeguards.clone());
    safeguards.extend(worker_lease_boundary.safeguards.clone());

    let mut required_capabilities = Vec::new();
    for gate in &admission.gates {
        push_unique_string(
            &mut required_capabilities,
            format!("{}: {}", gate.id, gate.requirement),
        );
    }
    for rule in &intent_store.idempotency_rules {
        push_unique_string(
            &mut required_capabilities,
            format!("{}: {}", rule.id, rule.requirement),
        );
    }
    for rule in &worker_lease_boundary.lease_rules {
        push_unique_string(
            &mut required_capabilities,
            format!("{}: {}", rule.id, rule.requirement),
        );
    }

    let idempotency_key_preview = intent_create_idempotency_key(&admission);

    ExecutionIntentCreateRequestPreview {
        workspace_id: admission.workspace_id.clone(),
        run_id: admission.run_id.clone(),
        job_id: admission.job_id.clone(),
        action: admission.action,
        mode: ExecutionIntentCreateRequestMode::PreviewOnlyRejected,
        status: ExecutionIntentCreateRequestStatus::RejectedRequiresAdmissionAndStore,
        create_request_allowed: false,
        intent_persistence_allowed: false,
        execution_allowed: false,
        durable_intent_id_issued: false,
        intent_id_preview: None,
        idempotency_key_preview,
        admission_token_required: true,
        vault_handle_required: true,
        quota_reservation_required: true,
        request_fields: execution_intent_create_request_fields(),
        write_plan: execution_intent_create_request_write_plan(),
        admission,
        intent_store,
        worker_lease_boundary,
        blocking_reasons,
        required_capabilities,
        safeguards,
        next_required_step: "Only create a durable hosted execution intent after tenant auth admits the action, a worker-scoped vault handle exists, quota is reserved, the intent store is connected, worker leases exist, and result commits are idempotent."
            .to_string(),
    }
}

pub fn execution_intent_durability_gate(
    request: ExecutionAdmissionRequest,
) -> ExecutionIntentDurabilityGate {
    let create_request = execution_intent_create_request_preview(request);
    let result_commit_boundary = result_commit_boundary();
    let prerequisites =
        execution_intent_durability_prerequisites(&create_request, &result_commit_boundary);

    let mut blocking_reasons = create_request.blocking_reasons.clone();
    for prerequisite in &prerequisites {
        if prerequisite.blocks_durability && !prerequisite.satisfied {
            push_unique_string(
                &mut blocking_reasons,
                format!("durability_gate_missing_{}", prerequisite.id),
            );
        }
    }
    if !result_commit_boundary.event_store_connected {
        push_unique_string(
            &mut blocking_reasons,
            "result_commit_event_store_not_connected",
        );
    }
    if !result_commit_boundary.commit_writes_enabled {
        push_unique_string(&mut blocking_reasons, "result_commit_writes_disabled");
    }

    let mut safeguards = create_request.safeguards.clone();
    safeguards.extend(result_commit_boundary.safeguards.clone());
    push_unique_string(
        &mut safeguards,
        "durability_gate_preview_only_no_store_connection",
    );
    push_unique_string(&mut safeguards, "no_intent_store_connection_attempted");
    push_unique_string(&mut safeguards, "no_result_commit_attempted");

    ExecutionIntentDurabilityGate {
        workspace_id: create_request.workspace_id.clone(),
        run_id: create_request.run_id.clone(),
        job_id: create_request.job_id.clone(),
        action: create_request.action,
        mode: ExecutionIntentDurabilityGateMode::PreviewOnlyRejected,
        status: ExecutionIntentDurabilityGateStatus::RejectedMissingHostedDurability,
        durability_allowed: false,
        hosted_store_connection_allowed: false,
        execution_allowed: false,
        create_request,
        result_commit_boundary,
        prerequisites,
        blocking_reasons,
        safeguards,
        next_required_step: "Connect real hosted tenant auth, admission tokens, vault handles, quota reservations, durable intent/idempotency stores, worker leases, retry scheduling, replay checks, and worker-owned result commits before replacing this rejected gate with durable intent creation."
            .to_string(),
    }
}

fn execution_intent_durability_prerequisites(
    create_request: &ExecutionIntentCreateRequestPreview,
    result_commit_boundary: &ResultCommitBoundary,
) -> Vec<ExecutionIntentDurabilityPrerequisite> {
    vec![
        ExecutionIntentDurabilityPrerequisite {
            id: "tenant_auth_admitted",
            label: "Tenant auth admitted",
            status: if create_request.admission.admitted {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::MissingHostedGate
            },
            satisfied: create_request.admission.admitted,
            blocks_durability: true,
            requirement: "A hosted workspace/actor context must admit the requested action before any durable intent row is accepted.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "admission_token_issued",
            label: "Admission token issued",
            status: if create_request.admission.admission_token_issued {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::MissingHostedGate
            },
            satisfied: create_request.admission.admission_token_issued,
            blocks_durability: true,
            requirement: "The server must issue a scoped admission capability; routes must not synthesize one locally.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "vault_handle_issued",
            label: "Vault handle issued",
            status: if create_request.admission.vault_handle_issued {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::MissingHostedGate
            },
            satisfied: create_request.admission.vault_handle_issued,
            blocks_durability: true,
            requirement: "Workers may receive vault handles only; raw credentials must never enter the intent payload.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "quota_reserved",
            label: "Quota reserved",
            status: if create_request.admission.quota_reserved {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::MissingHostedGate
            },
            satisfied: create_request.admission.quota_reserved,
            blocks_durability: true,
            requirement: "A billable quota reservation must exist before provider work can be queued.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "idempotency_preview_scoped",
            label: "Idempotency preview scoped",
            status: ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly,
            satisfied: !create_request.idempotency_key_preview.trim().is_empty(),
            blocks_durability: false,
            requirement: "The preview payload must expose the future workspace/resource/action idempotency scope without creating a durable key row.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "idempotency_index_connected",
            label: "Idempotency index connected",
            status: ExecutionIntentDurabilityPrerequisiteStatus::NotConnected,
            satisfied: false,
            blocks_durability: true,
            requirement: "A hosted uniqueness index must reject duplicate create requests before durable intent creation is enabled.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "intent_store_connected",
            label: "Intent store connected",
            status: if create_request.intent_store.intent_store_connected {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::NotConnected
            },
            satisfied: create_request.intent_store.intent_store_connected,
            blocks_durability: true,
            requirement: "A hosted durable intent store must be connected before routes can persist execution intents.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "intent_persistence_enabled",
            label: "Intent persistence enabled",
            status: if create_request.intent_persistence_allowed {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::Disabled
            },
            satisfied: create_request.intent_persistence_allowed,
            blocks_durability: true,
            requirement: "Intent writes remain disabled until hosted store, auth, vault, quota, and idempotency gates pass together.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "replay_before_claim_defined",
            label: "Replay before claim defined",
            status: ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly,
            satisfied: create_request.intent_store.replay_required_before_claim,
            blocks_durability: false,
            requirement: "Replay-before-claim semantics must stay explicit so workers rebuild intent state before claiming work.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "lease_store_connected",
            label: "Lease store connected",
            status: if create_request.worker_lease_boundary.lease_store_connected {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::NotConnected
            },
            satisfied: create_request.worker_lease_boundary.lease_store_connected,
            blocks_durability: true,
            requirement: "Workers must claim through a durable lease store, not API-route memory.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "retry_scheduler_enabled",
            label: "Retry scheduler enabled",
            status: if create_request.worker_lease_boundary.retry_scheduler_enabled {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::FutureRequired
            },
            satisfied: create_request.worker_lease_boundary.retry_scheduler_enabled,
            blocks_durability: true,
            requirement: "Retry scheduling must preserve partial results and degraded source states before live work is queued.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "result_event_store_connected",
            label: "Result event store connected",
            status: if result_commit_boundary.event_store_connected {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::NotConnected
            },
            satisfied: result_commit_boundary.event_store_connected,
            blocks_durability: true,
            requirement: "Worker result events must have a durable commit store before provider output can leave preview mode.",
        },
        ExecutionIntentDurabilityPrerequisite {
            id: "result_commit_writes_enabled",
            label: "Result commit writes enabled",
            status: if result_commit_boundary.commit_writes_enabled {
                ExecutionIntentDurabilityPrerequisiteStatus::SatisfiedPreviewOnly
            } else {
                ExecutionIntentDurabilityPrerequisiteStatus::Disabled
            },
            satisfied: result_commit_boundary.commit_writes_enabled,
            blocks_durability: true,
            requirement: "Result writes must be worker-owned and idempotent before durable intent execution is allowed.",
        },
    ]
}

fn execution_intent_create_request_fields() -> Vec<ExecutionIntentCreateRequestField> {
    vec![
        ExecutionIntentCreateRequestField {
            id: "workspace_id",
            source: "admission_request",
            accepted_now: true,
            requirement: "Tenant-scoped workspace id carried into the future durable intent create request.",
        },
        ExecutionIntentCreateRequestField {
            id: "run_or_job_id",
            source: "admission_request",
            accepted_now: true,
            requirement: "A local run id or queued job id identifies the graph workspace input, but does not authorize execution.",
        },
        ExecutionIntentCreateRequestField {
            id: "action",
            source: "admission_request",
            accepted_now: true,
            requirement: "The requested action is evaluated server-side before any future create request can persist.",
        },
        ExecutionIntentCreateRequestField {
            id: "admission_token",
            source: "future_auth_service",
            accepted_now: false,
            requirement: "A real admission token must be issued by hosted auth before durable intent creation.",
        },
        ExecutionIntentCreateRequestField {
            id: "vault_handle",
            source: "future_credential_vault",
            accepted_now: false,
            requirement: "A worker-scoped vault handle is required; raw provider secrets must never be accepted here.",
        },
        ExecutionIntentCreateRequestField {
            id: "quota_reservation",
            source: "future_quota_ledger",
            accepted_now: false,
            requirement: "A tenant-scoped quota reservation is required before provider execution can be queued.",
        },
        ExecutionIntentCreateRequestField {
            id: "route_plan_revision",
            source: "future_durable_route_plan",
            accepted_now: false,
            requirement: "Durable intent creation must bind to an immutable route-plan revision.",
        },
        ExecutionIntentCreateRequestField {
            id: "idempotency_key",
            source: "server_generated_preview",
            accepted_now: false,
            requirement: "The preview key documents the future duplicate-create contract but is not a persistence key yet.",
        },
    ]
}

fn execution_intent_create_request_write_plan() -> Vec<ExecutionIntentCreateRequestWriteStep> {
    vec![
        ExecutionIntentCreateRequestWriteStep {
            id: "validate_admission",
            target: "hosted_auth_and_policy",
            allowed_now: false,
            requirement: "Admission must be allowed by tenant auth, vault handle, quota reservation, and preflight gates.",
        },
        ExecutionIntentCreateRequestWriteStep {
            id: "insert_execution_intent",
            target: "future_postgres_execution_intents",
            allowed_now: false,
            requirement: "Insert a durable intent row only after the hosted intent store exists and idempotency is enforced.",
        },
        ExecutionIntentCreateRequestWriteStep {
            id: "mark_ready_for_lease",
            target: "future_worker_lease_store",
            allowed_now: false,
            requirement: "Expose the intent to workers only after replay-before-claim and lease compare-and-swap rules exist.",
        },
        ExecutionIntentCreateRequestWriteStep {
            id: "record_quota_reservation_link",
            target: "future_quota_ledger",
            allowed_now: false,
            requirement: "Link a real reservation without mutating billing or usage from the API route.",
        },
    ]
}

fn intent_create_idempotency_key(admission: &ExecutionAdmissionDecision) -> String {
    let resource_id = admission
        .job_id
        .as_deref()
        .or(admission.run_id.as_deref())
        .unwrap_or("future_provider_call");
    let action = format!("{:?}", admission.action).to_ascii_lowercase();
    format!(
        "{}:{resource_id}:{action}:hosted_intent_create_preview:v1",
        admission.workspace_id
    )
}

fn push_unique_string(values: &mut Vec<String>, value: impl Into<String>) {
    let value = value.into();
    if !values.iter().any(|existing| existing == &value) {
        values.push(value);
    }
}

impl ExecutionQueue {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn enqueue_preview(
        &self,
        request: RoutingPreviewRequest,
    ) -> Result<ExecutionJob, ExecutionQueueError> {
        let route_plan =
            build_routing_preview(request).map_err(ExecutionQueueError::RoutingPreview)?;
        let mut state = self
            .state
            .write()
            .map_err(|_| ExecutionQueueError::LockPoisoned)?;
        let sequence = state.next_sequence;
        state.next_sequence += 1;

        let now = unix_epoch_seconds();
        let job = ExecutionJob {
            id: format!("job_local_{sequence:06}"),
            workspace_id: route_plan.workspace_id.clone(),
            query: route_plan.query.clone(),
            status: ExecutionJobStatus::PreviewOnly,
            execution_allowed: route_plan.execution_allowed,
            selected_lane_id: route_plan.selected_lane_id.clone(),
            route_plan,
            created_at_epoch_seconds: now,
            updated_at_epoch_seconds: now,
            note: "Preview-only queue job; provider execution is intentionally disabled in this slice."
                .to_string(),
        };

        state.jobs.push(job.clone());
        Ok(job)
    }

    pub fn list_summaries(&self) -> Vec<ExecutionJobSummary> {
        let state = self
            .state
            .read()
            .expect("execution queue lock should be readable");
        state.jobs.iter().rev().map(ExecutionJob::summary).collect()
    }

    pub fn get_job(&self, job_id: &str) -> Option<ExecutionJob> {
        self.state
            .read()
            .expect("execution queue lock should be readable")
            .jobs
            .iter()
            .find(|job| job.id == job_id)
            .cloned()
    }

    pub fn get_work_order(&self, job_id: &str) -> Option<ExecutionWorkOrder> {
        self.get_job(job_id).map(|job| job.work_order())
    }

    pub fn get_handoff_preview(&self, job_id: &str) -> Option<ExecutionHandoffPreview> {
        self.get_job(job_id).map(|job| job.handoff_preview())
    }

    pub fn get_intent_preview(&self, job_id: &str) -> Option<ExecutionIntentPreview> {
        self.get_job(job_id).map(|job| job.intent_preview())
    }
}

impl ExecutionJob {
    pub fn summary(&self) -> ExecutionJobSummary {
        ExecutionJobSummary {
            id: self.id.clone(),
            workspace_id: self.workspace_id.clone(),
            query: self.query.clone(),
            status: self.status,
            execution_allowed: self.execution_allowed,
            selected_lane_id: self.selected_lane_id.clone(),
            created_at_epoch_seconds: self.created_at_epoch_seconds,
            updated_at_epoch_seconds: self.updated_at_epoch_seconds,
        }
    }

    pub fn work_order(&self) -> ExecutionWorkOrder {
        ExecutionWorkOrder {
            job_id: self.id.clone(),
            workspace_id: self.workspace_id.clone(),
            query: self.query.clone(),
            mode: ExecutionWorkOrderMode::PreviewOnly,
            execution_allowed: false,
            selected_lane_id: self.selected_lane_id.clone(),
            route_steps: self.route_plan.steps.clone(),
            routing_warnings: self.route_plan.warnings.clone(),
            safeguards: vec![
                "provider_execution_disabled".to_string(),
                "credential_access_forbidden".to_string(),
                "billing_disabled".to_string(),
                "worker_not_started".to_string(),
            ],
        }
    }

    pub fn handoff_preview(&self) -> ExecutionHandoffPreview {
        let work_order = self.work_order();
        let preflight = execution_preflight_boundary();
        let mut blocking_reasons = preflight.blocking_reasons.clone();
        if !work_order.execution_allowed {
            blocking_reasons.push("work_order_execution_disabled".to_string());
        }
        let mut safeguards = work_order.safeguards.clone();
        safeguards.extend(preflight.safeguards.clone());
        safeguards.push("handoff_preview_only_no_execution".to_string());

        ExecutionHandoffPreview {
            job_id: self.id.clone(),
            workspace_id: self.workspace_id.clone(),
            query: self.query.clone(),
            mode: ExecutionHandoffMode::PreviewOnlyDenied,
            execution_allowed: work_order.execution_allowed && preflight.execution_allowed,
            work_order,
            preflight,
            blocking_reasons,
            safeguards,
            next_required_step: "Implement hosted auth, vault-handle issuance, quota reservation, worker lease, and idempotent result commit before live handoff."
                .to_string(),
        }
    }

    pub fn intent_preview(&self) -> ExecutionIntentPreview {
        let handoff = self.handoff_preview();
        let worker_lease_boundary = worker_lease_boundary();
        let mut blocking_reasons = handoff.blocking_reasons.clone();
        if !worker_lease_boundary.lease_store_connected {
            blocking_reasons.push("worker_lease_store_not_connected".to_string());
        }
        if !worker_lease_boundary.retry_scheduler_enabled {
            blocking_reasons.push("retry_scheduler_disabled".to_string());
        }
        if !worker_lease_boundary.execution_allowed {
            blocking_reasons.push("worker_lease_execution_disabled".to_string());
        }
        blocking_reasons.push("execution_intent_persistence_disabled".to_string());

        let mut safeguards = handoff.safeguards.clone();
        safeguards.extend(worker_lease_boundary.safeguards.clone());
        safeguards.push("intent_preview_only_no_persistence".to_string());

        let required_capabilities = worker_lease_boundary
            .lease_rules
            .iter()
            .map(|rule| format!("{}: {}", rule.id, rule.requirement))
            .collect();

        ExecutionIntentPreview {
            job_id: self.id.clone(),
            workspace_id: self.workspace_id.clone(),
            query: self.query.clone(),
            mode: ExecutionIntentMode::PreviewOnlyRejected,
            intent_id_preview: format!("intent_preview_{}", self.id),
            idempotency_key_preview: format!(
                "{}:{}:execution_intent_preview:v1",
                self.workspace_id, self.id
            ),
            intent_creation_allowed: false,
            execution_allowed: false,
            handoff,
            worker_lease_boundary,
            blocking_reasons,
            required_capabilities,
            safeguards,
            next_required_step: "Persist execution intents only after hosted auth, vault handles, quota reservations, worker leases, retry scheduling, and idempotent result commits exist."
                .to_string(),
        }
    }
}

fn unix_epoch_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

impl std::fmt::Display for ExecutionQueueError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::RoutingPreview(error) => write!(formatter, "{error}"),
            Self::LockPoisoned => write!(formatter, "execution_queue_lock_poisoned"),
        }
    }
}

impl std::error::Error for ExecutionQueueError {}

#[cfg(test)]
mod tests {
    use super::{
        ExecutionHandoffMode, ExecutionIntentCreateRequestMode, ExecutionIntentCreateRequestStatus,
        ExecutionIntentDurabilityGateMode, ExecutionIntentDurabilityGateStatus,
        ExecutionIntentMode, ExecutionIntentStoreMode, ExecutionIntentStoreRuleStatus,
        ExecutionJobStatus, ExecutionLifecycleMode, ExecutionQueue, ExecutionQueueError,
        ExecutionWorkOrderMode, WorkerLeaseMode, WorkerLeaseRuleStatus,
        execution_intent_create_request_preview, execution_intent_durability_gate,
        execution_intent_store_boundary, execution_lifecycle_spec, worker_lease_boundary,
    };
    use retrocause_pro_domain::{ExecutionAdmissionRequest, WorkspaceAction};
    use retrocause_pro_provider_routing::{RoutingPreviewRequest, RoutingScenario, SourcePolicy};

    #[test]
    fn enqueue_preview_creates_non_executing_job() {
        let queue = ExecutionQueue::new();
        let job = queue
            .enqueue_preview(RoutingPreviewRequest {
                workspace_id: Some("workspace_queue".to_string()),
                query: "Why did routing need a queue?".to_string(),
                scenario: Some(RoutingScenario::Postmortem),
                source_policy: Some(SourcePolicy::Balanced),
            })
            .expect("preview queue job should be created");

        assert_eq!(job.id.as_str(), "job_local_000000");
        assert_eq!(job.status, ExecutionJobStatus::PreviewOnly);
        assert!(!job.execution_allowed);
        assert_eq!(job.workspace_id.as_str(), "workspace_queue");
        assert_eq!(
            job.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );
        assert!(
            job.note
                .contains("provider execution is intentionally disabled")
        );
    }

    #[test]
    fn list_summaries_returns_newest_first() {
        let queue = ExecutionQueue::new();

        queue
            .enqueue_preview(request("First routing request"))
            .expect("first job should be created");
        let second = queue
            .enqueue_preview(request("Second routing request"))
            .expect("second job should be created");

        let summaries = queue.list_summaries();
        assert_eq!(summaries.len(), 2);
        assert_eq!(summaries[0].id, second.id);
        assert_eq!(summaries[0].status, ExecutionJobStatus::PreviewOnly);
    }

    #[test]
    fn get_job_returns_created_job() {
        let queue = ExecutionQueue::new();
        let created = queue
            .enqueue_preview(request("Find this queued preview"))
            .expect("job should be created");

        let loaded = queue
            .get_job(&created.id)
            .expect("created job should be readable");
        assert_eq!(loaded.query, "Find this queued preview");
    }

    #[test]
    fn work_order_keeps_execution_disabled_and_safeguarded() {
        let queue = ExecutionQueue::new();
        let created = queue
            .enqueue_preview(request("Preview the executor contract"))
            .expect("job should be created");

        let work_order = queue
            .get_work_order(&created.id)
            .expect("created job should expose work order");

        assert_eq!(work_order.job_id, created.id);
        assert_eq!(work_order.mode, ExecutionWorkOrderMode::PreviewOnly);
        assert!(!work_order.execution_allowed);
        assert!(!work_order.route_steps.is_empty());
        assert!(
            work_order
                .safeguards
                .contains(&"provider_execution_disabled".to_string())
        );
        assert!(
            work_order
                .safeguards
                .contains(&"credential_access_forbidden".to_string())
        );
    }

    #[test]
    fn handoff_preview_composes_work_order_and_preflight_blockers() {
        let queue = ExecutionQueue::new();
        let created = queue
            .enqueue_preview(request("Preview the handoff boundary"))
            .expect("job should be created");

        let preview = queue
            .get_handoff_preview(&created.id)
            .expect("created job should expose handoff preview");

        assert_eq!(preview.job_id, created.id);
        assert_eq!(preview.mode, ExecutionHandoffMode::PreviewOnlyDenied);
        assert!(!preview.execution_allowed);
        assert_eq!(preview.work_order.job_id, preview.job_id);
        assert!(!preview.work_order.execution_allowed);
        assert!(!preview.preflight.execution_allowed);
        assert!(
            preview
                .blocking_reasons
                .contains(&"quota_reservation_required".to_string())
        );
        assert!(
            preview
                .blocking_reasons
                .contains(&"work_order_execution_disabled".to_string())
        );
        assert!(
            preview
                .safeguards
                .contains(&"handoff_preview_only_no_execution".to_string())
        );

        let combined = format!(
            "{:?} {:?} {}",
            preview.blocking_reasons, preview.safeguards, preview.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
    }

    #[test]
    fn intent_preview_composes_handoff_and_worker_lease_blockers() {
        let queue = ExecutionQueue::new();
        let created = queue
            .enqueue_preview(request("Preview the execution intent"))
            .expect("job should be created");

        let preview = queue
            .get_intent_preview(&created.id)
            .expect("created job should expose intent preview");

        assert_eq!(preview.job_id, created.id);
        assert_eq!(preview.mode, ExecutionIntentMode::PreviewOnlyRejected);
        assert!(!preview.intent_creation_allowed);
        assert!(!preview.execution_allowed);
        assert_eq!(preview.handoff.job_id, preview.job_id);
        assert!(!preview.handoff.execution_allowed);
        assert!(!preview.worker_lease_boundary.execution_allowed);
        assert!(
            preview
                .blocking_reasons
                .contains(&"quota_reservation_required".to_string())
        );
        assert!(
            preview
                .blocking_reasons
                .contains(&"worker_lease_store_not_connected".to_string())
        );
        assert!(
            preview
                .blocking_reasons
                .contains(&"execution_intent_persistence_disabled".to_string())
        );
        assert!(
            preview
                .safeguards
                .contains(&"intent_preview_only_no_persistence".to_string())
        );
        assert!(preview.intent_id_preview.contains(&created.id));
        assert!(preview.idempotency_key_preview.contains(&created.id));
        assert!(
            preview
                .required_capabilities
                .iter()
                .any(|capability| capability.contains("claim_requires_durable_job"))
        );

        let combined = format!(
            "{:?} {:?} {} {}",
            preview.blocking_reasons,
            preview.safeguards,
            preview.idempotency_key_preview,
            preview.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
    }

    #[test]
    fn intent_store_boundary_keeps_persistence_disabled_and_names_rules() {
        let boundary = execution_intent_store_boundary();

        assert_eq!(
            boundary.mode,
            ExecutionIntentStoreMode::PlannedNoPersistence
        );
        assert!(!boundary.intent_store_connected);
        assert!(!boundary.persistence_allowed);
        assert!(boundary.replay_required_before_claim);
        assert!(boundary.transition_rules.iter().any(|rule| {
            rule.id == "ready_for_lease_to_claimed"
                && !rule.allowed_now
                && rule.to_status == "claimed"
        }));
        assert!(boundary.idempotency_rules.iter().any(|rule| {
            rule.id == "intent_create_key"
                && rule.status == ExecutionIntentStoreRuleStatus::FutureRequired
        }));
        assert!(boundary.retention_rules.iter().any(|rule| {
            rule.id == "lease_rows" && rule.status == ExecutionIntentStoreRuleStatus::NotConnected
        }));
        assert!(
            boundary
                .safeguards
                .contains(&"no_intent_persistence".to_string())
        );
        assert!(
            boundary
                .safeguards
                .contains(&"no_provider_execution_or_secret_access".to_string())
        );

        let combined = format!(
            "{:?} {:?} {:?} {}",
            boundary.transition_rules,
            boundary.idempotency_rules,
            boundary.safeguards,
            boundary.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
    }

    #[test]
    fn hosted_intent_create_request_preview_rejects_before_admission_and_persistence() {
        let preview = execution_intent_create_request_preview(ExecutionAdmissionRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            job_id: Some("job_local_000000".to_string()),
            action: Some(WorkspaceAction::ExecuteProviderCalls),
        });

        assert_eq!(preview.workspace_id, "workspace_demo");
        assert_eq!(
            preview.mode,
            ExecutionIntentCreateRequestMode::PreviewOnlyRejected
        );
        assert_eq!(
            preview.status,
            ExecutionIntentCreateRequestStatus::RejectedRequiresAdmissionAndStore
        );
        assert!(!preview.create_request_allowed);
        assert!(!preview.intent_persistence_allowed);
        assert!(!preview.execution_allowed);
        assert!(!preview.durable_intent_id_issued);
        assert!(preview.intent_id_preview.is_none());
        assert!(!preview.admission.admitted);
        assert!(!preview.admission.admission_token_issued);
        assert!(!preview.admission.vault_handle_issued);
        assert!(!preview.admission.quota_reserved);
        assert!(!preview.intent_store.intent_store_connected);
        assert!(!preview.intent_store.persistence_allowed);
        assert!(!preview.worker_lease_boundary.lease_store_connected);
        assert!(!preview.worker_lease_boundary.execution_allowed);
        assert!(preview.idempotency_key_preview.contains("workspace_demo"));
        assert!(preview.idempotency_key_preview.contains("job_local_000000"));
        assert!(
            preview
                .request_fields
                .iter()
                .any(|field| field.id == "vault_handle" && !field.accepted_now)
        );
        assert!(preview.write_plan.iter().all(|step| !step.allowed_now));
        assert!(
            preview
                .blocking_reasons
                .contains(&"execution_admission_denied".to_string())
        );
        assert!(
            preview
                .blocking_reasons
                .contains(&"intent_store_not_connected".to_string())
        );
        assert!(
            preview
                .blocking_reasons
                .contains(&"intent_persistence_disabled".to_string())
        );
        assert!(
            preview
                .safeguards
                .contains(&"create_request_preview_only_no_persistence".to_string())
        );
        assert!(
            preview
                .safeguards
                .contains(&"no_durable_intent_id_issued".to_string())
        );
        assert!(
            preview
                .required_capabilities
                .iter()
                .any(|capability| capability.contains("tenant_auth"))
        );

        let combined = format!(
            "{:?} {:?} {:?} {:?} {} {}",
            preview.request_fields,
            preview.write_plan,
            preview.blocking_reasons,
            preview.safeguards,
            preview.idempotency_key_preview,
            preview.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
        assert!(!combined.contains("token:"));
    }

    #[test]
    fn intent_durability_gate_composes_all_hosted_prerequisites_without_writes() {
        let gate = execution_intent_durability_gate(ExecutionAdmissionRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            job_id: Some("job_local_000000".to_string()),
            action: Some(WorkspaceAction::ExecuteProviderCalls),
        });

        assert_eq!(gate.workspace_id, "workspace_demo");
        assert_eq!(
            gate.mode,
            ExecutionIntentDurabilityGateMode::PreviewOnlyRejected
        );
        assert_eq!(
            gate.status,
            ExecutionIntentDurabilityGateStatus::RejectedMissingHostedDurability
        );
        assert!(!gate.durability_allowed);
        assert!(!gate.hosted_store_connection_allowed);
        assert!(!gate.execution_allowed);
        assert!(!gate.create_request.create_request_allowed);
        assert!(!gate.create_request.intent_persistence_allowed);
        assert!(!gate.result_commit_boundary.event_store_connected);
        assert!(!gate.result_commit_boundary.commit_writes_enabled);
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "idempotency_preview_scoped" && prerequisite.satisfied
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "tenant_auth_admitted"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "vault_handle_issued"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "quota_reserved"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "intent_store_connected"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "lease_store_connected"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(gate.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "result_event_store_connected"
                && !prerequisite.satisfied
                && prerequisite.blocks_durability
        }));
        assert!(
            gate.blocking_reasons
                .contains(&"durability_gate_missing_tenant_auth_admitted".to_string())
        );
        assert!(
            gate.blocking_reasons
                .contains(&"result_commit_event_store_not_connected".to_string())
        );
        assert!(
            gate.safeguards
                .contains(&"durability_gate_preview_only_no_store_connection".to_string())
        );
        assert!(
            gate.safeguards
                .contains(&"no_result_commit_attempted".to_string())
        );

        let combined = format!(
            "{:?} {:?} {:?} {} {}",
            gate.prerequisites,
            gate.blocking_reasons,
            gate.safeguards,
            gate.create_request.idempotency_key_preview,
            gate.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
        assert!(!combined.contains("token:"));
    }

    #[test]
    fn lifecycle_spec_keeps_hosted_worker_contract_non_executing() {
        let spec = execution_lifecycle_spec();

        assert_eq!(spec.mode, ExecutionLifecycleMode::HostedWorkerPlanned);
        assert!(!spec.execution_allowed);
        assert!(
            spec.stages
                .iter()
                .any(|stage| stage.id == "waiting_for_worker")
        );
        assert!(
            spec.failure_states
                .iter()
                .any(|failure| failure.id == "provider_rate_limited" && !failure.terminal)
        );
        assert!(
            spec.transition_guards
                .contains(&"routes_never_receive_raw_provider_secrets".to_string())
        );
    }

    #[test]
    fn worker_lease_boundary_keeps_workers_and_retries_disabled() {
        let boundary = worker_lease_boundary();

        assert_eq!(boundary.mode, WorkerLeaseMode::PlannedNoWorkers);
        assert!(!boundary.lease_store_connected);
        assert!(!boundary.retry_scheduler_enabled);
        assert!(!boundary.execution_allowed);
        assert!(boundary.lease_rules.iter().any(|rule| {
            rule.id == "routes_cannot_claim_work"
                && rule.status == WorkerLeaseRuleStatus::NotConnected
        }));
        assert!(boundary.retry_rules.iter().any(|rule| {
            rule.id == "provider_rate_limited_retry"
                && rule.max_attempts == 3
                && rule.preserves_partial_results
        }));
        assert!(
            boundary
                .idempotency_rules
                .iter()
                .any(|rule| rule.id == "provider_call_key")
        );
        assert!(
            boundary
                .safeguards
                .contains(&"no_worker_process_started".to_string())
        );
        assert!(
            boundary
                .safeguards
                .contains(&"no_provider_execution_or_secret_access".to_string())
        );
    }

    #[test]
    fn blank_query_is_rejected_before_queue_mutation() {
        let queue = ExecutionQueue::new();
        let error = queue
            .enqueue_preview(RoutingPreviewRequest {
                workspace_id: None,
                query: "   ".to_string(),
                scenario: None,
                source_policy: None,
            })
            .expect_err("blank query should fail");

        assert!(matches!(error, ExecutionQueueError::RoutingPreview(_)));
        assert!(queue.list_summaries().is_empty());
    }

    fn request(query: &str) -> RoutingPreviewRequest {
        RoutingPreviewRequest {
            workspace_id: Some("workspace_queue".to_string()),
            query: query.to_string(),
            scenario: None,
            source_policy: None,
        }
    }
}
