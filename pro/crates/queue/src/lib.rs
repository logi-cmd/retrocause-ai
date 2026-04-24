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
pub struct ExecutionLifecycleSpec {
    pub mode: ExecutionLifecycleMode,
    pub execution_allowed: bool,
    pub stages: Vec<ExecutionLifecycleStage>,
    pub failure_states: Vec<ExecutionFailureState>,
    pub transition_guards: Vec<String>,
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
pub enum ExecutionLifecycleMode {
    HostedWorkerPlanned,
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
        ExecutionJobStatus, ExecutionLifecycleMode, ExecutionQueue, ExecutionQueueError,
        ExecutionWorkOrderMode, execution_lifecycle_spec,
    };
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
