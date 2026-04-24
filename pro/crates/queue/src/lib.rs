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

#[derive(Debug)]
pub enum ExecutionQueueError {
    RoutingPreview(RoutingPreviewError),
    LockPoisoned,
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
    use super::{ExecutionJobStatus, ExecutionQueue, ExecutionQueueError, ExecutionWorkOrderMode};
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
