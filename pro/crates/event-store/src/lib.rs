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
    use super::{EventReplayMode, FileEventStore, temp_store_path};
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
