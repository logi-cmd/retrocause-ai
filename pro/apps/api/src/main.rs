use axum::{Json, Router, routing::get};
use retrocause_pro_domain::sample_run;
use serde::Serialize;

#[derive(Serialize)]
struct HealthPayload {
    service: &'static str,
    status: &'static str,
}

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/healthz", get(health))
        .route("/api/graph/seed", get(seed_graph))
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

async fn seed_graph() -> Json<retrocause_pro_domain::RunSeed> {
    Json(sample_run())
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

    #[tokio::test]
    async fn health_payload_is_ok() {
        let payload = health().await.0;
        assert_eq!(payload.service, "retrocause-pro-api");
        assert_eq!(payload.status, "ok");
    }
}
