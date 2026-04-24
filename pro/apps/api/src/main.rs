use axum::{Json, Router, extract::Path, http::StatusCode, routing::get};
use retrocause_pro_domain::{
    KnowledgeGraph, ProRun, RunStatus, RunSummary, sample_run, sample_run_by_id,
    sample_run_summaries,
};
use serde::Serialize;

#[derive(Serialize)]
struct HealthPayload {
    service: &'static str,
    status: &'static str,
}

#[derive(Debug, Serialize)]
struct ErrorPayload {
    error: &'static str,
    run_id: String,
}

#[derive(Serialize)]
struct GraphPayload {
    run_id: &'static str,
    title: &'static str,
    status: RunStatus,
    confidence: f32,
    graph: KnowledgeGraph,
}

type ApiError = (StatusCode, Json<ErrorPayload>);

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/healthz", get(health))
        .route("/api/graph/seed", get(seed_graph))
        .route("/api/runs", get(list_runs))
        .route("/api/runs/{run_id}", get(get_run))
        .route("/api/runs/{run_id}/graph", get(get_run_graph))
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

async fn seed_graph() -> Json<ProRun> {
    Json(sample_run())
}

async fn list_runs() -> Json<Vec<RunSummary>> {
    Json(sample_run_summaries())
}

async fn get_run(Path(run_id): Path<String>) -> Result<Json<ProRun>, ApiError> {
    sample_run_by_id(&run_id)
        .map(Json)
        .ok_or_else(|| not_found(run_id))
}

async fn get_run_graph(Path(run_id): Path<String>) -> Result<Json<GraphPayload>, ApiError> {
    let run = sample_run_by_id(&run_id).ok_or_else(|| not_found(run_id))?;
    Ok(Json(GraphPayload {
        run_id: run.id,
        title: run.title,
        status: run.status,
        confidence: run.confidence,
        graph: run.graph,
    }))
}

fn not_found(run_id: String) -> ApiError {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorPayload {
            error: "run_not_found",
            run_id,
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
        let runs = list_runs().await.0;

        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].id, "run_semiconductor_controls_001");
        assert!(runs[0].node_count > 0);
        assert!(runs[0].edge_count > 0);
    }

    #[tokio::test]
    async fn graph_payload_is_scoped_to_requested_run() {
        let payload = get_run_graph(Path("run_semiconductor_controls_001".to_string()))
            .await
            .expect("known sample run")
            .0;

        assert_eq!(payload.run_id, "run_semiconductor_controls_001");
        assert_eq!(payload.graph.nodes.len(), sample_run().graph.nodes.len());
    }

    #[tokio::test]
    async fn unknown_run_returns_404_payload() {
        let response = get_run(Path("missing".to_string()))
            .await
            .expect_err("missing run should return not found")
            .into_response();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }
}
