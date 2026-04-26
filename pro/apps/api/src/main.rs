use axum::{
    Json, Router,
    body::Body,
    extract::{Path, State},
    http::{HeaderMap, HeaderValue, Request, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use retrocause_pro_domain::{
    CreateRunRequest, CredentialVaultBoundary, ExecutionAdmissionDecision,
    ExecutionAdmissionRequest, ExecutionPreflightBoundary, KnowledgeGraph, ProRun,
    ProviderStatusSnapshot, QuotaLedgerBoundary, ResultCommitBoundary, RunEventTimeline,
    RunReviewComparison, RunStatus, RunSummary, WorkspaceAccessContext,
    WorkspaceAccessGateDecision, WorkspaceAccessGateRequest, credential_vault_boundary,
    execution_admission, execution_preflight_boundary, provider_status_snapshot,
    quota_ledger_boundary, result_commit_boundary, run_event_timeline, run_review_comparison,
    sample_run, workspace_access_context, workspace_access_gate,
};
use retrocause_pro_event_store::{
    EventStoreEntry, EventStoreError, EventStoreReplay, FileEventStore, ResultSnapshotReadiness,
    WorkerResultCommitIntent, WorkerResultDryRun,
};
use retrocause_pro_provider_routing::{
    ExecutionReadinessDecision, ExecutionReadinessRequest, ProviderAdapterCandidateCatalog,
    ProviderAdapterContract, ProviderAdapterDryRunRequest, ProviderAdapterDryRunResult,
    ProviderAdapterGateCheckRequest, ProviderAdapterGateCheckResult, RoutingPreviewError,
    RoutingPreviewPlan, RoutingPreviewRequest, build_routing_preview, execution_readiness_gate,
    provider_adapter_candidates, provider_adapter_contract, provider_adapter_dry_run,
    provider_adapter_gate_check,
};
use retrocause_pro_queue::{
    ExecutionHandoffPreview, ExecutionIntentCreateRequestPreview, ExecutionIntentDurabilityGate,
    ExecutionIntentPreview, ExecutionIntentStoreBoundary, ExecutionJob, ExecutionJobSummary,
    ExecutionLifecycleSpec, ExecutionQueue, ExecutionQueueError, ExecutionWorkOrder,
    WorkerLeaseBoundary, execution_intent_create_request_preview, execution_intent_durability_gate,
    execution_intent_store_boundary, execution_lifecycle_spec, worker_lease_boundary,
};
use retrocause_pro_run_store::{
    FileRunStore, HostedStorageMigrationPlan, RunStoreError, hosted_storage_migration_plan,
};
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
    event_store: FileEventStore,
    execution_queue: ExecutionQueue,
}

impl AppState {
    fn open_default() -> Result<Self, String> {
        let run_store = FileRunStore::open_default().map_err(|error| error.to_string())?;
        let event_store = FileEventStore::open_default().map_err(|error| error.to_string())?;
        if let Some(seed) = run_store.get_run("run_semiconductor_controls_001") {
            event_store
                .ensure_run_events(&seed)
                .map_err(|error| error.to_string())?;
        }

        Ok(Self {
            run_store,
            event_store,
            execution_queue: ExecutionQueue::new(),
        })
    }
}

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/healthz", get(health))
        .route("/api/graph/seed", get(seed_graph))
        .route("/api/workspace/access-context", get(workspace_access))
        .route(
            "/api/workspace/access-gate",
            post(workspace_access_gate_decision).options(cors_preflight),
        )
        .route(
            "/api/execution-readiness",
            post(execution_readiness).options(cors_preflight),
        )
        .route(
            "/api/execution-admission",
            post(execution_admission_check).options(cors_preflight),
        )
        .route(
            "/api/execution-intents/create-request",
            post(execution_intent_create_request).options(cors_preflight),
        )
        .route(
            "/api/execution-intents/durability-gate",
            post(execution_intent_durability_check).options(cors_preflight),
        )
        .route(
            "/api/execution-preflight-boundary",
            get(execution_preflight),
        )
        .route("/api/credential-vault-boundary", get(credential_vault))
        .route("/api/quota-ledger-boundary", get(quota_ledger))
        .route("/api/result-commit-boundary", get(result_commit))
        .route("/api/provider-status", get(provider_status))
        .route(
            "/api/provider-route/preview",
            get(provider_route_hint)
                .post(provider_route_preview)
                .options(cors_preflight),
        )
        .route("/api/provider-adapter-contract", get(provider_adapter))
        .route(
            "/api/provider-adapter/candidates",
            get(provider_adapter_candidate_catalog),
        )
        .route(
            "/api/provider-adapter/gate-check",
            post(provider_adapter_gate_check_preview).options(cors_preflight),
        )
        .route(
            "/api/provider-adapter/dry-run",
            post(provider_adapter_dry_run_preview).options(cors_preflight),
        )
        .route(
            "/api/runs",
            get(list_runs).post(create_run).options(cors_preflight),
        )
        .route("/api/runs/{run_id}", get(get_run))
        .route("/api/runs/{run_id}/graph", get(get_run_graph))
        .route("/api/runs/{run_id}/events", get(get_run_events))
        .route("/api/runs/{run_id}/event-log", get(get_run_event_log))
        .route("/api/runs/{run_id}/event-replay", get(get_run_event_replay))
        .route(
            "/api/runs/{run_id}/worker-result-dry-run",
            post(run_worker_result_dry_run).options(cors_preflight),
        )
        .route(
            "/api/runs/{run_id}/result-snapshot-readiness",
            post(run_result_snapshot_readiness).options(cors_preflight),
        )
        .route(
            "/api/runs/{run_id}/worker-result-commit-intent",
            post(run_worker_result_commit_intent).options(cors_preflight),
        )
        .route(
            "/api/runs/{run_id}/review-comparison",
            get(get_run_review_comparison),
        )
        .route(
            "/api/execution-jobs",
            get(list_execution_jobs)
                .post(create_execution_job)
                .options(cors_preflight),
        )
        .route("/api/execution-jobs/{job_id}", get(get_execution_job))
        .route(
            "/api/execution-jobs/{job_id}/work-order",
            get(get_execution_work_order),
        )
        .route(
            "/api/execution-jobs/{job_id}/handoff-preview",
            get(get_execution_handoff_preview),
        )
        .route(
            "/api/execution-jobs/{job_id}/intent-preview",
            get(get_execution_intent_preview),
        )
        .route(
            "/api/execution-intent-store-boundary",
            get(execution_intent_store),
        )
        .route("/api/execution-lifecycle", get(execution_lifecycle))
        .route("/api/worker-lease-boundary", get(worker_lease))
        .route("/api/storage-plan", get(storage_plan))
        .layer(middleware::from_fn(add_cors_headers))
        .with_state(AppState::open_default().expect("open pro stores"))
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

async fn workspace_access() -> Json<WorkspaceAccessContext> {
    Json(workspace_access_context())
}

async fn workspace_access_gate_decision(
    Json(request): Json<WorkspaceAccessGateRequest>,
) -> Json<WorkspaceAccessGateDecision> {
    Json(workspace_access_gate(request))
}

async fn execution_readiness(
    Json(request): Json<ExecutionReadinessRequest>,
) -> Json<ExecutionReadinessDecision> {
    Json(execution_readiness_gate(request))
}

async fn execution_admission_check(
    Json(request): Json<ExecutionAdmissionRequest>,
) -> Json<ExecutionAdmissionDecision> {
    Json(execution_admission(request))
}

async fn execution_intent_create_request(
    Json(request): Json<ExecutionAdmissionRequest>,
) -> Json<ExecutionIntentCreateRequestPreview> {
    Json(execution_intent_create_request_preview(request))
}

async fn execution_intent_durability_check(
    Json(request): Json<ExecutionAdmissionRequest>,
) -> Json<ExecutionIntentDurabilityGate> {
    Json(execution_intent_durability_gate(request))
}

async fn execution_preflight() -> Json<ExecutionPreflightBoundary> {
    Json(execution_preflight_boundary())
}

async fn credential_vault() -> Json<CredentialVaultBoundary> {
    Json(credential_vault_boundary())
}

async fn quota_ledger() -> Json<QuotaLedgerBoundary> {
    Json(quota_ledger_boundary())
}

async fn result_commit() -> Json<ResultCommitBoundary> {
    Json(result_commit_boundary())
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

async fn provider_adapter() -> Json<ProviderAdapterContract> {
    Json(provider_adapter_contract())
}

async fn provider_adapter_candidate_catalog() -> Json<ProviderAdapterCandidateCatalog> {
    Json(provider_adapter_candidates())
}

async fn provider_adapter_gate_check_preview(
    Json(request): Json<ProviderAdapterGateCheckRequest>,
) -> Json<ProviderAdapterGateCheckResult> {
    Json(provider_adapter_gate_check(request))
}

async fn provider_adapter_dry_run_preview(
    Json(request): Json<ProviderAdapterDryRunRequest>,
) -> Result<Json<ProviderAdapterDryRunResult>, ApiError> {
    provider_adapter_dry_run(request)
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
    state
        .event_store
        .ensure_run_events(&run)
        .map_err(event_store_error)?;

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

async fn get_run_events(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<RunEventTimeline>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    Ok(Json(run_event_timeline(&run)))
}

async fn get_run_event_log(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<Vec<EventStoreEntry>>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    state
        .event_store
        .list_run_events(&run)
        .map(Json)
        .map_err(event_store_error)
}

async fn get_run_event_replay(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<EventStoreReplay>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    state
        .event_store
        .ensure_run_events(&run)
        .map(Json)
        .map_err(event_store_error)
}

async fn run_worker_result_dry_run(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<WorkerResultDryRun>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    state
        .event_store
        .worker_result_dry_run(&run)
        .map(Json)
        .map_err(event_store_error)
}

async fn run_result_snapshot_readiness(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<ResultSnapshotReadiness>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    state
        .event_store
        .result_snapshot_readiness(&run)
        .map(Json)
        .map_err(event_store_error)
}

async fn run_worker_result_commit_intent(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<WorkerResultCommitIntent>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    state
        .event_store
        .worker_result_commit_intent(&run)
        .map(Json)
        .map_err(event_store_error)
}

async fn get_run_review_comparison(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<RunReviewComparison>, ApiError> {
    let run = state
        .run_store
        .get_run(&run_id)
        .ok_or_else(|| not_found(run_id))?;
    Ok(Json(run_review_comparison(&run)))
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

async fn get_execution_work_order(
    State(state): State<AppState>,
    Path(job_id): Path<String>,
) -> Result<Json<ExecutionWorkOrder>, ApiError> {
    state
        .execution_queue
        .get_work_order(&job_id)
        .map(Json)
        .ok_or_else(|| job_not_found(job_id))
}

async fn get_execution_handoff_preview(
    State(state): State<AppState>,
    Path(job_id): Path<String>,
) -> Result<Json<ExecutionHandoffPreview>, ApiError> {
    state
        .execution_queue
        .get_handoff_preview(&job_id)
        .map(Json)
        .ok_or_else(|| job_not_found(job_id))
}

async fn get_execution_intent_preview(
    State(state): State<AppState>,
    Path(job_id): Path<String>,
) -> Result<Json<ExecutionIntentPreview>, ApiError> {
    state
        .execution_queue
        .get_intent_preview(&job_id)
        .map(Json)
        .ok_or_else(|| job_not_found(job_id))
}

async fn execution_intent_store() -> Json<ExecutionIntentStoreBoundary> {
    Json(execution_intent_store_boundary())
}

async fn execution_lifecycle() -> Json<ExecutionLifecycleSpec> {
    Json(execution_lifecycle_spec())
}

async fn worker_lease() -> Json<WorkerLeaseBoundary> {
    Json(worker_lease_boundary())
}

async fn storage_plan() -> Json<HostedStorageMigrationPlan> {
    Json(hosted_storage_migration_plan())
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

fn event_store_error(error: EventStoreError) -> ApiError {
    internal_error(error.to_string())
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
    use retrocause_pro_domain::WorkspaceAction;
    use std::path::PathBuf;

    impl AppState {
        fn seeded() -> Self {
            Self {
                run_store: FileRunStore::open(temp_store_path())
                    .expect("test run store should open"),
                event_store: FileEventStore::open(temp_event_store_path())
                    .expect("test event store should open"),
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
    async fn workspace_access_exposes_non_enforcing_preview_context() {
        let payload = workspace_access().await.0;

        assert_eq!(payload.workspace_id, "workspace_demo");
        assert!(!payload.safeguards.is_empty());
        assert!(
            payload
                .safeguards
                .contains(&"no_sessions_or_cookies_issued".to_string())
        );
        assert!(payload.permissions.iter().any(|permission| {
            permission.id == "execute_provider_calls"
                && permission.status
                    == retrocause_pro_domain::WorkspacePermissionStatus::RequiresAuthLater
        }));
    }

    #[tokio::test]
    async fn workspace_access_gate_allows_preview_and_denies_live_actions() {
        let preview = workspace_access_gate_decision(Json(WorkspaceAccessGateRequest {
            workspace_id: Some("workspace_demo".to_string()),
            action: WorkspaceAction::InspectKnowledgeGraph,
            resource: Some("run_semiconductor_controls_001".to_string()),
        }))
        .await
        .0;

        assert_eq!(preview.workspace_id, "workspace_demo");
        assert!(preview.allowed);
        assert!(preview.preview_only);
        assert!(!preview.requires_auth);
        assert_eq!(
            preview.matched_permission_id.as_deref(),
            Some("inspect_knowledge_graph")
        );

        let live = workspace_access_gate_decision(Json(WorkspaceAccessGateRequest {
            workspace_id: Some("workspace_demo".to_string()),
            action: WorkspaceAction::ExecuteProviderCalls,
            resource: Some("ofoxai_model_candidate".to_string()),
        }))
        .await
        .0;

        assert!(!live.allowed);
        assert!(live.requires_auth);
        assert!(live.requires_worker);
        assert!(
            live.blocking_reasons
                .contains(&"credential_vault_handle_required".to_string())
        );
        let combined = format!(
            "{} {:?} {:?}",
            live.actor_id, live.blocking_reasons, live.safeguards
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
    }

    #[tokio::test]
    async fn execution_readiness_denies_live_execution_with_composed_blockers() {
        let payload = execution_readiness(Json(ExecutionReadinessRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            candidate_id: Some("ofoxai_model_candidate".to_string()),
            dry_run_observed: true,
            auth_context_observed: true,
            quota_owner_confirmed: true,
            event_timeline_observed: true,
            work_order_observed: true,
            commit_intent_observed: true,
        }))
        .await
        .0;

        assert_eq!(payload.workspace_id, "workspace_demo");
        assert!(!payload.execution_allowed);
        assert!(matches!(
            payload.status,
            retrocause_pro_provider_routing::ExecutionReadinessStatus::DeniedRequiresHostedGates
        ));
        assert!(!payload.workspace_gate.allowed);
        assert!(!payload.provider_gate.execution_allowed);
        assert!(!payload.worker_commit_gate.allowed);
        assert!(!payload.snapshot_persistence_gate.allowed);
        assert!(
            payload
                .preview_observations
                .iter()
                .all(|item| item.observed)
        );
        assert!(
            payload
                .blocking_reasons
                .contains(&"provider_gate:workspace_auth_enforced".to_string())
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_credential_reads".to_string())
        );
        let combined = format!(
            "{:?} {:?} {:?}",
            payload.blocking_reasons, payload.safeguards, payload.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
    }

    #[tokio::test]
    async fn execution_admission_returns_server_computed_denial_payload() {
        let payload = execution_admission_check(Json(ExecutionAdmissionRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            job_id: Some("job_local_000000".to_string()),
            action: Some(WorkspaceAction::ExecuteProviderCalls),
        }))
        .await
        .0;

        assert!(matches!(
            payload.status,
            retrocause_pro_domain::ExecutionAdmissionStatus::DeniedRequiresHostedGates
        ));
        assert!(!payload.admitted);
        assert!(!payload.execution_allowed);
        assert!(!payload.admission_token_issued);
        assert!(!payload.vault_handle_issued);
        assert!(!payload.quota_reserved);
        assert!(!payload.secret_values_returned);
        assert!(!payload.ledger_mutation_enabled);
        assert!(payload.gates.iter().any(|gate| gate.id == "tenant_auth"));
        assert!(payload.gates.iter().any(|gate| gate.id == "vault_handle"));
        assert!(
            payload
                .gates
                .iter()
                .any(|gate| gate.id == "quota_reservation")
        );
        assert!(
            payload
                .blocking_reasons
                .contains(&"quota_reservation_not_created".to_string())
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_admission_token_or_capability_issued".to_string())
        );

        let combined = format!(
            "{:?} {:?} {:?} {}",
            payload.gates, payload.blocking_reasons, payload.safeguards, payload.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
    }

    #[tokio::test]
    async fn execution_intent_create_request_returns_rejected_preview_payload() {
        let payload = execution_intent_create_request(Json(ExecutionAdmissionRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            job_id: Some("job_local_000000".to_string()),
            action: Some(WorkspaceAction::ExecuteProviderCalls),
        }))
        .await
        .0;

        assert_eq!(payload.workspace_id, "workspace_demo");
        assert!(matches!(
            payload.status,
            retrocause_pro_queue::ExecutionIntentCreateRequestStatus::RejectedRequiresAdmissionAndStore
        ));
        assert!(!payload.create_request_allowed);
        assert!(!payload.intent_persistence_allowed);
        assert!(!payload.execution_allowed);
        assert!(!payload.durable_intent_id_issued);
        assert!(payload.intent_id_preview.is_none());
        assert!(!payload.admission.admitted);
        assert!(!payload.admission.admission_token_issued);
        assert!(!payload.admission.vault_handle_issued);
        assert!(!payload.admission.quota_reserved);
        assert!(!payload.intent_store.intent_store_connected);
        assert!(!payload.intent_store.persistence_allowed);
        assert!(!payload.worker_lease_boundary.lease_store_connected);
        assert!(
            payload
                .request_fields
                .iter()
                .any(|field| field.id == "quota_reservation" && !field.accepted_now)
        );
        assert!(payload.write_plan.iter().all(|step| !step.allowed_now));
        assert!(
            payload
                .blocking_reasons
                .contains(&"execution_admission_denied".to_string())
        );
        assert!(
            payload
                .blocking_reasons
                .contains(&"intent_store_not_connected".to_string())
        );
        assert!(
            payload
                .safeguards
                .contains(&"create_request_preview_only_no_persistence".to_string())
        );
        assert!(payload.idempotency_key_preview.contains("job_local_000000"));

        let combined = format!(
            "{:?} {:?} {:?} {:?} {} {}",
            payload.request_fields,
            payload.write_plan,
            payload.blocking_reasons,
            payload.safeguards,
            payload.idempotency_key_preview,
            payload.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
        assert!(!combined.contains("token:"));
    }

    #[tokio::test]
    async fn execution_intent_durability_gate_returns_rejected_preview_payload() {
        let payload = execution_intent_durability_check(Json(ExecutionAdmissionRequest {
            workspace_id: Some("workspace_demo".to_string()),
            run_id: Some("run_semiconductor_controls_001".to_string()),
            job_id: Some("job_local_000000".to_string()),
            action: Some(WorkspaceAction::ExecuteProviderCalls),
        }))
        .await
        .0;

        assert_eq!(payload.workspace_id, "workspace_demo");
        assert!(matches!(
            payload.status,
            retrocause_pro_queue::ExecutionIntentDurabilityGateStatus::RejectedMissingHostedDurability
        ));
        assert!(!payload.durability_allowed);
        assert!(!payload.hosted_store_connection_allowed);
        assert!(!payload.execution_allowed);
        assert!(!payload.create_request.create_request_allowed);
        assert!(!payload.create_request.intent_persistence_allowed);
        assert!(!payload.result_commit_boundary.event_store_connected);
        assert!(payload.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "idempotency_preview_scoped" && prerequisite.satisfied
        }));
        assert!(payload.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "tenant_auth_admitted" && !prerequisite.satisfied
        }));
        assert!(payload.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "quota_reserved" && !prerequisite.satisfied
        }));
        assert!(payload.prerequisites.iter().any(|prerequisite| {
            prerequisite.id == "result_event_store_connected" && !prerequisite.satisfied
        }));
        assert!(
            payload
                .blocking_reasons
                .contains(&"durability_gate_missing_intent_store_connected".to_string())
        );
        assert!(
            payload
                .blocking_reasons
                .contains(&"result_commit_writes_disabled".to_string())
        );
        assert!(
            payload
                .safeguards
                .contains(&"durability_gate_preview_only_no_store_connection".to_string())
        );

        let combined = format!(
            "{:?} {:?} {:?} {}",
            payload.prerequisites,
            payload.blocking_reasons,
            payload.safeguards,
            payload.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
        assert!(!combined.contains("token:"));
    }

    #[tokio::test]
    async fn execution_preflight_exposes_keyless_hosted_prerequisite_boundary() {
        let payload = execution_preflight().await.0;

        assert!(matches!(
            payload.status,
            retrocause_pro_domain::ExecutionPreflightStatus::DeniedRequiresHostedPrerequisites
        ));
        assert!(!payload.execution_allowed);
        assert!(!payload.auth_enforced);
        assert!(!payload.credential_vault_handle_issued);
        assert!(!payload.quota_reservation_allowed);
        assert!(!payload.worker_handoff_allowed);
        assert!(!payload.secret_values_returned);
        assert!(!payload.ledger_mutation_enabled);
        assert!(
            payload
                .requirements
                .iter()
                .any(|item| item.id == "tenant_auth_context")
        );
        assert!(
            payload
                .requirements
                .iter()
                .any(|item| item.id == "credential_vault_handle")
        );
        assert!(
            payload
                .requirements
                .iter()
                .any(|item| item.id == "quota_reservation")
        );
        assert!(payload.handoff_rules.iter().all(|rule| !rule.allowed_now));
        assert!(
            payload
                .blocking_reasons
                .contains(&"quota_reservation_required".to_string())
        );
        let combined = format!(
            "{:?} {:?} {:?}",
            payload.requirements, payload.handoff_rules, payload.safeguards
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
    }

    #[tokio::test]
    async fn credential_vault_exposes_keyless_boundary_preview() {
        let payload = credential_vault().await.0;

        assert!(!payload.connections_enabled);
        assert!(!payload.secret_values_returned);
        assert!(
            payload
                .credential_classes
                .iter()
                .any(|item| item.id == "managed_model_credentials")
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_secret_values_in_requests_or_responses".to_string())
        );
    }

    #[tokio::test]
    async fn quota_ledger_exposes_non_billing_boundary_preview() {
        let payload = quota_ledger().await.0;

        assert!(!payload.ledger_mutation_enabled);
        assert!(!payload.payment_provider_connected);
        assert!(
            payload
                .quota_lanes
                .iter()
                .any(|item| item.id == "managed_model_pool" && !item.billable_now)
        );
        assert!(
            payload
                .metering_rules
                .iter()
                .any(|rule| rule.id == "no_billable_units_in_preview" && !rule.billable_now)
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_billing_mutation_in_this_slice".to_string())
        );
    }

    #[tokio::test]
    async fn result_commit_exposes_non_durable_boundary_preview() {
        let payload = result_commit().await.0;

        assert!(!payload.event_store_connected);
        assert!(!payload.commit_writes_enabled);
        assert!(!payload.partial_reconciliation_enabled);
        assert!(
            payload
                .commit_stages
                .iter()
                .any(|item| item.id == "commit_evidence_events")
        );
        assert!(
            payload
                .event_write_rules
                .iter()
                .any(|rule| rule.id == "api_routes_cannot_write_events" && !rule.allowed_now)
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_event_store_write_in_this_slice".to_string())
        );
    }

    #[tokio::test]
    async fn execution_lifecycle_exposes_non_executing_worker_contract() {
        let payload = execution_lifecycle().await.0;

        assert!(!payload.execution_allowed);
        assert!(
            payload
                .stages
                .iter()
                .any(|stage| stage.id == "executing_provider_calls")
        );
        assert!(
            payload
                .failure_states
                .iter()
                .any(|failure| failure.id == "credential_unavailable")
        );
        assert!(
            payload
                .transition_guards
                .contains(&"worker_reads_credentials_from_vault_only".to_string())
        );
    }

    #[tokio::test]
    async fn worker_lease_exposes_non_executing_retry_boundary() {
        let payload = worker_lease().await.0;

        assert!(!payload.lease_store_connected);
        assert!(!payload.retry_scheduler_enabled);
        assert!(!payload.execution_allowed);
        assert!(
            payload
                .lease_rules
                .iter()
                .any(|rule| rule.id == "routes_cannot_claim_work")
        );
        assert!(
            payload
                .retry_rules
                .iter()
                .any(|rule| rule.id == "provider_rate_limited_retry"
                    && rule.preserves_partial_results)
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_worker_process_started".to_string())
        );
    }

    #[tokio::test]
    async fn storage_plan_exposes_hosted_migration_boundaries_without_connections() {
        let payload = storage_plan().await.0;

        assert!(!payload.connections_enabled);
        assert!(
            payload
                .components
                .iter()
                .any(|component| component.id == "postgres_usage_ledger")
        );
        assert!(
            payload
                .components
                .iter()
                .any(|component| component.id == "redis_execution_queue")
        );
        assert!(
            payload
                .worker_ownership
                .iter()
                .any(|boundary| boundary.id == "routes_do_not_execute_jobs")
        );
        assert!(
            payload
                .non_goals
                .contains(&"no_database_connection_in_this_slice".to_string())
        );
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
    async fn provider_adapter_contract_exposes_dry_non_executing_semantics() {
        let payload = provider_adapter().await.0;

        assert!(!payload.execution_allowed);
        assert!(
            payload
                .request_fields
                .iter()
                .any(|field| field.id == "provider_lane_id")
        );
        assert!(
            payload
                .degradation_states
                .iter()
                .any(|state| state.id == "provider_rate_limited")
        );
        assert!(
            payload
                .partial_result_rules
                .contains(&"preserve_successful_evidence_before_retry".to_string())
        );
    }

    #[tokio::test]
    async fn provider_adapter_dry_run_exposes_zero_billable_preview() {
        let payload = provider_adapter_dry_run_preview(Json(ProviderAdapterDryRunRequest {
            workspace_id: Some("workspace_test".to_string()),
            query: "Why did AI infrastructure names move?".to_string(),
            provider_lane_id: Some("uploaded_evidence_lane".to_string()),
            source_policy: None,
        }))
        .await
        .expect("valid dry-run request")
        .0;

        assert_eq!(payload.workspace_id, "workspace_test");
        assert_eq!(payload.provider_lane_id, "uploaded_evidence_lane");
        assert!(!payload.execution_allowed);
        assert_eq!(payload.usage_ledger_preview[0].billable_units, 0);
        assert!(
            payload
                .warnings
                .contains(&"dry_run_only_no_provider_calls".to_string())
        );
    }

    #[tokio::test]
    async fn provider_adapter_candidates_expose_gated_ofoxai_candidate() {
        let payload = provider_adapter_candidate_catalog().await.0;

        assert!(!payload.execution_allowed);
        assert!(payload.candidates.iter().any(|candidate| {
            candidate.id == "ofoxai_model_candidate"
                && candidate.lane_id == "managed_model_pool"
                && !candidate.execution_allowed
        }));
        assert!(
            payload
                .safeguards
                .contains(&"worker_execution_disabled".to_string())
        );
    }

    #[tokio::test]
    async fn provider_adapter_gate_check_denies_live_execution() {
        let payload = provider_adapter_gate_check_preview(Json(ProviderAdapterGateCheckRequest {
            workspace_id: Some("workspace_test".to_string()),
            candidate_id: Some("ofoxai_model_candidate".to_string()),
            dry_run_observed: true,
            auth_context_observed: true,
            quota_owner_confirmed: true,
            event_timeline_observed: true,
        }))
        .await
        .0;

        assert_eq!(payload.candidate_id, "ofoxai_model_candidate");
        assert!(!payload.execution_allowed);
        assert!(
            payload
                .blocking_reasons
                .contains(&"workspace_auth_enforced".to_string())
        );
        assert!(
            payload
                .warnings
                .contains(&"live_provider_execution_denied".to_string())
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
    async fn run_events_payload_is_derived_from_requested_run() {
        let payload = get_run_events(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert_eq!(payload.current_status, RunStatus::ReadyForReview);
        assert!(!payload.durable);
        assert!(!payload.events.is_empty());
        assert!(
            payload
                .safeguards
                .contains(&"no_event_store_connection_in_this_slice".to_string())
        );
    }

    #[tokio::test]
    async fn event_log_payload_is_persisted_for_requested_run() {
        let payload = get_run_event_log(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert!(!payload.is_empty());
        assert_eq!(payload[0].run_id, "run_semiconductor_controls_001");
        assert_eq!(
            payload[0].source,
            retrocause_pro_event_store::EventStoreEntrySource::DerivedRunTimelinePersistedLocally
        );
    }

    #[tokio::test]
    async fn event_replay_payload_is_local_and_durable() {
        let payload = get_run_event_replay(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert!(payload.durable);
        assert!(payload.event_count >= 3);
        assert!(
            payload
                .safeguards
                .contains(&"local_file_event_store_only".to_string())
        );
    }

    #[tokio::test]
    async fn worker_result_dry_run_uses_replay_without_execution_or_writes() {
        let payload = run_worker_result_dry_run(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert!(!payload.execution_allowed);
        assert!(!payload.provider_execution_allowed);
        assert!(!payload.result_commit_allowed);
        assert!(!payload.result_event_write_allowed);
        assert!(payload.replay_event_count >= 3);
        assert!(
            payload
                .proposed_steps
                .iter()
                .any(|step| step.id == "commit_result_events" && !step.writes_now)
        );
        assert!(
            payload
                .safeguards
                .contains(&"uses_local_event_replay_as_input".to_string())
        );
    }

    #[tokio::test]
    async fn result_snapshot_readiness_blocks_persistence_until_hosted_gates_exist() {
        let payload = run_result_snapshot_readiness(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert!(!payload.snapshot_persistence_allowed);
        assert!(!payload.result_event_write_allowed);
        assert!(!payload.provider_execution_allowed);
        assert!(payload.worker_commit_required);
        assert!(payload.replay_event_count >= 3);
        assert!(!payload.proposed_snapshot.persisted);
        assert!(!payload.proposed_snapshot.publishable);
        assert!(
            payload
                .readiness_checks
                .iter()
                .any(|check| check.id == "tenant_auth_enforced"
                    && check.blocking_snapshot_persistence)
        );
        assert!(
            payload
                .safeguards
                .contains(&"derives_from_worker_result_dry_run".to_string())
        );
    }

    #[tokio::test]
    async fn worker_result_commit_intent_is_rejected_until_hosted_gates_exist() {
        let payload = run_worker_result_commit_intent(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert!(!payload.commit_allowed);
        assert!(!payload.result_event_write_allowed);
        assert!(!payload.snapshot_persistence_allowed);
        assert!(!payload.provider_execution_allowed);
        assert!(payload.idempotency_key_required);
        assert!(
            payload
                .idempotency_key_preview
                .contains("run_semiconductor_controls_001")
        );
        assert!(payload.worker_lease_required);
        assert!(
            payload
                .blocking_checks
                .iter()
                .any(|check| { check.id == "durable_worker_commit_ready" })
        );
        assert!(
            payload
                .event_writes
                .iter()
                .all(|write| { !write.allowed_now && write.idempotency_required })
        );
        assert!(
            payload
                .safeguards
                .contains(&"derived_from_result_snapshot_readiness".to_string())
        );
    }

    #[tokio::test]
    async fn review_comparison_payload_is_derived_from_requested_run() {
        let payload = get_run_review_comparison(
            State(AppState::seeded()),
            Path("run_semiconductor_controls_001".to_string()),
        )
        .await
        .expect("known sample run")
        .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert_eq!(
            payload.baseline_run_id,
            "run_semiconductor_controls_001_previous_checkpoint"
        );
        assert_eq!(payload.evidence_summary.added, 1);
        assert_eq!(payload.challenge_summary.added, 1);
        assert!(!payload.evidence_deltas.is_empty());
        assert!(
            payload
                .safeguards
                .contains(&"no_provider_calls_or_credential_reads".to_string())
        );
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

        let graph = get_run_graph(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run graph should be readable")
            .0;
        assert_eq!(graph.run_id, created.id);
        assert_eq!(graph.graph.nodes.len(), 3);

        let events = get_run_events(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run events should be readable")
            .0;
        assert_eq!(events.run_id, created.id);
        assert_eq!(events.current_status, RunStatus::Queued);
        assert_eq!(events.events.len(), 1);

        let comparison = get_run_review_comparison(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run comparison should be readable")
            .0;
        assert_eq!(comparison.run_id, created.id);
        assert_eq!(comparison.evidence_summary.added, 1);

        let replay = get_run_event_replay(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run replay should be readable")
            .0;
        assert_eq!(replay.run_id, created.id);
        assert_eq!(replay.event_count, 1);

        let dry_run = run_worker_result_dry_run(State(state.clone()), Path(created.id.clone()))
            .await
            .expect("created run worker result dry-run should be readable")
            .0;
        assert_eq!(dry_run.run_id, created.id);
        assert_eq!(dry_run.replay_event_count, 1);
        assert!(!dry_run.result_event_write_allowed);

        let readiness =
            run_result_snapshot_readiness(State(state.clone()), Path(created.id.clone()))
                .await
                .expect("created run result snapshot readiness should be readable")
                .0;
        assert_eq!(readiness.run_id, created.id);
        assert_eq!(readiness.replay_event_count, 1);
        assert!(!readiness.snapshot_persistence_allowed);

        let intent = run_worker_result_commit_intent(State(state), Path(created.id.clone()))
            .await
            .expect("created run worker result commit intent should be readable")
            .0;
        assert_eq!(intent.run_id, created.id);
        assert!(!intent.commit_allowed);
        assert!(intent.idempotency_key_required);
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
    async fn execution_job_work_order_exposes_safeguarded_contract() {
        let state = AppState::seeded();

        let (_, Json(created)) = create_execution_job(
            State(state.clone()),
            Json(RoutingPreviewRequest {
                workspace_id: Some("workspace_executor".to_string()),
                query: "Why should workers wait?".to_string(),
                scenario: None,
                source_policy: None,
            }),
        )
        .await
        .expect("valid request should create preview job");

        let work_order = get_execution_work_order(State(state), Path(created.id.clone()))
            .await
            .expect("created job should expose work order")
            .0;

        assert_eq!(work_order.job_id, created.id);
        assert!(!work_order.execution_allowed);
        assert_eq!(
            work_order.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );
        assert!(
            work_order
                .safeguards
                .contains(&"provider_execution_disabled".to_string())
        );
    }

    #[tokio::test]
    async fn execution_handoff_preview_composes_preflight_with_work_order() {
        let state = AppState::seeded();

        let (_, Json(created)) = create_execution_job(
            State(state.clone()),
            Json(RoutingPreviewRequest {
                workspace_id: Some("workspace_executor".to_string()),
                query: "Why should handoff stay denied?".to_string(),
                scenario: None,
                source_policy: None,
            }),
        )
        .await
        .expect("valid request should create preview job");

        let preview = get_execution_handoff_preview(State(state), Path(created.id.clone()))
            .await
            .expect("created job should expose handoff preview")
            .0;

        assert_eq!(preview.job_id, created.id);
        assert_eq!(preview.work_order.job_id, created.id);
        assert!(!preview.execution_allowed);
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

    #[tokio::test]
    async fn execution_intent_preview_composes_handoff_and_lease_boundaries() {
        let state = AppState::seeded();

        let (_, Json(created)) = create_execution_job(
            State(state.clone()),
            Json(RoutingPreviewRequest {
                workspace_id: Some("workspace_executor".to_string()),
                query: "Why should intent creation stay rejected?".to_string(),
                scenario: None,
                source_policy: None,
            }),
        )
        .await
        .expect("valid request should create preview job");

        let preview = get_execution_intent_preview(State(state), Path(created.id.clone()))
            .await
            .expect("created job should expose intent preview")
            .0;

        assert_eq!(preview.job_id, created.id);
        assert_eq!(preview.handoff.job_id, created.id);
        assert!(!preview.intent_creation_allowed);
        assert!(!preview.execution_allowed);
        assert!(!preview.worker_lease_boundary.lease_store_connected);
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

    #[tokio::test]
    async fn execution_intent_store_boundary_exposes_disabled_persistence_rules() {
        let payload = execution_intent_store().await.0;

        assert!(!payload.intent_store_connected);
        assert!(!payload.persistence_allowed);
        assert!(payload.replay_required_before_claim);
        assert!(
            payload
                .transition_rules
                .iter()
                .any(|rule| { rule.id == "accepted_to_ready_for_lease" && !rule.allowed_now })
        );
        assert!(
            payload
                .idempotency_rules
                .iter()
                .any(|rule| rule.id == "intent_create_key")
        );
        assert!(
            payload
                .retention_rules
                .iter()
                .any(|rule| rule.id == "lease_rows")
        );
        assert!(
            payload
                .safeguards
                .contains(&"no_intent_persistence".to_string())
        );

        let combined = format!(
            "{:?} {:?} {:?} {}",
            payload.transition_rules,
            payload.idempotency_rules,
            payload.safeguards,
            payload.next_required_step
        )
        .to_lowercase();
        assert!(!combined.contains("sk-"));
        assert!(!combined.contains("api_key"));
        assert!(!combined.contains("bearer "));
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

    fn temp_event_store_path() -> PathBuf {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("system clock should be after unix epoch")
            .as_nanos();

        std::env::temp_dir().join(format!(
            "retrocause-pro-api-event-store-{}-{nanos}.json",
            std::process::id()
        ))
    }
}
