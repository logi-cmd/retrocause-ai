use axum::{
    Json, Router,
    extract::{Path, State},
    http::StatusCode,
    routing::get,
};
use retrocause_pro_domain::{
    CreateRunRequest, KnowledgeGraph, ProRun, RunStatus, RunSummary, create_run_from_request,
    sample_run,
};
use serde::Serialize;
use std::{
    collections::HashMap,
    sync::{
        Arc, RwLock,
        atomic::{AtomicU64, Ordering},
    },
};

#[derive(Serialize)]
struct HealthPayload {
    service: &'static str,
    status: &'static str,
}

#[derive(Debug, Serialize)]
struct ErrorPayload {
    error: String,
    run_id: Option<String>,
}

#[derive(Serialize)]
struct GraphPayload {
    run_id: String,
    title: String,
    status: RunStatus,
    confidence: f32,
    graph: KnowledgeGraph,
}

type ApiError = (StatusCode, Json<ErrorPayload>);

#[derive(Clone)]
struct AppState {
    runs: Arc<RwLock<HashMap<String, ProRun>>>,
    next_sequence: Arc<AtomicU64>,
}

impl AppState {
    fn seeded() -> Self {
        let sample = sample_run();
        let mut runs = HashMap::new();
        runs.insert(sample.id.clone(), sample);

        Self {
            runs: Arc::new(RwLock::new(runs)),
            next_sequence: Arc::new(AtomicU64::new(1)),
        }
    }
}

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/healthz", get(health))
        .route("/api/graph/seed", get(seed_graph))
        .route("/api/runs", get(list_runs).post(create_run))
        .route("/api/runs/{run_id}", get(get_run))
        .route("/api/runs/{run_id}/graph", get(get_run_graph))
        .with_state(AppState::seeded())
}

async fn index() -> &'static str {
    "RetroCause Pro API"
}

async fn health() -> Json<HealthPayload> {
    Json(HealthPayload {
        service: "retrocause-pro-api",
        status: "ok",
    })
}

async fn seed_graph(State(state): State<AppState>) -> Json<ProRun> {
    Json(get_run_from_state(&state, "run_semiconductor_controls_001").unwrap_or_else(sample_run))
}

async fn list_runs(State(state): State<AppState>) -> Json<Vec<RunSummary>> {
    let runs = state
        .runs
        .read()
        .expect("run store lock should be readable");
    let mut summaries = runs
        .values()
        .map(ProRun::summary)
        .collect::<Vec<RunSummary>>();

    summaries.sort_by(|left, right| {
        right
            .updated_at
            .cmp(&left.updated_at)
            .then_with(|| left.id.cmp(&right.id))
    });

    Json(summaries)
}

async fn create_run(
    State(state): State<AppState>,
    Json(request): Json<CreateRunRequest>,
) -> Result<(StatusCode, Json<ProRun>), ApiError> {
    let sequence = state.next_sequence.fetch_add(1, Ordering::Relaxed);
    let run = create_run_from_request(sequence, request).map_err(bad_request)?;

    state
        .runs
        .write()
        .expect("run store lock should be writable")
        .insert(run.id.clone(), run.clone());

    Ok((StatusCode::CREATED, Json(run)))
}

async fn get_run(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<ProRun>, ApiError> {
    get_run_from_state(&state, &run_id)
        .map(Json)
        .ok_or_else(|| not_found(run_id))
}

async fn get_run_graph(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GraphPayload>, ApiError> {
    let run = get_run_from_state(&state, &run_id).ok_or_else(|| not_found(run_id))?;
    Ok(Json(GraphPayload {
        run_id: run.id,
        title: run.title,
        status: run.status,
        confidence: run.confidence,
        graph: run.graph,
    }))
}

fn get_run_from_state(state: &AppState, run_id: &str) -> Option<ProRun> {
    state
        .runs
        .read()
        .expect("run store lock should be readable")
        .get(run_id)
        .cloned()
}

fn bad_request(error: String) -> ApiError {
    (
        StatusCode::BAD_REQUEST,
        Json(ErrorPayload {
            error,
            run_id: None,
        }),
    )
}

fn not_found(run_id: String) -> ApiError {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorPayload {
            error: "run_not_found".to_string(),
            run_id: Some(run_id),
        }),
    )
}

#[tokio::main]
async fn main() {
    let port = std::env::var("PRO_API_PORT")
        .ok()
        .and_then(|value| value.parse::<u16>().ok())
        .unwrap_or(8787);
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", port))
        .await
        .expect("bind pro api listener");

    println!("RetroCause Pro API listening on http://127.0.0.1:{port}");
    axum::serve(listener, router())
        .await
        .expect("serve pro api");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::response::IntoResponse;

    #[tokio::test]
    async fn health_payload_is_ok() {
        let payload = health().await.0;
        assert_eq!(payload.service, "retrocause-pro-api");
        assert_eq!(payload.status, "ok");
    }

    #[tokio::test]
    async fn list_runs_exposes_summary_counts() {
        let runs = list_runs(State(AppState::seeded())).await.0;

        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].id.as_str(), "run_semiconductor_controls_001");
        assert!(runs[0].node_count > 0);
        assert!(runs[0].edge_count > 0);
    }

    #[tokio::test]
    async fn graph_payload_is_scoped_to_requested_run() {
        let payload = get_run_graph(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id.as_str(), "run_semiconductor_controls_001");
        assert_eq!(payload.graph.nodes.len(), sample_run().graph.nodes.len());
    }

    #[tokio::test]
    async fn unknown_run_returns_404_payload() {
        let response = get_run(State(AppState::seeded()), Path("missing".to_string()))
            .await
            .expect_err("missing run should return not found")
            .into_response();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn create_run_stores_run_for_detail_and_graph_reads() {
        let state = AppState::seeded();

        let (status, Json(created)) = create_run(
            State(state.clone()),
            Json(CreateRunRequest {
                workspace_id: Some("workspace_test".to_string()),
                title: Some("Renewal conversion drop".to_string()),
                question: "Why did renewal conversion drop?".to_string(),
            }),
        )
        .await
        .expect("valid request should create a run");

        assert_eq!(status, StatusCode::CREATED);
        assert_eq!(created.workspace_id, "workspace_test");
        assert_eq!(created.title, "Renewal conversion drop");

        let detail = get_run(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run should be readable")
            .0;
        assert_eq!(detail.question, "Why did renewal conversion drop?");

        let graph = get_run_graph(State(state), Path(created.id.clone()))
            .await
            .expect("created run graph should be readable")
            .0;
        assert_eq!(graph.run_id, created.id);
        assert_eq!(graph.graph.nodes.len(), 3);
    }

    #[tokio::test]
    async fn create_run_rejects_blank_question() {
        let response = create_run(
            State(AppState::seeded()),
            Json(CreateRunRequest {
                workspace_id: None,
                title: None,
                question: "   ".to_string(),
            }),
        )
        .await
        .expect_err("blank question should return bad request")
        .into_response();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    }
}
