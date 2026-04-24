use axum::{
    Json, Router,
    body::Body,
    extract::{Path, State},
    http::{HeaderMap, HeaderValue, Request, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::get,
};
use retrocause_pro_domain::{
    CreateRunRequest, KnowledgeGraph, ProRun, ProviderStatusSnapshot, RunStatus, RunSummary,
    provider_status_snapshot, sample_run,
};
use retrocause_pro_provider_routing::{
    RoutingPreviewError, RoutingPreviewPlan, RoutingPreviewRequest, build_routing_preview,
};
use retrocause_pro_queue::{
    ExecutionJob, ExecutionJobSummary, ExecutionQueue, ExecutionQueueError,
};
use retrocause_pro_run_store::{FileRunStore, RunStoreError};
use serde::Serialize;

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
    run_store: FileRunStore,
    execution_queue: ExecutionQueue,
}

impl AppState {
    fn open_default() -> Result<Self, RunStoreError> {
        Ok(Self {
            run_store: FileRunStore::open_default()?,
            execution_queue: ExecutionQueue::new(),
        })
    }
}

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/healthz", get(health))
        .route("/api/graph/seed", get(seed_graph))
        .route("/api/provider-status", get(provider_status))
        .route(
            "/api/provider-route/preview",
            get(provider_route_hint)
                .post(provider_route_preview)
                .options(cors_preflight),
        )
        .route(
            "/api/runs",
            get(list_runs).post(create_run).options(cors_preflight),
        )
        .route("/api/runs/{run_id}", get(get_run))
        .route("/api/runs/{run_id}/graph", get(get_run_graph))
        .route(
            "/api/execution-jobs",
            get(list_execution_jobs)
                .post(create_execution_job)
                .options(cors_preflight),
        )
        .route("/api/execution-jobs/{job_id}", get(get_execution_job))
        .layer(middleware::from_fn(add_cors_headers))
        .with_state(AppState::open_default().expect("open pro run store"))
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

async fn cors_preflight() -> Response {
    let mut response = StatusCode::NO_CONTENT.into_response();
    apply_cors_headers(response.headers_mut());
    response
}

async fn seed_graph(State(state): State<AppState>) -> Json<ProRun> {
    Json(
        state
            .run_store
            .get_run("run_semiconductor_controls_001")
            .unwrap_or_else(sample_run),
    )
}

async fn provider_status() -> Json<ProviderStatusSnapshot> {
    Json(provider_status_snapshot())
}

async fn provider_route_hint() -> Json<RoutingPreviewPlan> {
    Json(
        build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "Preview local keyless provider routing.".to_string(),
            scenario: None,
            source_policy: None,
        })
        .expect("static provider routing preview should be valid"),
    )
}

async fn provider_route_preview(
    Json(request): Json<RoutingPreviewRequest>,
) -> Result<Json<RoutingPreviewPlan>, ApiError> {
    build_routing_preview(request)
        .map(Json)
        .map_err(routing_preview_error)
}

async fn list_runs(State(state): State<AppState>) -> Json<Vec<RunSummary>> {
    Json(state.run_store.list_summaries())
}

async fn create_run(
    State(state): State<AppState>,
    Json(request): Json<CreateRunRequest>,
) -> Result<(StatusCode, Json<ProRun>), ApiError> {
    let run = state
        .run_store
        .create_run(request)
        .map_err(run_store_error)?;

    Ok((StatusCode::CREATED, Json(run)))
}

async fn get_run(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<ProRun>, ApiError> {
    state
        .run_store
        .get_run(&run_id)
        .map(Json)
        .ok_or_else(|| not_found(run_id))
}

async fn get_run_graph(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GraphPayload>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    Ok(Json(GraphPayload {
        run_id: run.id,
        title: run.title,
        status: run.status,
        confidence: run.confidence,
        graph: run.graph,
    }))
}

async fn list_execution_jobs(State(state): State<AppState>) -> Json<Vec<ExecutionJobSummary>> {
    Json(state.execution_queue.list_summaries())
}

async fn create_execution_job(
    State(state): State<AppState>,
    Json(request): Json<RoutingPreviewRequest>,
) -> Result<(StatusCode, Json<ExecutionJob>), ApiError> {
    let job = state
        .execution_queue
        .enqueue_preview(request)
        .map_err(execution_queue_error)?;

    Ok((StatusCode::CREATED, Json(job)))
}

async fn get_execution_job(
    State(state): State<AppState>,
    Path(job_id): Path<String>,
) -> Result<Json<ExecutionJob>, ApiError> {
    state
        .execution_queue
        .get_job(&job_id)
        .map(Json)
        .ok_or_else(|| job_not_found(job_id))
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

fn internal_error(error: String) -> ApiError {
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Json(ErrorPayload {
            error,
            run_id: None,
        }),
    )
}

fn run_store_error(error: RunStoreError) -> ApiError {
    match error {
        RunStoreError::InvalidRun(error) => bad_request(error),
        error => internal_error(error.to_string()),
    }
}

fn routing_preview_error(error: RoutingPreviewError) -> ApiError {
    match error {
        RoutingPreviewError::QueryRequired => bad_request(error.to_string()),
    }
}

fn execution_queue_error(error: ExecutionQueueError) -> ApiError {
    match error {
        ExecutionQueueError::RoutingPreview(error) => routing_preview_error(error),
        ExecutionQueueError::LockPoisoned => internal_error(error.to_string()),
    }
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

fn job_not_found(job_id: String) -> ApiError {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorPayload {
            error: format!("execution_job_not_found:{job_id}"),
            run_id: None,
        }),
    )
}

async fn add_cors_headers(request: Request<Body>, next: Next) -> Response {
    let mut response = next.run(request).await;
    apply_cors_headers(response.headers_mut());
    response
}

fn apply_cors_headers(headers: &mut HeaderMap) {
    headers.insert(
        header::ACCESS_CONTROL_ALLOW_ORIGIN,
        HeaderValue::from_static("*"),
    );
    headers.insert(
        header::ACCESS_CONTROL_ALLOW_METHODS,
        HeaderValue::from_static("GET,POST,OPTIONS"),
    );
    headers.insert(
        header::ACCESS_CONTROL_ALLOW_HEADERS,
        HeaderValue::from_static("content-type"),
    );
    headers.insert(
        header::ACCESS_CONTROL_MAX_AGE,
        HeaderValue::from_static("600"),
    );
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
    use std::path::PathBuf;

    impl AppState {
        fn seeded() -> Self {
            Self {
                run_store: FileRunStore::open(temp_store_path())
                    .expect("test run store should open"),
                execution_queue: ExecutionQueue::new(),
            }
        }
    }

    #[tokio::test]
    async fn health_payload_is_ok() {
        let payload = health().await.0;
        assert_eq!(payload.service, "retrocause-pro-api");
        assert_eq!(payload.status, "ok");
    }

    #[tokio::test]
    async fn cors_preflight_allows_local_web_fetches() {
        let response = cors_preflight().await;

        assert_eq!(response.status(), StatusCode::NO_CONTENT);
        assert_eq!(
            response.headers()[header::ACCESS_CONTROL_ALLOW_METHODS],
            "GET,POST,OPTIONS"
        );
        assert_eq!(
            response.headers()[header::ACCESS_CONTROL_ALLOW_HEADERS],
            "content-type"
        );
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
    async fn provider_status_exposes_keyless_quota_modes() {
        let payload = provider_status().await.0;

        assert_eq!(payload.workspace_id.as_str(), "workspace_demo");
        assert!(payload.entries.iter().any(|entry| {
            entry.id.as_str() == "market_search_cooldown"
                && entry.cooldown.retry_after_seconds == Some(900)
        }));
        assert!(payload.entries.iter().all(|entry| {
            let combined = format!("{} {} {}", entry.id, entry.label, entry.note).to_lowercase();
            !combined.contains("api_key") && !combined.contains("secret")
        }));
    }

    #[tokio::test]
    async fn provider_route_preview_exposes_non_executing_plan() {
        let plan = provider_route_preview(Json(RoutingPreviewRequest {
            workspace_id: Some("workspace_test".to_string()),
            query: "Why did chip stocks move?".to_string(),
            scenario: None,
            source_policy: None,
        }))
        .await
        .expect("valid preview request")
        .0;

        assert_eq!(plan.workspace_id, "workspace_test");
        assert!(!plan.execution_allowed);
        assert_eq!(
            plan.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );
    }

    #[tokio::test]
    async fn provider_route_preview_rejects_blank_query() {
        let response = provider_route_preview(Json(RoutingPreviewRequest {
            workspace_id: None,
            query: "   ".to_string(),
            scenario: None,
            source_policy: None,
        }))
        .await
        .expect_err("blank query should return bad request")
        .into_response();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
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

    #[tokio::test]
    async fn execution_jobs_store_preview_only_routing_plan() {
        let state = AppState::seeded();

        let (status, Json(created)) = create_execution_job(
            State(state.clone()),
            Json(RoutingPreviewRequest {
                workspace_id: Some("workspace_queue".to_string()),
                query: "Why did a run need queueing?".to_string(),
                scenario: None,
                source_policy: None,
            }),
        )
        .await
        .expect("valid request should create preview job");

        assert_eq!(status, StatusCode::CREATED);
        assert_eq!(created.id, "job_local_000000");
        assert!(!created.execution_allowed);
        assert_eq!(
            created.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );

        let detail = get_execution_job(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created job should be readable")
            .0;
        assert_eq!(detail.query, "Why did a run need queueing?");

        let summaries = list_execution_jobs(State(state)).await.0;
        assert_eq!(summaries.len(), 1);
        assert_eq!(summaries[0].id, created.id);
    }

    #[tokio::test]
    async fn execution_job_rejects_blank_query() {
        let response = create_execution_job(
            State(AppState::seeded()),
            Json(RoutingPreviewRequest {
                workspace_id: None,
                query: "  ".to_string(),
                scenario: None,
                source_policy: None,
            }),
        )
        .await
        .expect_err("blank query should return bad request")
        .into_response();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    }

    #[tokio::test]
    async fn unknown_execution_job_returns_404_payload() {
        let response = get_execution_job(State(AppState::seeded()), Path("missing".to_string()))
            .await
            .expect_err("missing job should return not found")
            .into_response();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }

    fn temp_store_path() -> PathBuf {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("system clock should be after unix epoch")
            .as_nanos();

        std::env::temp_dir().join(format!(
            "retrocause-pro-api-store-{}-{nanos}.json",
            std::process::id()
        ))
    }
}
