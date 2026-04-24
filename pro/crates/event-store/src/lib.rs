use retrocause_pro_domain::{ProRun, RunEvent, run_event_timeline};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    env, fmt, fs,
    path::{Path, PathBuf},
    sync::{Arc, RwLock},
};

const STORE_SCHEMA_VERSION: u8 = 1;
const DEFAULT_STORE_PATH: &str = ".retrocause/pro_events.json";
const STORE_PATH_ENV: &str = "RETROCAUSE_PRO_EVENT_STORE_PATH";

#[derive(Clone)]
pub struct FileEventStore {
    path: Arc<PathBuf>,
    state: Arc<RwLock<StoredEventState>>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct StoredEventState {
    schema_version: u8,
    streams: HashMap<String, Vec<EventStoreEntry>>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EventStoreEntry {
    pub id: String,
    pub run_id: String,
    pub workspace_id: String,
    pub sequence: u32,
    pub recorded_at: String,
    pub source: EventStoreEntrySource,
    pub event: RunEvent,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EventStoreReplay {
    pub run_id: String,
    pub workspace_id: String,
    pub mode: EventReplayMode,
    pub generated_at: String,
    pub durable: bool,
    pub event_count: usize,
    pub events: Vec<EventStoreEntry>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultDryRun {
    pub run_id: String,
    pub workspace_id: String,
    pub mode: WorkerResultDryRunMode,
    pub execution_allowed: bool,
    pub provider_execution_allowed: bool,
    pub result_commit_allowed: bool,
    pub result_event_write_allowed: bool,
    pub replay_event_count: usize,
    pub proposed_steps: Vec<WorkerResultDryRunStep>,
    pub commit_checks: Vec<WorkerResultCommitCheck>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultDryRunStep {
    pub id: String,
    pub label: String,
    pub status: WorkerResultDryRunStepStatus,
    pub depends_on_replay_events: usize,
    pub writes_now: bool,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultCommitCheck {
    pub id: String,
    pub label: String,
    pub passed: bool,
    pub required_before_live_execution: bool,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResultSnapshotReadiness {
    pub run_id: String,
    pub workspace_id: String,
    pub mode: ResultSnapshotReadinessMode,
    pub snapshot_persistence_allowed: bool,
    pub result_event_write_allowed: bool,
    pub provider_execution_allowed: bool,
    pub worker_commit_required: bool,
    pub replay_event_count: usize,
    pub proposed_snapshot: ResultSnapshotPreview,
    pub readiness_checks: Vec<ResultSnapshotReadinessCheck>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResultSnapshotPreview {
    pub id: String,
    pub run_revision: String,
    pub source_replay_events: usize,
    pub graph_node_count: usize,
    pub evidence_count: usize,
    pub challenge_count: usize,
    pub persisted: bool,
    pub publishable: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResultSnapshotReadinessCheck {
    pub id: String,
    pub label: String,
    pub passed: bool,
    pub blocking_snapshot_persistence: bool,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultCommitIntent {
    pub run_id: String,
    pub workspace_id: String,
    pub mode: WorkerResultCommitIntentMode,
    pub status: WorkerResultCommitIntentStatus,
    pub commit_allowed: bool,
    pub result_event_write_allowed: bool,
    pub snapshot_persistence_allowed: bool,
    pub provider_execution_allowed: bool,
    pub idempotency_key_required: bool,
    pub idempotency_key_preview: String,
    pub worker_lease_required: bool,
    pub readiness_check_count: usize,
    pub blocking_checks: Vec<WorkerResultCommitBlocker>,
    pub event_writes: Vec<WorkerResultCommitEventWrite>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultCommitBlocker {
    pub id: String,
    pub label: String,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkerResultCommitEventWrite {
    pub id: String,
    pub event_kind: String,
    pub owner: String,
    pub allowed_now: bool,
    pub idempotency_required: bool,
    pub note: String,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EventReplayMode {
    LocalFileReplay,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EventStoreEntrySource {
    DerivedRunTimelinePersistedLocally,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerResultDryRunMode {
    PreviewOnlyLocalReplay,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerResultDryRunStepStatus {
    PreviewOnly,
    BlockedUntilWorkerCommit,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ResultSnapshotReadinessMode {
    PreviewOnlyGate,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerResultCommitIntentMode {
    PreviewOnlyFromSnapshotReadiness,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkerResultCommitIntentStatus {
    RejectedUntilHostedGates,
}

#[derive(Debug)]
pub enum EventStoreError {
    Io(std::io::Error),
    Json(serde_json::Error),
    LockPoisoned,
}

impl FileEventStore {
    pub fn open_default() -> Result<Self, EventStoreError> {
        Self::open(default_event_store_path())
    }

    pub fn open(path: impl Into<PathBuf>) -> Result<Self, EventStoreError> {
        let path = path.into();
        let state = if path.exists() && fs::metadata(&path)?.len() > 0 {
            read_state(&path)?
        } else {
            StoredEventState::empty()
        };

        let store = Self {
            path: Arc::new(path),
            state: Arc::new(RwLock::new(state)),
        };
        store.persist_current_state()?;
        Ok(store)
    }

    pub fn path(&self) -> &Path {
        self.path.as_path()
    }

    pub fn ensure_run_events(&self, run: &ProRun) -> Result<EventStoreReplay, EventStoreError> {
        let mut state = self
            .state
            .write()
            .map_err(|_| EventStoreError::LockPoisoned)?;
        if !state.streams.contains_key(&run.id) {
            let entries = entries_from_run(run);
            state.streams.insert(run.id.clone(), entries);
            write_state(&self.path, &state)?;
        }

        Ok(replay_from_entries(
            run,
            state.streams.get(&run.id).cloned().unwrap_or_default(),
        ))
    }

    pub fn list_run_events(&self, run: &ProRun) -> Result<Vec<EventStoreEntry>, EventStoreError> {
        Ok(self.ensure_run_events(run)?.events)
    }

    pub fn worker_result_dry_run(
        &self,
        run: &ProRun,
    ) -> Result<WorkerResultDryRun, EventStoreError> {
        let replay = self.ensure_run_events(run)?;
        Ok(worker_result_dry_run_from_replay(&replay))
    }

    pub fn result_snapshot_readiness(
        &self,
        run: &ProRun,
    ) -> Result<ResultSnapshotReadiness, EventStoreError> {
        let dry_run = self.worker_result_dry_run(run)?;
        Ok(result_snapshot_readiness_from_dry_run(run, &dry_run))
    }

    pub fn worker_result_commit_intent(
        &self,
        run: &ProRun,
    ) -> Result<WorkerResultCommitIntent, EventStoreError> {
        let readiness = self.result_snapshot_readiness(run)?;
        Ok(worker_result_commit_intent_from_readiness(run, &readiness))
    }

    fn persist_current_state(&self) -> Result<(), EventStoreError> {
        let state = self
            .state
            .read()
            .map_err(|_| EventStoreError::LockPoisoned)?;
        write_state(&self.path, &state)
    }
}

impl StoredEventState {
    fn empty() -> Self {
        Self {
            schema_version: STORE_SCHEMA_VERSION,
            streams: HashMap::new(),
        }
    }
}

pub fn default_event_store_path() -> PathBuf {
    env::var_os(STORE_PATH_ENV)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(DEFAULT_STORE_PATH))
}

fn entries_from_run(run: &ProRun) -> Vec<EventStoreEntry> {
    run_event_timeline(run)
        .events
        .into_iter()
        .map(|event| entry_from_event(run, event))
        .collect()
}

fn entry_from_event(run: &ProRun, event: RunEvent) -> EventStoreEntry {
    EventStoreEntry {
        id: format!("{}_store_{:02}", run.id, event.sequence),
        run_id: run.id.clone(),
        workspace_id: run.workspace_id.clone(),
        sequence: event.sequence,
        recorded_at: format!("local-event-store:{}#{}", run.updated_at, event.sequence),
        source: EventStoreEntrySource::DerivedRunTimelinePersistedLocally,
        event,
    }
}

fn replay_from_entries(run: &ProRun, events: Vec<EventStoreEntry>) -> EventStoreReplay {
    EventStoreReplay {
        run_id: run.id.clone(),
        workspace_id: run.workspace_id.clone(),
        mode: EventReplayMode::LocalFileReplay,
        generated_at: format!("local-event-replay:{}", run.updated_at),
        durable: true,
        event_count: events.len(),
        events,
        safeguards: vec![
            "local_file_event_store_only".to_string(),
            "no_postgres_or_redis_connection".to_string(),
            "no_worker_or_provider_execution".to_string(),
            "no_auth_or_credential_access".to_string(),
            "replay_is_run_scoped_by_requested_run_id".to_string(),
        ],
    }
}

pub fn worker_result_dry_run_from_replay(replay: &EventStoreReplay) -> WorkerResultDryRun {
    let replay_event_count = replay.events.len();
    WorkerResultDryRun {
        run_id: replay.run_id.clone(),
        workspace_id: replay.workspace_id.clone(),
        mode: WorkerResultDryRunMode::PreviewOnlyLocalReplay,
        execution_allowed: false,
        provider_execution_allowed: false,
        result_commit_allowed: false,
        result_event_write_allowed: false,
        replay_event_count,
        proposed_steps: vec![
            WorkerResultDryRunStep {
                id: "read_local_replay_stream".to_string(),
                label: "Read local replay stream".to_string(),
                status: WorkerResultDryRunStepStatus::PreviewOnly,
                depends_on_replay_events: replay_event_count,
                writes_now: false,
                note: "Use the persisted local replay stream as dry-run input.".to_string(),
            },
            WorkerResultDryRunStep {
                id: "prepare_result_commit_batch".to_string(),
                label: "Prepare result commit batch".to_string(),
                status: WorkerResultDryRunStepStatus::PreviewOnly,
                depends_on_replay_events: replay_event_count,
                writes_now: false,
                note: "Preview the result commit envelope without mutating the run.".to_string(),
            },
            WorkerResultDryRunStep {
                id: "commit_result_events".to_string(),
                label: "Commit result events".to_string(),
                status: WorkerResultDryRunStepStatus::BlockedUntilWorkerCommit,
                depends_on_replay_events: replay_event_count,
                writes_now: false,
                note: "Blocked until real worker leases, auth, quota, vault, and event writes exist."
                    .to_string(),
            },
            WorkerResultDryRunStep {
                id: "publish_review_ready_snapshot".to_string(),
                label: "Publish review-ready snapshot".to_string(),
                status: WorkerResultDryRunStepStatus::BlockedUntilWorkerCommit,
                depends_on_replay_events: replay_event_count,
                writes_now: false,
                note: "Blocked until committed result events can update the run revision.".to_string(),
            },
        ],
        commit_checks: vec![
            WorkerResultCommitCheck {
                id: "local_replay_loaded".to_string(),
                label: "Local replay loaded".to_string(),
                passed: replay_event_count > 0,
                required_before_live_execution: true,
                note: format!("{replay_event_count} replay event(s) available for dry-run input."),
            },
            WorkerResultCommitCheck {
                id: "worker_lease_available".to_string(),
                label: "Worker lease available".to_string(),
                passed: false,
                required_before_live_execution: true,
                note: "No worker process or lease store is connected in this slice.".to_string(),
            },
            WorkerResultCommitCheck {
                id: "tenant_auth_enforced".to_string(),
                label: "Tenant auth enforced".to_string(),
                passed: false,
                required_before_live_execution: true,
                note: "The current Pro shell exposes preview context only, not real auth.".to_string(),
            },
            WorkerResultCommitCheck {
                id: "quota_and_vault_ready".to_string(),
                label: "Quota and vault ready".to_string(),
                passed: false,
                required_before_live_execution: true,
                note: "Provider credentials, quota reservations, and billing mutations remain disabled."
                    .to_string(),
            },
        ],
        safeguards: vec![
            "preview_only_no_result_event_writes".to_string(),
            "uses_local_event_replay_as_input".to_string(),
            "no_worker_process_started".to_string(),
            "no_provider_execution_or_secret_access".to_string(),
            "no_quota_or_billing_mutation".to_string(),
            "run_scoped_to_requested_run_id".to_string(),
        ],
    }
}

pub fn result_snapshot_readiness_from_dry_run(
    run: &ProRun,
    dry_run: &WorkerResultDryRun,
) -> ResultSnapshotReadiness {
    let replay_event_count = dry_run.replay_event_count;
    ResultSnapshotReadiness {
        run_id: run.id.clone(),
        workspace_id: run.workspace_id.clone(),
        mode: ResultSnapshotReadinessMode::PreviewOnlyGate,
        snapshot_persistence_allowed: false,
        result_event_write_allowed: false,
        provider_execution_allowed: false,
        worker_commit_required: true,
        replay_event_count,
        proposed_snapshot: ResultSnapshotPreview {
            id: format!("{}_snapshot_preview", run.id),
            run_revision: run.updated_at.clone(),
            source_replay_events: replay_event_count,
            graph_node_count: run.graph.nodes.len(),
            evidence_count: run.evidence.len(),
            challenge_count: run.challenge_checks.len(),
            persisted: false,
            publishable: false,
        },
        readiness_checks: vec![
            ResultSnapshotReadinessCheck {
                id: "worker_dry_run_loaded".to_string(),
                label: "Worker dry-run loaded".to_string(),
                passed: replay_event_count > 0,
                blocking_snapshot_persistence: replay_event_count == 0,
                note: format!(
                    "{replay_event_count} replay event(s) are available for snapshot preview input."
                ),
            },
            ResultSnapshotReadinessCheck {
                id: "durable_worker_commit_ready".to_string(),
                label: "Durable worker commit ready".to_string(),
                passed: false,
                blocking_snapshot_persistence: true,
                note: "No worker-owned durable result-event commit path exists yet.".to_string(),
            },
            ResultSnapshotReadinessCheck {
                id: "tenant_auth_enforced".to_string(),
                label: "Tenant auth enforced".to_string(),
                passed: false,
                blocking_snapshot_persistence: true,
                note: "The Pro shell still uses a preview-only workspace context.".to_string(),
            },
            ResultSnapshotReadinessCheck {
                id: "quota_reservation_ready".to_string(),
                label: "Quota reservation ready".to_string(),
                passed: false,
                blocking_snapshot_persistence: true,
                note: "Quota ledger rows and billable usage writes remain disabled.".to_string(),
            },
            ResultSnapshotReadinessCheck {
                id: "credential_vault_ready".to_string(),
                label: "Credential vault ready".to_string(),
                passed: false,
                blocking_snapshot_persistence: true,
                note: "Provider credentials cannot be read by workers in this slice.".to_string(),
            },
            ResultSnapshotReadinessCheck {
                id: "idempotent_event_writes_ready".to_string(),
                label: "Idempotent event writes ready".to_string(),
                passed: false,
                blocking_snapshot_persistence: true,
                note: "Result-event writes still need idempotency keys and replay-safe commits."
                    .to_string(),
            },
        ],
        safeguards: vec![
            "preview_only_no_snapshot_persistence".to_string(),
            "derives_from_worker_result_dry_run".to_string(),
            "uses_local_event_replay_as_input".to_string(),
            "no_result_event_writes".to_string(),
            "no_provider_execution_or_secret_access".to_string(),
            "no_quota_or_billing_mutation".to_string(),
            "run_scoped_to_requested_run_id".to_string(),
        ],
    }
}

pub fn worker_result_commit_intent_from_readiness(
    run: &ProRun,
    readiness: &ResultSnapshotReadiness,
) -> WorkerResultCommitIntent {
    let blocking_checks = readiness
        .readiness_checks
        .iter()
        .filter(|check| check.blocking_snapshot_persistence || !check.passed)
        .map(|check| WorkerResultCommitBlocker {
            id: check.id.clone(),
            label: check.label.clone(),
            note: check.note.clone(),
        })
        .collect::<Vec<_>>();

    WorkerResultCommitIntent {
        run_id: run.id.clone(),
        workspace_id: run.workspace_id.clone(),
        mode: WorkerResultCommitIntentMode::PreviewOnlyFromSnapshotReadiness,
        status: WorkerResultCommitIntentStatus::RejectedUntilHostedGates,
        commit_allowed: false,
        result_event_write_allowed: false,
        snapshot_persistence_allowed: false,
        provider_execution_allowed: false,
        idempotency_key_required: true,
        idempotency_key_preview: format!("preview:{}:{}:result_commit", run.id, run.updated_at),
        worker_lease_required: true,
        readiness_check_count: readiness.readiness_checks.len(),
        blocking_checks,
        event_writes: vec![
            WorkerResultCommitEventWrite {
                id: "append_worker_result_events".to_string(),
                event_kind: "worker_result_events".to_string(),
                owner: "future_hosted_worker".to_string(),
                allowed_now: false,
                idempotency_required: true,
                note: "Would append result events only after worker lease, auth, quota, and vault gates pass."
                    .to_string(),
            },
            WorkerResultCommitEventWrite {
                id: "persist_result_snapshot_revision".to_string(),
                event_kind: "result_snapshot_revision".to_string(),
                owner: "future_hosted_worker".to_string(),
                allowed_now: false,
                idempotency_required: true,
                note: "Would persist a new snapshot revision after result events commit idempotently."
                    .to_string(),
            },
            WorkerResultCommitEventWrite {
                id: "publish_review_ready_status".to_string(),
                event_kind: "run_status_update".to_string(),
                owner: "future_hosted_worker".to_string(),
                allowed_now: false,
                idempotency_required: true,
                note: "Would publish review-ready status only after durable snapshot persistence."
                    .to_string(),
            },
        ],
        safeguards: vec![
            "preview_only_commit_intent_rejected".to_string(),
            "derived_from_result_snapshot_readiness".to_string(),
            "idempotency_key_is_preview_only".to_string(),
            "no_result_event_writes".to_string(),
            "no_snapshot_persistence".to_string(),
            "no_provider_execution_or_secret_access".to_string(),
            "no_quota_or_billing_mutation".to_string(),
            "run_scoped_to_requested_run_id".to_string(),
        ],
    }
}

fn read_state(path: &Path) -> Result<StoredEventState, EventStoreError> {
    let raw = fs::read_to_string(path)?;
    let mut state = serde_json::from_str::<StoredEventState>(&raw)?;

    if state.schema_version == 0 {
        state.schema_version = STORE_SCHEMA_VERSION;
    }

    Ok(state)
}

fn write_state(path: &Path, state: &StoredEventState) -> Result<(), EventStoreError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let raw = serde_json::to_string_pretty(state)?;
    fs::write(path, raw)?;
    Ok(())
}

impl fmt::Display for EventStoreError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(formatter, "event_store_io_error: {error}"),
            Self::Json(error) => write!(formatter, "event_store_json_error: {error}"),
            Self::LockPoisoned => write!(formatter, "event_store_lock_poisoned"),
        }
    }
}

impl std::error::Error for EventStoreError {}

impl From<std::io::Error> for EventStoreError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for EventStoreError {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

#[cfg(test)]
mod tests {
    use super::{
        EventReplayMode, FileEventStore, ResultSnapshotReadinessMode, WorkerResultCommitIntentMode,
        WorkerResultCommitIntentStatus, WorkerResultDryRunMode, WorkerResultDryRunStepStatus,
        temp_store_path,
    };
    use retrocause_pro_domain::{CreateRunRequest, create_run_from_request, sample_run};
    use std::fs;

    #[test]
    fn replay_persists_sample_run_events_to_local_file() {
        let path = temp_store_path("sample");
        let store = FileEventStore::open(&path).expect("event store should open");
        let replay = store
            .ensure_run_events(&sample_run())
            .expect("sample events should persist");

        assert_eq!(replay.run_id, "run_semiconductor_controls_001");
        assert_eq!(replay.mode, EventReplayMode::LocalFileReplay);
        assert!(replay.durable);
        assert!(replay.event_count >= 3);
        assert!(path.exists());
        assert!(
            replay
                .safeguards
                .contains(&"no_worker_or_provider_execution".to_string())
        );

        let _ = fs::remove_file(path);
    }

    #[test]
    fn replay_survives_reopen_without_duplicating_events() {
        let path = temp_store_path("reopen");
        let run = create_run_from_request(
            42,
            CreateRunRequest {
                workspace_id: Some("workspace_replay".to_string()),
                title: Some("Replay run".to_string()),
                question: "Why did activation fall?".to_string(),
            },
        )
        .expect("valid run should be created");

        let store = FileEventStore::open(&path).expect("event store should open");
        let first = store
            .ensure_run_events(&run)
            .expect("events should persist");
        let reopened = FileEventStore::open(&path).expect("event store should reopen");
        let second = reopened
            .ensure_run_events(&run)
            .expect("events should replay");

        assert_eq!(first.event_count, 1);
        assert_eq!(second.event_count, 1);
        assert_eq!(second.events[0].run_id, run.id);
        assert_eq!(second.events[0].workspace_id, "workspace_replay");

        let _ = fs::remove_file(path);
    }

    #[test]
    fn list_run_events_uses_the_same_persisted_stream() {
        let path = temp_store_path("list");
        let store = FileEventStore::open(&path).expect("event store should open");
        let run = sample_run();

        let replay = store
            .ensure_run_events(&run)
            .expect("events should persist");
        let events = store
            .list_run_events(&run)
            .expect("events should be listable");

        assert_eq!(events.len(), replay.event_count);
        assert_eq!(events[0].run_id, run.id);

        let _ = fs::remove_file(path);
    }

    #[test]
    fn worker_result_dry_run_uses_replay_without_result_writes() {
        let path = temp_store_path("worker-result");
        let store = FileEventStore::open(&path).expect("event store should open");
        let run = sample_run();

        let dry_run = store
            .worker_result_dry_run(&run)
            .expect("worker result dry-run should build from replay");

        assert_eq!(dry_run.run_id, run.id);
        assert_eq!(dry_run.mode, WorkerResultDryRunMode::PreviewOnlyLocalReplay);
        assert!(!dry_run.execution_allowed);
        assert!(!dry_run.provider_execution_allowed);
        assert!(!dry_run.result_commit_allowed);
        assert!(!dry_run.result_event_write_allowed);
        assert!(dry_run.replay_event_count >= 3);
        assert!(dry_run.proposed_steps.iter().any(|step| {
            step.id == "commit_result_events"
                && step.status == WorkerResultDryRunStepStatus::BlockedUntilWorkerCommit
                && !step.writes_now
        }));
        assert!(
            dry_run
                .commit_checks
                .iter()
                .any(|check| check.id == "local_replay_loaded" && check.passed)
        );
        assert!(
            dry_run
                .safeguards
                .contains(&"preview_only_no_result_event_writes".to_string())
        );

        let _ = fs::remove_file(path);
    }

    #[test]
    fn result_snapshot_readiness_blocks_persistence_until_hosted_gates_exist() {
        let path = temp_store_path("result-snapshot-readiness");
        let store = FileEventStore::open(&path).expect("event store should open");
        let run = sample_run();

        let readiness = store
            .result_snapshot_readiness(&run)
            .expect("snapshot readiness should build from dry-run");

        assert_eq!(readiness.run_id, run.id);
        assert_eq!(readiness.mode, ResultSnapshotReadinessMode::PreviewOnlyGate);
        assert!(!readiness.snapshot_persistence_allowed);
        assert!(!readiness.result_event_write_allowed);
        assert!(!readiness.provider_execution_allowed);
        assert!(readiness.worker_commit_required);
        assert_eq!(
            readiness.proposed_snapshot.graph_node_count,
            run.graph.nodes.len()
        );
        assert_eq!(
            readiness.proposed_snapshot.evidence_count,
            run.evidence.len()
        );
        assert!(!readiness.proposed_snapshot.persisted);
        assert!(
            readiness
                .readiness_checks
                .iter()
                .any(|check| { check.id == "worker_dry_run_loaded" && check.passed })
        );
        assert!(readiness.readiness_checks.iter().any(|check| {
            check.id == "durable_worker_commit_ready" && check.blocking_snapshot_persistence
        }));
        assert!(
            readiness
                .safeguards
                .contains(&"preview_only_no_snapshot_persistence".to_string())
        );

        let _ = fs::remove_file(path);
    }

    #[test]
    fn worker_result_commit_intent_is_rejected_until_hosted_gates_exist() {
        let path = temp_store_path("worker-result-commit-intent");
        let store = FileEventStore::open(&path).expect("event store should open");
        let run = sample_run();

        let intent = store
            .worker_result_commit_intent(&run)
            .expect("commit intent should build from readiness");

        assert_eq!(intent.run_id, run.id);
        assert_eq!(
            intent.mode,
            WorkerResultCommitIntentMode::PreviewOnlyFromSnapshotReadiness
        );
        assert_eq!(
            intent.status,
            WorkerResultCommitIntentStatus::RejectedUntilHostedGates
        );
        assert!(!intent.commit_allowed);
        assert!(!intent.result_event_write_allowed);
        assert!(!intent.snapshot_persistence_allowed);
        assert!(!intent.provider_execution_allowed);
        assert!(intent.idempotency_key_required);
        assert!(intent.idempotency_key_preview.contains(run.id.as_str()));
        assert!(intent.worker_lease_required);
        assert!(intent.readiness_check_count >= 4);
        assert!(
            intent
                .blocking_checks
                .iter()
                .any(|check| { check.id == "durable_worker_commit_ready" })
        );
        assert!(
            intent
                .event_writes
                .iter()
                .all(|write| { !write.allowed_now && write.idempotency_required })
        );
        assert!(
            intent
                .safeguards
                .contains(&"preview_only_commit_intent_rejected".to_string())
        );

        let _ = fs::remove_file(path);
    }
}

#[cfg(test)]
fn temp_store_path(label: &str) -> PathBuf {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();

    std::env::temp_dir().join(format!(
        "retrocause-pro-event-store-{label}-{}-{nanos}.json",
        std::process::id()
    ))
}
