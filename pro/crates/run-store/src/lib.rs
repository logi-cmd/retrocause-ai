use retrocause_pro_domain::{
    CreateRunRequest, ProRun, RunSummary, create_run_from_request, sample_run,
};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    env, fmt, fs,
    path::{Path, PathBuf},
    sync::{Arc, RwLock},
};

const STORE_SCHEMA_VERSION: u8 = 1;
const DEFAULT_STORE_PATH: &str = ".retrocause/pro_runs.json";
const STORE_PATH_ENV: &str = "RETROCAUSE_PRO_RUN_STORE_PATH";

#[derive(Clone)]
pub struct FileRunStore {
    path: Arc<PathBuf>,
    state: Arc<RwLock<StoredRunState>>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct StoredRunState {
    schema_version: u8,
    next_sequence: u64,
    runs: HashMap<String, ProRun>,
}

#[derive(Debug)]
pub enum RunStoreError {
    Io(std::io::Error),
    Json(serde_json::Error),
    InvalidRun(String),
    LockPoisoned,
}

#[derive(Clone, Debug, Serialize)]
pub struct HostedStorageMigrationPlan {
    pub mode: HostedStorageMode,
    pub connections_enabled: bool,
    pub components: Vec<HostedStorageComponent>,
    pub tenant_boundaries: Vec<HostedStorageBoundary>,
    pub worker_ownership: Vec<HostedStorageBoundary>,
    pub migration_steps: Vec<HostedMigrationStep>,
    pub non_goals: Vec<String>,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum HostedStorageMode {
    PlannedNoConnections,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct HostedStorageComponent {
    pub id: &'static str,
    pub target: &'static str,
    pub owner: &'static str,
    pub purpose: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct HostedStorageBoundary {
    pub id: &'static str,
    pub owner: &'static str,
    pub rule: &'static str,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct HostedMigrationStep {
    pub id: &'static str,
    pub status: &'static str,
    pub exit_criteria: &'static str,
}

impl FileRunStore {
    pub fn open_default() -> Result<Self, RunStoreError> {
        Self::open(default_run_store_path())
    }

    pub fn open(path: impl Into<PathBuf>) -> Result<Self, RunStoreError> {
        let path = path.into();
        let state = if path.exists() && fs::metadata(&path)?.len() > 0 {
            read_state(&path)?
        } else {
            StoredRunState::seeded()
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

    pub fn list_summaries(&self) -> Vec<RunSummary> {
        let state = self
            .state
            .read()
            .expect("run store lock should be readable");
        let mut summaries = state
            .runs
            .values()
            .map(ProRun::summary)
            .collect::<Vec<RunSummary>>();

        summaries.sort_by(|left, right| {
            right
                .updated_at
                .cmp(&left.updated_at)
                .then_with(|| left.id.cmp(&right.id))
        });

        summaries
    }

    pub fn get_run(&self, run_id: &str) -> Option<ProRun> {
        self.state
            .read()
            .expect("run store lock should be readable")
            .runs
            .get(run_id)
            .cloned()
    }

    pub fn create_run(&self, request: CreateRunRequest) -> Result<ProRun, RunStoreError> {
        let mut state = self
            .state
            .write()
            .map_err(|_| RunStoreError::LockPoisoned)?;
        let run = create_run_from_request(state.next_sequence, request)
            .map_err(RunStoreError::InvalidRun)?;

        state.next_sequence += 1;
        state.runs.insert(run.id.clone(), run.clone());
        write_state(&self.path, &state)?;

        Ok(run)
    }

    fn persist_current_state(&self) -> Result<(), RunStoreError> {
        let state = self.state.read().map_err(|_| RunStoreError::LockPoisoned)?;
        write_state(&self.path, &state)
    }
}

impl StoredRunState {
    fn seeded() -> Self {
        let sample = sample_run();
        let mut runs = HashMap::new();
        runs.insert(sample.id.clone(), sample);

        Self {
            schema_version: STORE_SCHEMA_VERSION,
            next_sequence: 1,
            runs,
        }
    }
}

pub fn default_run_store_path() -> PathBuf {
    env::var_os(STORE_PATH_ENV)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(DEFAULT_STORE_PATH))
}

pub fn hosted_storage_migration_plan() -> HostedStorageMigrationPlan {
    HostedStorageMigrationPlan {
        mode: HostedStorageMode::PlannedNoConnections,
        connections_enabled: false,
        components: vec![
            HostedStorageComponent {
                id: "postgres_runs",
                target: "postgres",
                owner: "api",
                purpose: "Durably store run metadata, graph payload revisions, review status, and export metadata.",
            },
            HostedStorageComponent {
                id: "postgres_evidence",
                target: "postgres",
                owner: "api",
                purpose: "Store uploaded evidence, normalized provider evidence, citation anchors, and source policy metadata.",
            },
            HostedStorageComponent {
                id: "postgres_usage_ledger",
                target: "postgres",
                owner: "billing_and_quota",
                purpose: "Record provider/source usage, quota owner, billable units, cooldowns, and audit rows.",
            },
            HostedStorageComponent {
                id: "redis_execution_queue",
                target: "redis",
                owner: "worker_pool",
                purpose: "Hold claimable execution jobs, worker leases, retry timestamps, and cancellation markers.",
            },
            HostedStorageComponent {
                id: "redis_cooldown_buckets",
                target: "redis",
                owner: "provider_router",
                purpose: "Share short-lived provider cooldown and rate-limit state across API and workers.",
            },
            HostedStorageComponent {
                id: "credential_vault",
                target: "vault",
                owner: "worker_pool",
                purpose: "Resolve provider credentials inside worker-owned execution paths, never inside route handlers.",
            },
        ],
        tenant_boundaries: vec![
            HostedStorageBoundary {
                id: "workspace_id_required",
                owner: "api",
                rule: "Every persisted run, evidence item, usage row, and queue job must carry a workspace id.",
            },
            HostedStorageBoundary {
                id: "user_identity_required",
                owner: "api",
                rule: "Hosted writes require an authenticated actor id before persistence.",
            },
            HostedStorageBoundary {
                id: "row_level_policy_required",
                owner: "postgres",
                rule: "Tenant-scoped tables must be protected by workspace-aware access policy.",
            },
            HostedStorageBoundary {
                id: "audit_log_required",
                owner: "api",
                rule: "Credential, export, review-link, and billing-sensitive actions must write audit metadata.",
            },
        ],
        worker_ownership: vec![
            HostedStorageBoundary {
                id: "worker_claims_redis_lease",
                owner: "worker_pool",
                rule: "Workers must claim jobs through leases before reading work orders.",
            },
            HostedStorageBoundary {
                id: "worker_writes_status_events",
                owner: "worker_pool",
                rule: "Workers own execution status events after a lease is claimed.",
            },
            HostedStorageBoundary {
                id: "routes_do_not_execute_jobs",
                owner: "api",
                rule: "Route handlers create jobs and read state; they do not call providers or mutate worker leases.",
            },
            HostedStorageBoundary {
                id: "workers_read_vault_credentials",
                owner: "worker_pool",
                rule: "Only workers resolve provider credentials from a vault boundary.",
            },
            HostedStorageBoundary {
                id: "partial_results_are_persisted",
                owner: "worker_pool",
                rule: "Workers preserve partial evidence and degraded-source state before retry or failure.",
            },
        ],
        migration_steps: vec![
            HostedMigrationStep {
                id: "keep_local_alpha_store",
                status: "current",
                exit_criteria: "Local JSON and in-memory queue remain the Pro prototype boundary.",
            },
            HostedMigrationStep {
                id: "define_postgres_schema",
                status: "planned",
                exit_criteria: "Runs, evidence, usage ledger, review links, and export metadata have tenant-scoped schemas.",
            },
            HostedMigrationStep {
                id: "define_redis_queue",
                status: "planned",
                exit_criteria: "Queue keys, leases, retry timestamps, cancellation markers, and cooldown buckets are named.",
            },
            HostedMigrationStep {
                id: "dual_write_non_provider_state",
                status: "planned",
                exit_criteria: "API can write run/job metadata to hosted stores without provider execution.",
            },
            HostedMigrationStep {
                id: "enable_worker_lease_smoke",
                status: "planned",
                exit_criteria: "A worker can claim a dry-run job, write status events, and release the lease.",
            },
        ],
        non_goals: vec![
            "no_database_connection_in_this_slice".to_string(),
            "no_redis_connection_in_this_slice".to_string(),
            "no_schema_migration_in_this_slice".to_string(),
            "no_provider_execution_in_this_slice".to_string(),
            "no_credentials_or_billing_in_this_slice".to_string(),
        ],
    }
}

fn read_state(path: &Path) -> Result<StoredRunState, RunStoreError> {
    let raw = fs::read_to_string(path)?;
    let mut state = serde_json::from_str::<StoredRunState>(&raw)?;

    if state.schema_version == 0 {
        state.schema_version = STORE_SCHEMA_VERSION;
    }

    Ok(state)
}

fn write_state(path: &Path, state: &StoredRunState) -> Result<(), RunStoreError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let raw = serde_json::to_string_pretty(state)?;
    fs::write(path, raw)?;
    Ok(())
}

impl fmt::Display for RunStoreError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(formatter, "run_store_io_error: {error}"),
            Self::Json(error) => write!(formatter, "run_store_json_error: {error}"),
            Self::InvalidRun(error) => write!(formatter, "{error}"),
            Self::LockPoisoned => write!(formatter, "run_store_lock_poisoned"),
        }
    }
}

impl std::error::Error for RunStoreError {}

impl From<std::io::Error> for RunStoreError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for RunStoreError {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

#[cfg(test)]
mod tests {
    use super::{
        FileRunStore, HostedStorageMode, RunStoreError, hosted_storage_migration_plan,
        temp_store_path,
    };
    use retrocause_pro_domain::CreateRunRequest;
    use std::fs;

    #[test]
    fn open_seeds_sample_run_and_writes_file() {
        let path = temp_store_path("seeded");
        let store = FileRunStore::open(&path).expect("store should open");

        let runs = store.list_summaries();
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].id.as_str(), "run_semiconductor_controls_001");
        assert!(path.exists());

        let _ = fs::remove_file(path);
    }

    #[test]
    fn created_run_survives_reopen() {
        let path = temp_store_path("reopen");
        let store = FileRunStore::open(&path).expect("store should open");
        let created = store
            .create_run(CreateRunRequest {
                workspace_id: Some("workspace_persisted".to_string()),
                title: Some("Persisted run".to_string()),
                question: "Why did retention fall?".to_string(),
            })
            .expect("valid run should be created");

        let reopened = FileRunStore::open(&path).expect("store should reopen");
        let loaded = reopened
            .get_run(&created.id)
            .expect("created run should survive reopen");

        assert_eq!(loaded.title, "Persisted run");
        assert_eq!(loaded.workspace_id, "workspace_persisted");

        let _ = fs::remove_file(path);
    }

    #[test]
    fn blank_questions_are_rejected_without_overwriting_store() {
        let path = temp_store_path("blank");
        let store = FileRunStore::open(&path).expect("store should open");
        let before = fs::read_to_string(&path).expect("store file should exist");

        let error = store
            .create_run(CreateRunRequest {
                workspace_id: None,
                title: None,
                question: "   ".to_string(),
            })
            .expect_err("blank question should be rejected");

        assert!(matches!(error, RunStoreError::InvalidRun(_)));
        assert_eq!(
            fs::read_to_string(&path).expect("store file should still exist"),
            before
        );

        let _ = fs::remove_file(path);
    }

    #[test]
    fn hosted_storage_plan_keeps_connections_disabled() {
        let plan = hosted_storage_migration_plan();

        assert_eq!(plan.mode, HostedStorageMode::PlannedNoConnections);
        assert!(!plan.connections_enabled);
        assert!(
            plan.components
                .iter()
                .any(|component| component.id == "postgres_runs")
        );
        assert!(
            plan.components
                .iter()
                .any(|component| component.id == "redis_execution_queue")
        );
        assert!(
            plan.tenant_boundaries
                .iter()
                .any(|boundary| boundary.id == "workspace_id_required")
        );
        assert!(
            plan.worker_ownership
                .iter()
                .any(|boundary| boundary.id == "workers_read_vault_credentials")
        );
        assert!(
            plan.non_goals
                .contains(&"no_database_connection_in_this_slice".to_string())
        );
    }
}

#[cfg(test)]
fn temp_store_path(label: &str) -> PathBuf {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();

    std::env::temp_dir().join(format!(
        "retrocause-pro-run-store-{label}-{}-{nanos}.json",
        std::process::id()
    ))
}
