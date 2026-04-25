use axum::{
    Router,
    response::{Html, IntoResponse},
    routing::get,
};
use maud::{DOCTYPE, Markup, PreEscaped, html};
use retrocause_pro_domain::{
    ChallengeStatus, EvidenceFreshness, EvidenceStance, GraphEdge, GraphNode, NodeKind, ProRun,
    ProviderQuotaStatus, RunStatus, SourceStatus, StepState, provider_status_snapshot, sample_run,
};

const CANVAS_WIDTH: u16 = 1220;
const CANVAS_HEIGHT: u16 = 720;

fn router() -> Router {
    Router::new().route("/", get(index))
}

async fn index() -> impl IntoResponse {
    Html(render_page(&sample_run(), &api_base()).into_string())
}

fn render_page(run: &ProRun, api_base: &str) -> Markup {
    let seed_json = serde_json::to_string_pretty(run).expect("serialize seed run");
    let provider_snapshot = provider_status_snapshot();
    let provider_json =
        serde_json::to_string_pretty(&provider_snapshot).expect("serialize provider status");
    let selected_node_id = run.graph.nodes.first().map(|node| node.id.as_str());

    html! {
        (DOCTYPE)
        html lang="en" {
            head {
                meta charset="utf-8";
                meta name="viewport" content="width=device-width, initial-scale=1";
                title { "RetroCause Pro" }
                style { (PreEscaped(styles())) }
            }
            body data-api-base=(api_base) {
                main class="field-shell" {
                    section class="graph-field" aria-label="Knowledge graph operating field" {
                        header class="hud hud--top" {
                            div class="brand-lockup" {
                                div class="brand-mark" { "RC" }
                                div {
                                    p class="eyebrow" { "RetroCause Pro" }
                                    h1 { "Causal graph command room" }
                                }
                            }
                            div class="run-state" {
                                span id="run-status" class="state-token state-token--live" { (run_status_label(run.status)) }
                                span id="run-confidence" class="state-token" { "confidence " (percent(run.confidence)) }
                                span id="run-node-count" class="state-token" { (run.graph.nodes.len()) " nodes" }
                                span id="run-edge-count" class="state-token" { (run.graph.edges.len()) " edges" }
                            }
                        }

                        div class="question-band" {
                            p class="eyebrow" { "Run" }
                            h2 id="run-title" { (run.title.as_str()) }
                            p id="run-question" { (run.question.as_str()) }
                            strong id="run-headline" { (run.operator_summary.headline.as_str()) }
                            form id="run-create-form" class="run-console" {
                                label for="run-question-input" { "Ask a new causal question" }
                                textarea id="run-question-input" name="question" rows="3" required="" {
                                    "Why did renewal conversion drop after the pricing launch?"
                                }
                                div class="create-grid" {
                                    input id="run-title-input" name="title" type="text" placeholder="Optional run title";
                                    button type="submit" { "Create run" }
                                }
                                div class="create-grid" {
                                    select id="run-picker" aria-label="Saved Pro runs" {}
                                    button id="load-run-button" type="button" { "Load run" }
                                }
                                p id="run-action-status" class="console-status" { "API: " (api_base) }
                            }
                            div id="workspace-access-panel" class="workspace-access-panel" {
                                article class="access-card access-card--empty" {
                                    div {
                                        strong { "Workspace access preview" }
                                        p { "Access context loads from the Pro API; auth enforcement is not enabled yet." }
                                    }
                                    span class="quota-state quota-state--deferred" { "preview" }
                                }
                            }
                            div class="create-grid" {
                                select id="workspace-access-action" aria-label="Workspace gate action" {
                                    option value="inspect_knowledge_graph" selected="" { "Inspect graph" }
                                    option value="execute_provider_calls" { "Execute provider calls" }
                                    option value="commit_worker_result" { "Commit worker result" }
                                }
                                button id="workspace-access-gate-button" type="button" { "Check access gate" }
                            }
                            p id="workspace-access-gate-status" class="console-status" {
                                "Server gate evaluates preview access before live execution exists."
                            }
                            div id="workspace-access-gate-panel" class="workspace-access-panel" {
                                article class="access-card access-card--empty" {
                                    div {
                                        strong { "Workspace access gate" }
                                        p { "Choose an action to see the server-computed access decision." }
                                    }
                                    span class="quota-state quota-state--deferred" { "idle" }
                                }
                            }
                            div id="run-event-panel" class="run-event-panel" {
                                article class="event-card event-card--empty" {
                                    div {
                                        strong { "Run event timeline" }
                                        p { "Event status vocabulary loads from the Pro API; no durable event store is connected." }
                                    }
                                    span class="quota-state quota-state--deferred" { "derived" }
                                }
                            }
                            div id="event-replay-panel" class="event-replay-panel" {
                                article class="event-card event-card--empty" {
                                    div {
                                        strong { "Event replay" }
                                        p { "Durable local event replay loads from the Pro API; hosted event storage is not connected." }
                                    }
                                    span class="quota-state quota-state--deferred" { "local file" }
                                }
                            }
                            div id="review-comparison-panel" class="review-comparison-panel" {
                                article class="review-card review-card--empty" {
                                    div {
                                        strong { "Review comparison" }
                                        p { "Evidence and challenge deltas load from the Pro API; no historical store is queried yet." }
                                    }
                                    span class="quota-state quota-state--deferred" { "preview" }
                                }
                            }
                        }

                        div class="graph-viewport" {
                            div class="axis-line axis-line--x" {}
                            div class="axis-line axis-line--y" {}
                            svg
                                id="graph-wires"
                                class="graph-wires"
                                viewBox={(format!("0 0 {} {}", CANVAS_WIDTH, CANVAS_HEIGHT))}
                                aria-hidden="true"
                            {
                                @for edge in &run.graph.edges {
                                    (render_edge(run, edge))
                                }
                            }
                            div id="graph-nodes" {
                                @for node in &run.graph.nodes {
                                    (render_node(node, selected_node_id == Some(node.id.as_str())))
                                }
                            }
                        }

                        aside class="graph-inspector" aria-label="Graph inspector" {
                            p class="eyebrow" { "Graph inspector" }
                            div id="node-inspector" {
                                @if let Some(node) = run.graph.nodes.first() {
                                    (render_node_inspector(run, node))
                                } @else {
                                    p { "Select a node to inspect evidence and challenge links." }
                                }
                            }
                        }

                        aside class="focus-docket" aria-label="Focus queue" {
                            p class="eyebrow" { "Focus queue" }
                            ol id="focus-list" {
                                @for step in &run.next_steps {
                                    li {
                                        span { (step_state_label(step.state)) }
                                        strong { (step.title.as_str()) }
                                    }
                                }
                            }
                        }

                        aside class="source-pulse" aria-label="Source pulse" {
                            p class="eyebrow" { "Source pulse" }
                            div id="source-list" {
                                @for source in &run.sources {
                                    (render_source_meter(
                                        source.source.as_str(),
                                        source.status,
                                        source.note.as_str()
                                    ))
                                }
                            }
                        }

                        aside class="quota-console" aria-label="Provider quota routing" {
                            p class="eyebrow" { "Quota routing" }
                            strong id="provider-status-mode" {
                                (provider_status_mode_label(provider_snapshot.mode))
                            }
                            div id="provider-status-list" {
                                @for entry in &provider_snapshot.entries {
                                    (render_provider_status(entry))
                                }
                            }
                            div id="provider-adapter-panel" class="adapter-panel" {
                                article class="quota-meter quota-meter--empty" {
                                    div {
                                        strong { "Adapter contract planned" }
                                        p { "Provider adapter semantics load from the Pro API; provider calls stay disabled." }
                                    }
                                    span class="quota-state quota-state--deferred" { "dry" }
                                }
                            }
                            button id="provider-adapter-dry-run-button" type="button" {
                                "Dry-run adapter"
                            }
                            p id="provider-adapter-dry-run-status" class="console-status" {
                                "Dry-run uses the current run question; provider calls stay disabled."
                            }
                            div id="provider-adapter-dry-run-result" class="adapter-dry-run-result" {
                                article class="quota-meter quota-meter--empty" {
                                    div {
                                        strong { "No adapter dry-run yet" }
                                        p { "Run one to inspect evidence, quota, and degradation shape before live providers exist." }
                                    }
                                    span class="quota-state quota-state--deferred" { "idle" }
                                }
                            }
                            div id="provider-adapter-candidate-panel" class="adapter-candidate-panel" {
                                article class="quota-meter quota-meter--empty" {
                                    div {
                                        strong { "Live adapter candidate" }
                                        p { "Candidate gates load from the Pro API; live provider calls stay denied." }
                                    }
                                    span class="quota-state quota-state--deferred" { "gated" }
                                }
                            }
                            button id="live-adapter-gate-check-button" type="button" {
                                "Check live gates"
                            }
                            p id="live-adapter-gate-check-status" class="console-status" {
                                "Gate check verifies auth, quota, dry-run, and event prerequisites without calling providers."
                            }
                            div id="live-adapter-gate-check-result" class="adapter-gate-check-result" {
                                article class="quota-meter quota-meter--empty" {
                                    div {
                                        strong { "No live gate check yet" }
                                        p { "Run the check to see exactly why live adapter execution is still blocked." }
                                    }
                                    span class="quota-state quota-state--deferred" { "denied" }
                                }
                            }
                            button id="execution-readiness-button" type="button" {
                                "Check execution readiness"
                            }
                            p id="execution-readiness-status" class="console-status" {
                                "Composed readiness checks workspace, provider, worker, and commit gates without executing."
                            }
                            div id="execution-readiness-result" class="execution-readiness-result" {
                                article class="quota-meter quota-meter--empty" {
                                    div {
                                        strong { "Execution readiness" }
                                        p { "Run the check before any future live execution path is enabled." }
                                    }
                                    span class="quota-state quota-state--deferred" { "blocked" }
                                }
                            }
                        }

                        aside class="execution-console" aria-label="Execution queue" {
                            p class="eyebrow" { "Execution queue" }
                            strong id="execution-queue-mode" { "preview-only" }
                            button id="queue-preview-button" type="button" { "Queue preview job" }
                            p id="execution-queue-status" class="console-status" {
                                "Queue uses the current run question; execution stays disabled."
                            }
                            button id="execution-admission-button" type="button" {
                                "Check admission gate"
                            }
                            p id="execution-admission-status" class="console-status" {
                                "Admission composes tenant auth, vault handle, and quota reservation before intent storage."
                            }
                            div id="execution-admission-panel" class="admission-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Execution admission gate" }
                                        p { "Server-side admission payload waits for hosted auth, vault handles, and quota reservations." }
                                    }
                                    span class="quota-state quota-state--deferred" { "denied" }
                                }
                            }
                            div id="execution-job-list" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "No queued preview jobs yet" }
                                        p { "Create one to inspect the routing lane before workers exist." }
                                    }
                                    span class="quota-state quota-state--deferred" { "idle" }
                                }
                            }
                            div id="execution-work-order-detail" class="work-order-detail" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "No work order selected" }
                                        p { "Inspect a queued job to see route steps and execution safeguards." }
                                    }
                                    span class="quota-state quota-state--deferred" { "preview" }
                                }
                            }
                            div id="execution-handoff-panel" class="handoff-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Execution handoff preview" }
                                        p { "Inspect a queued job to see why provider and worker handoff remains blocked." }
                                    }
                                    span class="quota-state quota-state--deferred" { "denied" }
                                }
                            }
                            div id="execution-intent-panel" class="intent-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Execution intent preview" }
                                        p { "Inspect a queued job to see why hosted intent persistence remains blocked." }
                                    }
                                    span class="quota-state quota-state--deferred" { "rejected" }
                                }
                            }
                            div id="execution-intent-store-panel" class="intent-store-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Intent store boundary" }
                                        p { "Durable intent persistence rules load from the Pro API; persistence remains off." }
                                    }
                                    span class="quota-state quota-state--deferred" { "persistence off" }
                                }
                            }
                            div id="execution-lifecycle-panel" class="lifecycle-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Worker lifecycle planned" }
                                        p { "Lifecycle states load from the Pro API; execution remains disabled." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                            div id="execution-preflight-panel" class="preflight-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Pre-execution boundary" }
                                        p { "Hosted auth, vault handles, quota reservations, and worker leases must exist before live calls." }
                                    }
                                    span class="quota-state quota-state--deferred" { "denied" }
                                }
                            }
                            div id="worker-lease-panel" class="lease-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Worker lease boundary" }
                                        p { "Lease and retry rules load from the Pro API; no workers or retries run." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                            div id="result-commit-panel" class="commit-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Result commit boundary" }
                                        p { "Commit and event-store rules load from the Pro API; no durable writes run." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                            button id="worker-result-dry-run-button" type="button" {
                                "Dry-run result commit"
                            }
                            p id="worker-result-dry-run-status" class="console-status" {
                                "Result dry-run uses local replay; worker execution and result writes stay disabled."
                            }
                            div id="worker-result-dry-run-panel" class="commit-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Worker result dry-run" }
                                        p { "Run a preview to inspect proposed result commit steps from local replay." }
                                    }
                                    span class="quota-state quota-state--deferred" { "preview" }
                                }
                            }
                            button id="result-snapshot-readiness-button" type="button" {
                                "Check snapshot gate"
                            }
                            p id="result-snapshot-readiness-status" class="console-status" {
                                "Snapshot readiness checks hosted safety gates without persisting a result."
                            }
                            div id="result-snapshot-readiness-panel" class="commit-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Result snapshot readiness" }
                                        p { "Check why persisted result snapshots are still blocked." }
                                    }
                                    span class="quota-state quota-state--deferred" { "gated" }
                                }
                            }
                            button id="worker-result-commit-intent-button" type="button" {
                                "Prepare commit intent"
                            }
                            p id="worker-result-commit-intent-status" class="console-status" {
                                "Commit intent previews worker-owned writes and idempotency without persisting results."
                            }
                            div id="worker-result-commit-intent-panel" class="commit-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Worker commit intent" }
                                        p { "Prepare a rejected commit intent to inspect idempotency and hosted blockers." }
                                    }
                                    span class="quota-state quota-state--deferred" { "rejected" }
                                }
                            }
                            div id="storage-boundary-panel" class="storage-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Hosted storage plan" }
                                        p { "Store boundaries load from the Pro API; no database connections are open." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                            div id="credential-vault-panel" class="vault-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Credential vault boundary" }
                                        p { "Vault rules load from the Pro API; no credentials are accepted or stored." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                            div id="quota-ledger-panel" class="ledger-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Quota ledger boundary" }
                                        p { "Ledger and billing rules load from the Pro API; no billable usage is written." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
                                }
                            }
                        }

                        aside class="evidence-dock" aria-label="Evidence anchors" {
                            p class="eyebrow" { "Evidence anchors" }
                            p id="review-focus-status" class="console-status" {
                                "Use inspector links to focus evidence and challenge checks."
                            }
                            div id="evidence-list" {
                                @for evidence in run.evidence.iter().take(3) {
                                    article class="evidence-chip" data-evidence-id=(evidence.id.as_str()) {
                                        div {
                                            strong { (evidence.title.as_str()) }
                                            p { (evidence.excerpt.as_str()) }
                                        }
                                        span { (evidence_stance_label(evidence.stance)) " / " (evidence_freshness_label(evidence.freshness)) }
                                    }
                                }
                            }
                            div id="challenge-strip" class="challenge-strip" aria-label="Challenge checks" {
                                @for challenge in &run.challenge_checks {
                                    span data-challenge-id=(challenge.id.as_str()) {
                                        (challenge_status_label(challenge.status)) ": " (challenge.title.as_str())
                                    }
                                }
                            }
                        }

                        footer class="command-deck" {
                            div class="verdict" {
                                p class="eyebrow" { "Current read" }
                                strong id="run-current-read" { (run.operator_summary.current_read.as_str()) }
                                span id="run-caveat" { (run.operator_summary.caveat.as_str()) }
                            }
                            div class="command-clusters" aria-label="Run signals" {
                                span id="command-status" { (run_status_label(run.status)) }
                                span id="command-confidence" { (percent(run.confidence)) " confidence" }
                                span id="command-nodes" { (run.graph.nodes.len()) " nodes tracked" }
                                span id="command-edges" { (run.graph.edges.len()) " causal links" }
                                span id="command-challenges" { (run.challenge_checks.len()) " challenge checks" }
                            }
                        }

                        details class="seed-drawer" {
                            summary { "Run payload" }
                            pre id="payload-json" { (seed_json.as_str()) }
                        }
                    }
                }
                script id="seed-run-json" type="application/json" { (PreEscaped(seed_json)) }
                script id="provider-status-json" type="application/json" { (PreEscaped(provider_json)) }
                script { (PreEscaped(client_script())) }
            }
        }
    }
}

fn render_edge(run: &ProRun, edge: &GraphEdge) -> Markup {
    let source = run
        .graph
        .nodes
        .iter()
        .find(|node| node.id.as_str() == edge.source.as_str())
        .expect("known source node");
    let target = run
        .graph
        .nodes
        .iter()
        .find(|node| node.id.as_str() == edge.target.as_str())
        .expect("known target node");

    let path = wire_path(source, target);
    let label_x = (source.x + target.x) / 2;
    let label_y = (source.y + target.y) / 2;

    html! {
        path class="wire-shadow" d=(path.clone()) {}
        path class="wire" d=(path) {}
        text class="wire-label" x=(label_x) y=(label_y) { (edge.label.as_str()) }
    }
}

fn render_node(node: &GraphNode, selected: bool) -> Markup {
    html! {
        article
            class=(format!(
                "graph-node {}{}",
                node_kind_label(node.kind),
                if selected { " is-selected" } else { "" }
            ))
            data-node-id=(node.id.as_str())
            role="button"
            tabindex="0"
            aria-label=(format!("Inspect {}", node.title))
            style=(format!("left:{}px; top:{}px;", node.x, node.y))
        {
            div class="node-head" {
                p class="node-kind" { (node_kind_label(node.kind)) }
                span { (percent(node.confidence)) }
            }
            h3 { (node.title.as_str()) }
            p { (node.summary.as_str()) }
            small { (node.evidence_ids.len()) " evidence / " (node.challenge_ids.len()) " checks" }
        }
    }
}

fn render_node_inspector(run: &ProRun, node: &GraphNode) -> Markup {
    html! {
        article class="inspector-card" {
            div class="inspector-head" {
                strong id="inspector-node-title" { (node.title.as_str()) }
                span id="inspector-node-confidence" { (percent(node.confidence)) }
            }
            p id="inspector-node-kind" { (node_kind_label(node.kind)) }
            p id="inspector-node-summary" { (node.summary.as_str()) }
            div class="inspector-links" {
                p { "Evidence" }
                ul id="inspector-evidence-list" {
                    @for evidence_id in &node.evidence_ids {
                        li {
                            button
                                class="focus-link"
                                type="button"
                                data-review-kind="evidence"
                                data-review-id=(evidence_id.as_str())
                            {
                                (lookup_evidence_title(run, evidence_id).unwrap_or(evidence_id.as_str()))
                            }
                        }
                    }
                }
            }
            div class="inspector-links" {
                p { "Challenges" }
                ul id="inspector-challenge-list" {
                    @for challenge_id in &node.challenge_ids {
                        li {
                            button
                                class="focus-link"
                                type="button"
                                data-review-kind="challenge"
                                data-review-id=(challenge_id.as_str())
                            {
                                (lookup_challenge_title(run, challenge_id).unwrap_or(challenge_id.as_str()))
                            }
                        }
                    }
                }
            }
        }
    }
}

fn render_source_meter(source: &str, status: SourceStatus, note: &str) -> Markup {
    html! {
        article class="source-meter" {
            div {
                strong { (source) }
                p { (note) }
            }
            span class=(format!("status-dot status-dot--{}", source_status_label(status))) {}
        }
    }
}

fn lookup_evidence_title<'a>(run: &'a ProRun, evidence_id: &str) -> Option<&'a str> {
    run.evidence
        .iter()
        .find(|evidence| evidence.id.as_str() == evidence_id)
        .map(|evidence| evidence.title.as_str())
}

fn lookup_challenge_title<'a>(run: &'a ProRun, challenge_id: &str) -> Option<&'a str> {
    run.challenge_checks
        .iter()
        .find(|challenge| challenge.id.as_str() == challenge_id)
        .map(|challenge| challenge.title.as_str())
}

fn render_provider_status(entry: &ProviderQuotaStatus) -> Markup {
    html! {
        article class="quota-meter" {
            div {
                strong { (entry.label.as_str()) }
                p { (entry.note.as_str()) }
                small {
                    (ledger_category_label(entry.category))
                    " / "
                    (quota_owner_label(entry.quota_owner))
                    " / "
                    (credential_policy_label(entry.credential_policy))
                }
            }
            span class=(format!(
                "quota-state quota-state--{}",
                provider_readiness_label(entry.readiness)
            )) {
                (provider_readiness_label(entry.readiness))
            }
        }
    }
}

fn api_base() -> String {
    std::env::var("PRO_API_BASE").unwrap_or_else(|_| "http://127.0.0.1:8787".to_string())
}

fn client_script() -> &'static str {
    r#"
(() => {
  const apiBase = document.body.dataset.apiBase || "http://127.0.0.1:8787";
  const seed = JSON.parse(document.getElementById("seed-run-json").textContent || "{}");
  const providerSeed = JSON.parse(document.getElementById("provider-status-json").textContent || "{}");
  const byId = (id) => document.getElementById(id);
  let currentRun = seed;
  let activeNodeId = seed?.graph?.nodes?.[0]?.id || null;
  let lastAdapterDryRun = null;
  let workspaceAccessLoaded = false;
  let providerStatusLoaded = Boolean(providerSeed?.entries?.length);
  let runEventsLoaded = false;
  let workOrderLoaded = false;
  let commitIntentLoaded = false;
  let lastInspectedJobId = null;
  let selectedAdapterCandidateId = "ofoxai_model_candidate";

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll("\"", "&quot;")
      .replaceAll("'", "&#39;");
  }

  function percent(value) {
    return `${Math.round((Number(value) || 0) * 100)}%`;
  }

  function readable(value) {
    return String(value ?? "").replaceAll("_", " ");
  }

  function setText(id, value) {
    const node = byId(id);
    if (node) node.textContent = value;
  }

  function setStatus(message) {
    setText("run-action-status", message);
  }

  function wirePath(source, target) {
    const startX = Number(source.x) + 168;
    const startY = Number(source.y) + 86;
    const endX = Number(target.x);
    const endY = Number(target.y) + 86;
    const controlX = Math.round((startX + endX) / 2);
    return `M ${startX} ${startY} C ${controlX} ${startY}, ${controlX} ${endY}, ${endX} ${endY}`;
  }

  function selectNode(nodeId) {
    activeNodeId = nodeId;
    renderGraph(currentRun);
    renderInspector(currentRun);
  }

  function renderGraph(run) {
    const graph = run.graph || { nodes: [], edges: [] };
    const wires = byId("graph-wires");
    const nodes = byId("graph-nodes");
    if (!wires || !nodes) return;

    wires.innerHTML = graph.edges.map((edge) => {
      const source = graph.nodes.find((node) => node.id === edge.source);
      const target = graph.nodes.find((node) => node.id === edge.target);
      if (!source || !target) return "";
      const path = wirePath(source, target);
      const labelX = Math.round((Number(source.x) + Number(target.x)) / 2);
      const labelY = Math.round((Number(source.y) + Number(target.y)) / 2);
      return `
        <path class="wire-shadow" d="${escapeHtml(path)}"></path>
        <path class="wire" d="${escapeHtml(path)}"></path>
        <text class="wire-label" x="${labelX}" y="${labelY}">${escapeHtml(edge.label)}</text>
      `;
    }).join("");

    nodes.innerHTML = graph.nodes.map((node) => `
      <article class="graph-node ${escapeHtml(readable(node.kind).replaceAll(" ", "-"))}${node.id === activeNodeId ? " is-selected" : ""}" data-node-id="${escapeHtml(node.id)}" role="button" tabindex="0" aria-label="Inspect ${escapeHtml(node.title)}" style="left:${Number(node.x) || 0}px; top:${Number(node.y) || 0}px;">
        <div class="node-head">
          <p class="node-kind">${escapeHtml(readable(node.kind))}</p>
          <span>${percent(node.confidence)}</span>
        </div>
        <h3>${escapeHtml(node.title)}</h3>
        <p>${escapeHtml(node.summary)}</p>
        <small>${(node.evidence_ids || []).length} evidence / ${(node.challenge_ids || []).length} checks</small>
      </article>
    `).join("");
    nodes.querySelectorAll(".graph-node").forEach((nodeElement) => {
      nodeElement.addEventListener("click", () => selectNode(nodeElement.dataset.nodeId));
      nodeElement.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode(nodeElement.dataset.nodeId);
        }
      });
    });
  }

  function renderInspector(run) {
    const graph = run.graph || { nodes: [] };
    const node = graph.nodes.find((candidate) => candidate.id === activeNodeId) || graph.nodes[0];
    const panel = byId("node-inspector");
    if (!panel) return;
    if (!node) {
      panel.innerHTML = "<p>Select a node to inspect evidence and challenge links.</p>";
      return;
    }
    const evidence = new Map((run.evidence || []).map((item) => [item.id, item.title]));
    const challenges = new Map((run.challenge_checks || []).map((item) => [item.id, item.title]));
    activeNodeId = node.id;
    panel.innerHTML = `
      <article class="inspector-card">
        <div class="inspector-head">
          <strong id="inspector-node-title">${escapeHtml(node.title)}</strong>
          <span id="inspector-node-confidence">${percent(node.confidence)}</span>
        </div>
        <p id="inspector-node-kind">${escapeHtml(readable(node.kind))}</p>
        <p id="inspector-node-summary">${escapeHtml(node.summary)}</p>
        <div class="inspector-links">
          <p>Evidence</p>
          <ul id="inspector-evidence-list">${(node.evidence_ids || []).map((id) => `
            <li><button class="focus-link" type="button" data-review-kind="evidence" data-review-id="${escapeHtml(id)}">${escapeHtml(evidence.get(id) || id)}</button></li>
          `).join("")}</ul>
        </div>
        <div class="inspector-links">
          <p>Challenges</p>
          <ul id="inspector-challenge-list">${(node.challenge_ids || []).map((id) => `
            <li><button class="focus-link" type="button" data-review-kind="challenge" data-review-id="${escapeHtml(id)}">${escapeHtml(challenges.get(id) || id)}</button></li>
          `).join("")}</ul>
        </div>
      </article>
    `;
  }

  function focusReviewItem(kind, id) {
    const attr = kind === "challenge" ? "data-challenge-id" : "data-evidence-id";
    document
      .querySelectorAll(".evidence-chip.is-focused, .challenge-strip span.is-focused")
      .forEach((item) => item.classList.remove("is-focused"));
    const candidates = Array.from(document.querySelectorAll(`[${attr}]`));
    const target = candidates.find((item) => item.getAttribute(attr) === id);
    if (!target) {
      setText("review-focus-status", `${readable(kind)} ${id} is not visible in the current dock.`);
      return;
    }
    target.classList.add("is-focused");
    target.scrollIntoView({ block: "nearest", inline: "nearest" });
    setText("review-focus-status", `Focused ${readable(kind)}: ${target.textContent.trim()}`);
  }

  function renderRun(run) {
    currentRun = run;
    const nodes = run.graph?.nodes || [];
    if (!nodes.some((node) => node.id === activeNodeId)) {
      activeNodeId = nodes[0]?.id || null;
    }
    renderGraph(run);
    renderInspector(run);
    setText("run-status", readable(run.status));
    setText("run-confidence", `confidence ${percent(run.confidence)}`);
    setText("run-node-count", `${(run.graph?.nodes || []).length} nodes`);
    setText("run-edge-count", `${(run.graph?.edges || []).length} edges`);
    setText("run-title", run.title || "Untitled run");
    setText("run-question", run.question || "");
    setText("run-headline", run.operator_summary?.headline || "");
    setText("run-current-read", run.operator_summary?.current_read || "");
    setText("run-caveat", run.operator_summary?.caveat || "");
    setText("command-status", readable(run.status));
    setText("command-confidence", `${percent(run.confidence)} confidence`);
    setText("command-nodes", `${(run.graph?.nodes || []).length} nodes tracked`);
    setText("command-edges", `${(run.graph?.edges || []).length} causal links`);
    setText("command-challenges", `${(run.challenge_checks || []).length} challenge checks`);
    setText("payload-json", JSON.stringify(run, null, 2));

    const focus = byId("focus-list");
    if (focus) {
      focus.innerHTML = (run.next_steps || []).map((step) => `
        <li><span>${escapeHtml(readable(step.state))}</span><strong>${escapeHtml(step.title)}</strong></li>
      `).join("");
    }

    const sources = byId("source-list");
    if (sources) {
      sources.innerHTML = (run.sources || []).map((source) => `
        <article class="source-meter">
          <div><strong>${escapeHtml(source.source)}</strong><p>${escapeHtml(source.note)}</p></div>
          <span class="status-dot status-dot--${escapeHtml(source.status)}"></span>
        </article>
      `).join("");
    }

    const evidence = byId("evidence-list");
    if (evidence) {
      evidence.innerHTML = (run.evidence || []).slice(0, 3).map((item) => `
        <article class="evidence-chip" data-evidence-id="${escapeHtml(item.id)}">
          <div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.excerpt)}</p></div>
          <span>${escapeHtml(readable(item.stance))} / ${escapeHtml(readable(item.freshness))}</span>
        </article>
      `).join("");
    }

    const challenges = byId("challenge-strip");
    if (challenges) {
      challenges.innerHTML = (run.challenge_checks || []).map((challenge) => `
        <span data-challenge-id="${escapeHtml(challenge.id)}">${escapeHtml(readable(challenge.status))}: ${escapeHtml(challenge.title)}</span>
      `).join("");
    }

  }

  function renderWorkspaceAccess(context) {
    const panel = byId("workspace-access-panel");
    if (!panel) return;
    workspaceAccessLoaded = Boolean(context);
    if (!context) {
      panel.innerHTML = `
        <article class="access-card access-card--empty">
          <div>
            <strong>Workspace access preview</strong>
            <p>Access context loads from the Pro API; auth enforcement is not enabled yet.</p>
          </div>
          <span class="quota-state quota-state--deferred">preview</span>
        </article>
      `;
      return;
    }

    const allowed = (context.permissions || [])
      .filter((permission) => permission.status === "preview_allowed")
      .slice(0, 3)
      .map((permission) => `<li>${escapeHtml(permission.label)}</li>`)
      .join("");
    const gated = (context.permissions || [])
      .filter((permission) => permission.status !== "preview_allowed")
      .slice(0, 3)
      .map((permission) => `<li>${escapeHtml(permission.label)}</li>`)
      .join("");
    const safeguards = (context.safeguards || [])
      .slice(0, 3)
      .map((safeguard) => `<li>${escapeHtml(safeguard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="access-card">
        <div class="work-order-header">
          <strong>Workspace access preview</strong>
          <span class="quota-state quota-state--deferred">${escapeHtml(readable(context.enforcement_mode || "not_enforced_preview"))}</span>
          <p>${escapeHtml(context.workspace_id || "workspace")} / ${escapeHtml(readable(context.auth_mode || "local_preview_only"))}</p>
          <small>${escapeHtml(context.actor?.display_name || "local operator")} / ${escapeHtml(readable(context.actor?.role || "preview_operator"))}</small>
        </div>
        <section>
          <p class="work-order-label">Preview allowed</p>
          <ul class="work-order-list">${allowed || "<li>No preview permissions returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Requires real auth later</p>
          <ul class="work-order-list">${gated || "<li>No gated permissions returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderWorkspaceAccessGate(decision) {
    const panel = byId("workspace-access-gate-panel");
    if (!panel) return;
    if (!decision) {
      panel.innerHTML = `
        <article class="access-card access-card--empty">
          <div>
            <strong>Workspace access gate</strong>
            <p>Choose an action to see the server-computed access decision.</p>
          </div>
          <span class="quota-state quota-state--deferred">idle</span>
        </article>
      `;
      return;
    }

    const blockers = (decision.blocking_reasons || [])
      .slice(0, 5)
      .map((reason) => `<li>${escapeHtml(reason)}</li>`)
      .join("");
    const safeguards = (decision.safeguards || [])
      .slice(0, 4)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");
    const sensitiveRules = (decision.sensitive_data_rules || [])
      .slice(0, 3)
      .map((rule) => `<li>${escapeHtml(rule)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="access-card">
        <div class="work-order-header">
          <strong>Workspace access gate</strong>
          <span class="quota-state quota-state--deferred">${decision.allowed ? "preview allowed" : "access denied"}</span>
          <p>${escapeHtml(readable(decision.action || "unknown_action"))} / ${escapeHtml(readable(decision.status || "unknown_status"))}</p>
          <small>${escapeHtml(decision.workspace_id || "workspace")} / ${escapeHtml(decision.actor_id || "actor")} / resource: ${escapeHtml(decision.resource || "none")}</small>
        </div>
        <section>
          <p class="work-order-label">Decision</p>
          <ul class="work-order-list">
            <li>${decision.preview_only ? "preview only" : "not preview only"}</li>
            <li>${decision.requires_auth ? "hosted auth required" : "hosted auth not required"}</li>
            <li>${decision.requires_worker ? "worker required" : "worker not required"}</li>
            <li>permission: ${escapeHtml(decision.matched_permission_id || "none")}</li>
          </ul>
        </section>
        <section>
          <p class="work-order-label">Blocking reasons</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Sensitive data rules</p>
          <ul class="work-order-list">${sensitiveRules || "<li>No sensitive-data rules returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderRunEvents(timeline) {
    const panel = byId("run-event-panel");
    if (!panel) return;
    runEventsLoaded = Boolean(timeline);
    if (!timeline) {
      panel.innerHTML = `
        <article class="event-card event-card--empty">
          <div>
            <strong>Run event timeline</strong>
            <p>Event status vocabulary loads from the Pro API; no durable event store is connected.</p>
          </div>
          <span class="quota-state quota-state--deferred">derived</span>
        </article>
      `;
      return;
    }

    const events = (timeline.events || []).slice(-4).map((event) => `
      <li>
        <strong>${escapeHtml(event.title)}</strong>
        <span>${escapeHtml(readable(event.status))} / ${escapeHtml(readable(event.kind))}</span>
        <small>${escapeHtml(event.detail || "Derived from the current run record.")}</small>
      </li>
    `).join("");
    const vocabulary = (timeline.status_vocabulary || []).slice(0, 4).map((entry) => `
      <li>
        <strong>${escapeHtml(entry.label)}</strong>
        <span>${entry.reviewable ? "reviewable" : "not reviewable"}${entry.requires_worker ? " / worker later" : ""}</span>
      </li>
    `).join("");
    const safeguards = (timeline.safeguards || []).slice(0, 2).map((guard) => `<li>${escapeHtml(guard)}</li>`).join("");

    panel.innerHTML = `
      <article class="event-card">
        <div class="work-order-header">
          <strong>Run event timeline</strong>
          <span class="quota-state quota-state--deferred">${timeline.durable ? "durable" : "non durable"}</span>
          <p>${escapeHtml(readable(timeline.current_status || "queued"))} / ${escapeHtml(timeline.generated_at || "derived")}</p>
          <small>${escapeHtml(timeline.run_id || "run")} / ${escapeHtml(timeline.workspace_id || "workspace")}</small>
        </div>
        <section>
          <p class="work-order-label">Recent events</p>
          <ol class="work-order-list">${events || "<li>No events returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Status vocabulary</p>
          <ul class="work-order-list">${vocabulary || "<li>No status vocabulary returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Timeline safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>Timeline is derived only.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderEventReplay(replay) {
    const panel = byId("event-replay-panel");
    if (!panel) return;
    if (!replay) {
      panel.innerHTML = `
        <article class="event-card event-card--empty">
          <div>
            <strong>Event replay</strong>
            <p>Durable local event replay loads from the Pro API; hosted event storage is not connected.</p>
          </div>
          <span class="quota-state quota-state--deferred">local file</span>
        </article>
      `;
      return;
    }

    const events = (replay.events || []).slice(-4).map((entry) => `
      <li>
        <strong>${escapeHtml(entry.event?.title || entry.id)}</strong>
        <span>${escapeHtml(readable(entry.event?.status || "unknown"))} / seq ${escapeHtml(entry.sequence)}</span>
        <small>${escapeHtml(entry.event?.detail || "Replay event persisted locally.")}</small>
      </li>
    `).join("");
    const safeguards = (replay.safeguards || [])
      .slice(0, 3)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="event-card">
        <div class="work-order-header">
          <strong>Event replay</strong>
          <span class="quota-state quota-state--deferred">${replay.durable ? "local durable" : "derived"}</span>
          <p>${escapeHtml(readable(replay.mode || "local_file_replay"))} / ${escapeHtml(replay.event_count || 0)} events</p>
          <small>${escapeHtml(replay.generated_at || "local replay")}</small>
        </div>
        <section>
          <p class="work-order-label">Replay stream</p>
          <ol class="work-order-list">${events || "<li>No replay events returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Replay safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>Replay remains local-only.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderReviewComparison(comparison) {
    const panel = byId("review-comparison-panel");
    if (!panel) return;
    if (!comparison) {
      panel.innerHTML = `
        <article class="review-card review-card--empty">
          <div>
            <strong>Review comparison</strong>
            <p>Evidence and challenge deltas load from the Pro API; no historical store is queried yet.</p>
          </div>
          <span class="quota-state quota-state--deferred">preview</span>
        </article>
      `;
      return;
    }

    const evidenceItems = (comparison.evidence_deltas || []).slice(0, 4).map((delta) => `
      <li>
        <strong>${escapeHtml(delta.title)}</strong>
        <span>${escapeHtml(readable(delta.delta))} / ${escapeHtml(readable(delta.stance))} / ${escapeHtml(readable(delta.freshness))}</span>
        <small>${escapeHtml(delta.source)}: ${escapeHtml(delta.note)}</small>
      </li>
    `).join("");
    const challengeItems = (comparison.challenge_deltas || []).slice(0, 4).map((delta) => `
      <li>
        <strong>${escapeHtml(delta.title)}</strong>
        <span>${escapeHtml(readable(delta.delta))} / ${escapeHtml(readable(delta.status))}</span>
        <small>${escapeHtml(delta.note)}</small>
      </li>
    `).join("");
    const evidenceSummary = comparison.evidence_summary || {};
    const challengeSummary = comparison.challenge_summary || {};
    const safeguards = (comparison.safeguards || [])
      .slice(0, 2)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="review-card">
        <div class="work-order-header">
          <strong>Review comparison</strong>
          <span class="quota-state quota-state--deferred">${escapeHtml(readable(comparison.mode || "derived_previous_checkpoint"))}</span>
          <p>${escapeHtml(comparison.run_id || "run")} vs ${escapeHtml(comparison.baseline_run_id || "baseline")}</p>
          <small>Evidence +${evidenceSummary.added || 0} / ~${evidenceSummary.changed || 0} / -${evidenceSummary.removed || 0}; challenges +${challengeSummary.added || 0} / ~${challengeSummary.changed || 0} / -${challengeSummary.removed || 0}</small>
        </div>
        <section>
          <p class="work-order-label">Evidence deltas</p>
          <ol class="work-order-list">${evidenceItems || "<li>No evidence deltas returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Challenge deltas</p>
          <ol class="work-order-list">${challengeItems || "<li>No challenge deltas returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Comparison safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>Comparison is preview-only.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderProviderStatus(snapshot) {
    providerStatusLoaded = Boolean(snapshot?.entries?.length);
    setText("provider-status-mode", readable(snapshot.mode || "local_alpha_no_credentials"));
    const list = byId("provider-status-list");
    if (!list) return;
    list.innerHTML = (snapshot.entries || []).map((entry) => `
      <article class="quota-meter">
        <div>
          <strong>${escapeHtml(entry.label)}</strong>
          <p>${escapeHtml(entry.note)}</p>
          <small>${escapeHtml(readable(entry.category))} / ${escapeHtml(readable(entry.quota_owner))} / ${escapeHtml(readable(entry.credential_policy))}</small>
        </div>
        <span class="quota-state quota-state--${escapeHtml(entry.readiness)}">${escapeHtml(readable(entry.readiness))}</span>
      </article>
    `).join("");
  }

  function renderProviderAdapterContract(contract) {
    const panel = byId("provider-adapter-panel");
    if (!panel) return;
    if (!contract) {
      panel.innerHTML = `
        <article class="quota-meter quota-meter--empty">
          <div>
            <strong>Adapter contract planned</strong>
            <p>Provider adapter semantics load from the Pro API; provider calls stay disabled.</p>
          </div>
          <span class="quota-state quota-state--deferred">dry</span>
        </article>
      `;
      return;
    }

    const requestFields = (contract.request_fields || []).slice(0, 4).map((field) => `
      <li>
        <strong>${escapeHtml(field.id)}</strong>
        <span>${escapeHtml(field.owner)}${field.required ? " / required" : " / optional"}</span>
      </li>
    `).join("");
    const degradations = (contract.degradation_states || []).slice(0, 4).map((state) => `
      <li>
        <strong>${escapeHtml(state.id)}</strong>
        <span>${escapeHtml(readable(state.status))} / ${escapeHtml(readable(state.retry_policy))}</span>
      </li>
    `).join("");

    panel.innerHTML = `
      <article class="work-order-card adapter-card">
        <div class="work-order-header">
          <strong>Provider adapter contract</strong>
          <span class="quota-state quota-state--deferred">${contract.execution_allowed ? "calls on" : "calls off"}</span>
          <p>${escapeHtml(readable(contract.mode || "dry_contract_only"))}</p>
        </div>
        <section>
          <p class="work-order-label">Request fields</p>
          <ol class="work-order-list">${requestFields || "<li>No request fields returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Degradation states</p>
          <ul class="work-order-list">${degradations || "<li>No degradation states returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderProviderAdapterDryRun(result) {
    const panel = byId("provider-adapter-dry-run-result");
    if (!panel) return;
    lastAdapterDryRun = result || null;
    if (!result) {
      panel.innerHTML = `
        <article class="quota-meter quota-meter--empty">
          <div>
            <strong>No adapter dry-run yet</strong>
            <p>Run one to inspect evidence, quota, and degradation shape before live providers exist.</p>
          </div>
          <span class="quota-state quota-state--deferred">idle</span>
        </article>
      `;
      return;
    }

    const evidenceCount = (result.evidence_preview || []).length;
    const usageItems = (result.usage_ledger_preview || []).slice(0, 3).map((row) => `
      <li>
        <strong>${escapeHtml(row.lane_id)}</strong>
        <span>${escapeHtml(readable(row.quota_owner))} / billable units: ${escapeHtml(row.billable_units)}</span>
        <small>${escapeHtml(row.note || "No usage note.")}</small>
      </li>
    `).join("");
    const degradationItems = (result.degradation_states || []).slice(0, 3).map((state) => `
      <li>
        <strong>${escapeHtml(state.id)}</strong>
        <span>${escapeHtml(readable(state.status))} / ${escapeHtml(readable(state.retry_policy))}</span>
      </li>
    `).join("");
    const warnings = (result.warnings || []).slice(0, 4).map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card adapter-card">
        <div class="work-order-header">
          <strong>Provider adapter dry run</strong>
          <span class="quota-state quota-state--deferred">${result.execution_allowed ? "calls on" : "calls off"}</span>
          <p>${escapeHtml(readable(result.mode || "dry_run_only"))}</p>
          <small>Lane: ${escapeHtml(result.provider_lane_id || "none")} / evidence preview: ${evidenceCount}</small>
        </div>
        <section>
          <p class="work-order-label">Usage preview</p>
          <ol class="work-order-list">${usageItems || "<li>No usage rows returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Degradation preview</p>
          <ul class="work-order-list">${degradationItems || "<li>No degradation states returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Warnings</p>
          <ul class="work-order-list">${warnings || "<li>No warnings returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderProviderAdapterCandidates(catalog) {
    const panel = byId("provider-adapter-candidate-panel");
    if (!panel) return;
    if (!catalog || !(catalog.candidates || []).length) {
      panel.innerHTML = `
        <article class="quota-meter quota-meter--empty">
          <div>
            <strong>Live adapter candidate</strong>
            <p>Candidate gates load from the Pro API; live provider calls stay denied.</p>
          </div>
          <span class="quota-state quota-state--deferred">gated</span>
        </article>
      `;
      return;
    }

    const candidate = catalog.candidates[0];
    selectedAdapterCandidateId = candidate.id || selectedAdapterCandidateId;
    const gates = (candidate.required_gates || []).slice(0, 4).map((gate) => `
      <li>
        <strong>${escapeHtml(gate.label || gate.id)}</strong>
        <span>${escapeHtml(readable(gate.status || "blocked"))} / ${escapeHtml(gate.owner || "owner")}</span>
      </li>
    `).join("");
    const safeguards = (catalog.safeguards || []).slice(0, 3).map((guard) => `<li>${escapeHtml(guard)}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card adapter-card">
        <div class="work-order-header">
          <strong>${escapeHtml(candidate.label || "Live adapter candidate")}</strong>
          <span class="quota-state quota-state--deferred">${candidate.execution_allowed ? "execution on" : "execution denied"}</span>
          <p>${escapeHtml(candidate.provider_kind || "provider")} / ${escapeHtml(candidate.lane_id || "lane")}</p>
          <small>${escapeHtml(candidate.description || "Candidate is gated before live execution.")}</small>
        </div>
        <section>
          <p class="work-order-label">Required gates</p>
          <ol class="work-order-list">${gates || "<li>No gates returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>Live calls remain denied.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderProviderAdapterGateCheck(result) {
    const panel = byId("live-adapter-gate-check-result");
    if (!panel) return;
    if (!result) {
      panel.innerHTML = `
        <article class="quota-meter quota-meter--empty">
          <div>
            <strong>No live gate check yet</strong>
            <p>Run the check to see exactly why live adapter execution is still blocked.</p>
          </div>
          <span class="quota-state quota-state--deferred">denied</span>
        </article>
      `;
      return;
    }

    const gates = (result.gates || []).slice(0, 6).map((gate) => `
      <li>
        <strong>${escapeHtml(gate.label || gate.id)}</strong>
        <span>${escapeHtml(readable(gate.status || "blocked"))} / ${escapeHtml(gate.owner || "owner")}</span>
        <small>${escapeHtml(gate.description || "Gate has no description.")}</small>
      </li>
    `).join("");
    const blockers = (result.blocking_reasons || []).slice(0, 6).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card adapter-card">
        <div class="work-order-header">
          <strong>Live adapter gate check</strong>
          <span class="quota-state quota-state--deferred">${result.execution_allowed ? "execution on" : "execution denied"}</span>
          <p>${escapeHtml(readable(result.mode || "denied_preview_only"))} / ${escapeHtml(result.candidate_id || "candidate")}</p>
          <small>${escapeHtml(result.next_required_step || "Live execution remains blocked.")}</small>
        </div>
        <section>
          <p class="work-order-label">Gate states</p>
          <ol class="work-order-list">${gates || "<li>No gates returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Blocking reasons</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionReadiness(result) {
    const panel = byId("execution-readiness-result");
    if (!panel) return;
    if (!result) {
      panel.innerHTML = `
        <article class="quota-meter quota-meter--empty">
          <div>
            <strong>Execution readiness</strong>
            <p>Run the check before any future live execution path is enabled.</p>
          </div>
          <span class="quota-state quota-state--deferred">blocked</span>
        </article>
      `;
      return;
    }

    const observations = (result.preview_observations || []).slice(0, 6).map((item) => `
      <li>
        <strong>${escapeHtml(item.label || item.id)}</strong>
        <span>${item.observed ? "observed" : "missing"} / ${item.required_before_live_execution ? "required" : "optional"}</span>
      </li>
    `).join("");
    const blockers = (result.blocking_reasons || []).slice(0, 8).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("");
    const safeguards = (result.safeguards || []).slice(0, 8).map((guard) => `<li>${escapeHtml(guard)}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card adapter-card">
        <div class="work-order-header">
          <strong>Execution readiness</strong>
          <span class="quota-state quota-state--deferred">${result.execution_allowed ? "execution on" : "execution denied"}</span>
          <p>${escapeHtml(readable(result.mode || "composed_preview_only"))} / ${escapeHtml(readable(result.status || "denied_requires_hosted_gates"))}</p>
          <small>${escapeHtml(result.workspace_id || "workspace")} / ${escapeHtml(result.run_id || "run")} / ${escapeHtml(result.candidate_id || "candidate")}</small>
        </div>
        <section>
          <p class="work-order-label">Observed prerequisites</p>
          <ol class="work-order-list">${observations || "<li>No observations returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Blocking reasons</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Readiness safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionAdmission(decision) {
    const panel = byId("execution-admission-panel");
    if (!panel) return;
    if (!decision) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Execution admission gate</strong>
            <p>Server-side admission payload waits for hosted auth, vault handles, and quota reservations.</p>
          </div>
          <span class="quota-state quota-state--deferred">denied</span>
        </article>
      `;
      return;
    }

    const gates = (decision.gates || []).slice(0, 5).map((gate) => `
      <li>
        <strong>${escapeHtml(readable(gate.id || gate.label))}</strong>
        <span>${escapeHtml(readable(gate.status || "missing"))} / ${gate.allowed ? "allowed" : "blocked"}</span>
        <small>${escapeHtml(gate.requirement || "Gate has no requirement.")}</small>
      </li>
    `).join("");
    const blockers = (decision.blocking_reasons || [])
      .slice(0, 8)
      .map((reason) => `<li>${escapeHtml(readable(reason))}</li>`)
      .join("");
    const safeguards = (decision.safeguards || [])
      .slice(0, 6)
      .map((guard) => `<li>${escapeHtml(readable(guard))}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card admission-card">
        <div class="work-order-header">
          <strong>Execution admission gate</strong>
          <span class="quota-state quota-state--deferred">${decision.admitted ? "admitted" : "admission denied"}</span>
          <p>${escapeHtml(readable(decision.mode || "preview_only_server_computed"))} / ${escapeHtml(readable(decision.status || "denied_requires_hosted_gates"))}</p>
          <small>tenant auth: blocked / vault handle: ${decision.vault_handle_issued ? "issued" : "missing"} / quota reservation: ${decision.quota_reserved ? "reserved" : "missing"}</small>
        </div>
        <section>
          <p class="work-order-label">Admission gates</p>
          <ol class="work-order-list">${gates || "<li>No gates returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Blocking reasons</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Admission safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>no provider execution or secret access</li>"}</ul>
        </section>
        <small>${escapeHtml(decision.next_required_step || "Connect hosted gates before execution admission can pass.")}</small>
      </article>
    `;
  }

  function renderExecutionPreflightBoundary(boundary) {
    const panel = byId("execution-preflight-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Pre-execution boundary</strong>
            <p>Hosted auth, vault handles, quota reservations, and worker leases must exist before live calls.</p>
          </div>
          <span class="quota-state quota-state--deferred">denied</span>
        </article>
      `;
      return;
    }

    const requirements = (boundary.requirements || []).slice(0, 6).map((item) => `
      <li>
        <strong>${escapeHtml(item.label || item.id)}</strong>
        <span>${escapeHtml(readable(item.status))} / ${item.blocks_execution ? "blocks execution" : "informational"}</span>
        <small>${escapeHtml(item.owner)}: ${escapeHtml(item.requirement)}</small>
      </li>
    `).join("");
    const handoffs = (boundary.handoff_rules || []).slice(0, 4).map((rule) => `
      <li>
        <strong>${escapeHtml(readable(rule.stage || rule.id))}</strong>
        <span>${rule.allowed_now ? "allowed now" : "blocked now"}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || [])
      .slice(0, 5)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card preflight-card">
        <div class="work-order-header">
          <strong>Pre-execution boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.execution_allowed ? "execution on" : "execution denied"}</span>
          <p>${escapeHtml(readable(boundary.mode || "preview_only_no_execution"))} / ${escapeHtml(readable(boundary.status || "denied_requires_hosted_prerequisites"))}</p>
          <small>auth: ${boundary.auth_enforced ? "enforced" : "missing"} / vault handle: ${boundary.credential_vault_handle_issued ? "issued" : "missing"} / quota reservation: ${boundary.quota_reservation_allowed ? "allowed" : "blocked"}</small>
        </div>
        <section>
          <p class="work-order-label">Hosted prerequisites</p>
          <ol class="work-order-list">${requirements || "<li>No requirements returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Execution handoffs</p>
          <ul class="work-order-list">${handoffs || "<li>No handoff rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Preflight safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionJobs(jobs) {
    const list = byId("execution-job-list");
    if (!list) return;
    if (!jobs || jobs.length === 0) {
      list.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>No queued preview jobs yet</strong>
            <p>Create one to inspect the routing lane before workers exist.</p>
          </div>
          <span class="quota-state quota-state--deferred">idle</span>
        </article>
      `;
      renderWorkOrder(null);
      renderExecutionHandoffPreview(null);
      renderExecutionIntentPreview(null);
      return;
    }
    list.innerHTML = jobs.slice(0, 4).map((job) => `
      <article class="queue-meter">
        <div>
          <strong>${escapeHtml(job.id)}</strong>
          <p>${escapeHtml(job.query)}</p>
          <small>${escapeHtml(readable(job.status))} / ${escapeHtml(job.selected_lane_id || "no selected lane")}</small>
          <button class="queue-action" type="button" data-work-order-job-id="${escapeHtml(job.id)}">Inspect route</button>
        </div>
        <span class="quota-state quota-state--${job.execution_allowed ? "ready" : "deferred"}">${job.execution_allowed ? "execution on" : "execution off"}</span>
      </article>
    `).join("");
  }

  function renderWorkOrder(order) {
    const detail = byId("execution-work-order-detail");
    if (!detail) return;
    workOrderLoaded = Boolean(order);
    if (!order) {
      lastInspectedJobId = null;
      detail.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>No work order selected</strong>
            <p>Inspect a queued job to see route steps and execution safeguards.</p>
          </div>
          <span class="quota-state quota-state--deferred">preview</span>
        </article>
      `;
      return;
    }
    lastInspectedJobId = order.job_id || lastInspectedJobId;

    const routeSteps = (order.route_steps || []).map((step) => `
      <li>
        <strong>${escapeHtml(step.label || step.lane_id || "route lane")}</strong>
        <span>${escapeHtml(readable(step.decision || "unknown"))} / ${escapeHtml(readable(step.readiness || "unknown"))} / ${escapeHtml(readable(step.quota_owner || "unknown"))}</span>
        <small>${escapeHtml(readable(step.action || "no action"))}${step.retry_after_seconds ? ` after ${escapeHtml(step.retry_after_seconds)}s` : ""}: ${escapeHtml(step.reason || "No route note provided.")}</small>
      </li>
    `).join("");
    const warnings = (order.routing_warnings || []).map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
    const safeguards = (order.safeguards || []).map((guard) => `<li>${escapeHtml(guard)}</li>`).join("");

    detail.innerHTML = `
      <article class="work-order-card">
        <div class="work-order-header">
          <strong>${escapeHtml(order.job_id)}</strong>
          <span class="quota-state quota-state--deferred">${escapeHtml(readable(order.mode || "preview_only"))}</span>
          <p>${escapeHtml(order.query)}</p>
          <small>Selected lane: ${escapeHtml(order.selected_lane_id || "none")}</small>
        </div>
        <section>
          <p class="work-order-label">Route steps</p>
          <ol class="work-order-list">${routeSteps || "<li>No route steps returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Routing warnings</p>
          <ul class="work-order-list">${warnings || "<li>No routing warnings.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Execution safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>Execution remains disabled.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionHandoffPreview(preview) {
    const panel = byId("execution-handoff-panel");
    if (!panel) return;
    if (!preview) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Execution handoff preview</strong>
            <p>Inspect a queued job to see why provider and worker handoff remains blocked.</p>
          </div>
          <span class="quota-state quota-state--deferred">denied</span>
        </article>
      `;
      return;
    }

    const blockers = (preview.blocking_reasons || []).map((reason) => `<li title="${escapeHtml(reason)}">${escapeHtml(readable(reason))}</li>`).join("");
    const safeguards = (preview.safeguards || []).map((guard) => `<li title="${escapeHtml(guard)}">${escapeHtml(readable(guard))}</li>`).join("");
    const requirements = (preview.preflight?.requirements || []).slice(0, 5).map((item) => `
      <li>
        <strong>${escapeHtml(item.label || item.id)}</strong>
        <span>${escapeHtml(readable(item.status))} / ${item.blocks_execution ? "blocks execution" : "informational"}</span>
        <small>${escapeHtml(item.requirement)}</small>
      </li>
    `).join("");

    panel.innerHTML = `
      <article class="work-order-card handoff-card">
        <div class="work-order-header">
          <strong>Execution handoff preview</strong>
          <span class="quota-state quota-state--deferred">${preview.execution_allowed ? "handoff allowed" : "handoff denied"}</span>
          <p>${escapeHtml(readable(preview.mode || "preview_only_denied"))} / ${escapeHtml(preview.job_id || "job")}</p>
          <small>${escapeHtml(preview.next_required_step || "Hosted prerequisites must exist before live handoff.")}</small>
        </div>
        <section>
          <p class="work-order-label">Handoff blockers</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Preflight requirements</p>
          <ol class="work-order-list">${requirements || "<li>No preflight requirements returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Handoff safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionIntentPreview(preview) {
    const panel = byId("execution-intent-panel");
    if (!panel) return;
    if (!preview) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Execution intent preview</strong>
            <p>Inspect a queued job to see why hosted intent persistence remains blocked.</p>
          </div>
          <span class="quota-state quota-state--deferred">rejected</span>
        </article>
      `;
      return;
    }

    const blockers = (preview.blocking_reasons || []).map((reason) => `<li title="${escapeHtml(reason)}">${escapeHtml(readable(reason))}</li>`).join("");
    const capabilities = (preview.required_capabilities || []).slice(0, 5).map((capability) => `<li>${escapeHtml(capability)}</li>`).join("");
    const safeguards = (preview.safeguards || []).map((guard) => `<li title="${escapeHtml(guard)}">${escapeHtml(readable(guard))}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card intent-card">
        <div class="work-order-header">
          <strong>Execution intent preview</strong>
          <span class="quota-state quota-state--deferred">${preview.intent_creation_allowed ? "intent allowed" : "intent rejected"}</span>
          <p>${escapeHtml(readable(preview.mode || "preview_only_rejected"))} / ${escapeHtml(preview.intent_id_preview || "intent preview")}</p>
          <small>Idempotency preview: ${escapeHtml(preview.idempotency_key_preview || "not available")}</small>
          <small>${escapeHtml(preview.next_required_step || "Hosted prerequisites must exist before intent persistence.")}</small>
        </div>
        <section>
          <p class="work-order-label">Intent blockers</p>
          <ul class="work-order-list">${blockers || "<li>No blockers returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Required capabilities</p>
          <ul class="work-order-list">${capabilities || "<li>No capabilities returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Intent safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderExecutionIntentStoreBoundary(boundary) {
    const panel = byId("execution-intent-store-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Intent store boundary</strong>
            <p>Durable intent persistence rules load from the Pro API; persistence remains off.</p>
          </div>
          <span class="quota-state quota-state--deferred">persistence off</span>
        </article>
      `;
      return;
    }

    const transitions = (boundary.transition_rules || []).slice(0, 5).map((rule) => `
      <li title="${escapeHtml(rule.requirement || "")}">
        <strong>${escapeHtml(readable(rule.id || "transition"))}</strong>
        <span>${escapeHtml(readable(rule.from_status || "from"))} -> ${escapeHtml(readable(rule.to_status || "to"))}</span>
        <small>${rule.allowed_now ? "allowed now" : "planned only"}</small>
      </li>
    `).join("");
    const idempotency = (boundary.idempotency_rules || []).slice(0, 4).map((rule) => `
      <li title="${escapeHtml(rule.requirement || "")}">
        <strong>${escapeHtml(readable(rule.id || "idempotency"))}</strong>
        <span>${escapeHtml(rule.key_scope || "future key scope")}</span>
      </li>
    `).join("");
    const retention = (boundary.retention_rules || []).slice(0, 3).map((rule) => `
      <li title="${escapeHtml(rule.requirement || "")}">
        <strong>${escapeHtml(readable(rule.id || "retention"))}</strong>
        <span>${escapeHtml(readable(rule.store || "future store"))}</span>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || []).map((guard) => `<li title="${escapeHtml(guard)}">${escapeHtml(readable(guard))}</li>`).join("");

    panel.innerHTML = `
      <article class="work-order-card intent-store-card">
        <div class="work-order-header">
          <strong>Intent store boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.persistence_allowed ? "persistence on" : "persistence off"}</span>
          <p>${escapeHtml(readable(boundary.mode || "planned_no_persistence"))} / store ${boundary.intent_store_connected ? "connected" : "not connected"}</p>
          <small>${escapeHtml(boundary.next_required_step || "Connect durable hosted storage only after execution gates exist.")}</small>
        </div>
        <section>
          <p class="work-order-label">Transition rules</p>
          <ul class="work-order-list">${transitions || "<li>No transition rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Idempotency rules</p>
          <ul class="work-order-list">${idempotency || "<li>No idempotency rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Retention rules</p>
          <ul class="work-order-list">${retention || "<li>No retention rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Store safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  async function inspectWorkOrder(jobId) {
    if (!jobId) return;
    setText("execution-queue-status", `Inspecting ${jobId} work order...`);
    const [order, handoff, intent] = await Promise.all([
      fetchJson(`/api/execution-jobs/${encodeURIComponent(jobId)}/work-order`),
      fetchJson(`/api/execution-jobs/${encodeURIComponent(jobId)}/handoff-preview`),
      fetchJson(`/api/execution-jobs/${encodeURIComponent(jobId)}/intent-preview`),
    ]);
    renderWorkOrder(order);
    renderExecutionHandoffPreview(handoff);
    renderExecutionIntentPreview(intent);
    setText("execution-queue-status", `Loaded ${jobId} route, handoff, and intent blockers; execution remains disabled.`);
  }

  function renderExecutionLifecycle(spec) {
    const panel = byId("execution-lifecycle-panel");
    if (!panel) return;
    if (!spec) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Worker lifecycle planned</strong>
            <p>Lifecycle states load from the Pro API; execution remains disabled.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const visibleStages = (spec.stages || []).filter((stage) => stage.visible_to_user).slice(0, 5);
    const stageItems = visibleStages.map((stage) => `
      <li>
        <strong>${escapeHtml(stage.label)}</strong>
        <span>${escapeHtml(readable(stage.phase))}</span>
        <small>${escapeHtml(stage.purpose)}</small>
      </li>
    `).join("");
    const failureItems = (spec.failure_states || []).slice(0, 4).map((failure) => `
      <li>
        <strong>${escapeHtml(failure.label)}</strong>
        <span>${escapeHtml(readable(failure.retry_policy))}${failure.terminal ? " / terminal" : " / retryable"}</span>
      </li>
    `).join("");

    panel.innerHTML = `
      <article class="work-order-card lifecycle-card">
        <div class="work-order-header">
          <strong>Hosted worker lifecycle</strong>
          <span class="quota-state quota-state--deferred">${spec.execution_allowed ? "execution on" : "execution off"}</span>
          <p>${escapeHtml(readable(spec.mode || "hosted_worker_planned"))}</p>
        </div>
        <section>
          <p class="work-order-label">Visible stages</p>
          <ol class="work-order-list">${stageItems || "<li>No visible stages returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Failure states</p>
          <ul class="work-order-list">${failureItems || "<li>No failure states returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderWorkerLeaseBoundary(boundary) {
    const panel = byId("worker-lease-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Worker lease boundary</strong>
            <p>Lease and retry rules load from the Pro API; no workers or retries run.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const leaseRules = (boundary.lease_rules || []).slice(0, 4).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${escapeHtml(rule.actor)} / ${escapeHtml(readable(rule.status))}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const retryRules = (boundary.retry_rules || []).slice(0, 4).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${escapeHtml(rule.failure_state)} / ${escapeHtml(readable(rule.retry_policy))} / ${rule.max_attempts} attempts</span>
        <small>${rule.preserves_partial_results ? "preserves partial results" : "no partial preservation"} / ${escapeHtml(readable(rule.status))}</small>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || [])
      .slice(0, 4)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card lease-card">
        <div class="work-order-header">
          <strong>Worker lease boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.execution_allowed ? "execution on" : "execution off"}</span>
          <p>${escapeHtml(readable(boundary.mode || "planned_no_workers"))} / lease store: ${boundary.lease_store_connected ? "connected" : "off"} / retry scheduler: ${boundary.retry_scheduler_enabled ? "on" : "off"}</p>
        </div>
        <section>
          <p class="work-order-label">Lease rules</p>
          <ol class="work-order-list">${leaseRules || "<li>No lease rules returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Retry scheduler</p>
          <ul class="work-order-list">${retryRules || "<li>No retry rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Worker safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No worker safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderResultCommitBoundary(boundary) {
    const panel = byId("result-commit-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Result commit boundary</strong>
            <p>Commit and event-store rules load from the Pro API; no durable writes run.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const stages = (boundary.commit_stages || []).slice(0, 4).map((stage) => `
      <li>
        <strong>${escapeHtml(stage.label)}</strong>
        <span>${escapeHtml(readable(stage.status))}</span>
        <small>${escapeHtml(stage.id)}: ${escapeHtml(stage.requirement)}</small>
      </li>
    `).join("");
    const writeRules = (boundary.event_write_rules || []).slice(0, 4).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${escapeHtml(rule.event_kind)} / ${rule.allowed_now ? "allowed now" : "blocked now"}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const reconciliation = (boundary.reconciliation_rules || []).slice(0, 3).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${escapeHtml(rule.failure_state)} / ${rule.preserves_partial_results ? "preserves partials" : "drops partials"} / ${escapeHtml(readable(rule.status))}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || [])
      .slice(0, 4)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card commit-card">
        <div class="work-order-header">
          <strong>Result commit boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.commit_writes_enabled ? "writes on" : "writes off"}</span>
          <p>${escapeHtml(readable(boundary.mode || "planned_no_writes"))} / event store: ${boundary.event_store_connected ? "connected" : "off"} / partial reconciliation: ${boundary.partial_reconciliation_enabled ? "on" : "off"}</p>
        </div>
        <section>
          <p class="work-order-label">Commit stages</p>
          <ol class="work-order-list">${stages || "<li>No commit stages returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Event writes</p>
          <ul class="work-order-list">${writeRules || "<li>No event write rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Partial reconciliation</p>
          <ul class="work-order-list">${reconciliation || "<li>No reconciliation rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Commit safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No commit safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderWorkerResultDryRun(result) {
    const panel = byId("worker-result-dry-run-panel");
    if (!panel) return;
    if (!result) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Worker result dry-run</strong>
            <p>Run a preview to inspect proposed result commit steps from local replay.</p>
          </div>
          <span class="quota-state quota-state--deferred">preview</span>
        </article>
      `;
      return;
    }

    const steps = (result.proposed_steps || []).map((step) => `
      <li>
        <strong>${escapeHtml(step.label || step.id)}</strong>
        <span>${escapeHtml(readable(step.status || "preview_only"))} / writes now: ${step.writes_now ? "yes" : "no"}</span>
        <small>${escapeHtml(step.id)} / replay events: ${escapeHtml(step.depends_on_replay_events || 0)} / ${escapeHtml(step.note || "No dry-run note.")}</small>
      </li>
    `).join("");
    const checks = (result.commit_checks || []).map((check) => `
      <li>
        <strong>${escapeHtml(check.label || check.id)}</strong>
        <span>${check.passed ? "passed" : "blocked"} / required later: ${check.required_before_live_execution ? "yes" : "no"}</span>
        <small>${escapeHtml(check.note || "No commit check note.")}</small>
      </li>
    `).join("");
    const safeguards = (result.safeguards || [])
      .slice(0, 6)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card commit-card">
        <div class="work-order-header">
          <strong>Worker result dry-run</strong>
          <span class="quota-state quota-state--deferred">${result.result_event_write_allowed ? "writes on" : "writes off"}</span>
          <p>${escapeHtml(readable(result.mode || "preview_only_local_replay"))} / replay events: ${escapeHtml(result.replay_event_count || 0)} / result commit: ${result.result_commit_allowed ? "allowed" : "blocked"}</p>
          <small>Run: ${escapeHtml(result.run_id || "unknown")} / Workspace: ${escapeHtml(result.workspace_id || "unknown")}</small>
        </div>
        <section>
          <p class="work-order-label">Proposed result steps</p>
          <ol class="work-order-list">${steps || "<li>No proposed steps returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Commit checks</p>
          <ul class="work-order-list">${checks || "<li>No commit checks returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Dry-run safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No dry-run safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderResultSnapshotReadiness(readiness) {
    const panel = byId("result-snapshot-readiness-panel");
    if (!panel) return;
    if (!readiness) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Result snapshot readiness</strong>
            <p>Check why persisted result snapshots are still blocked.</p>
          </div>
          <span class="quota-state quota-state--deferred">gated</span>
        </article>
      `;
      return;
    }

    const snapshot = readiness.proposed_snapshot || {};
    const checks = (readiness.readiness_checks || []).map((check) => `
      <li>
        <strong>${escapeHtml(check.label || check.id)}</strong>
        <span>${check.passed ? "passed" : "blocked"} / blocks persistence: ${check.blocking_snapshot_persistence ? "yes" : "no"}</span>
        <small>${escapeHtml(check.note || "No readiness note.")}</small>
      </li>
    `).join("");
    const safeguards = (readiness.safeguards || [])
      .slice(0, 7)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card commit-card">
        <div class="work-order-header">
          <strong>Result snapshot readiness</strong>
          <span class="quota-state quota-state--deferred">${readiness.snapshot_persistence_allowed ? "persistence on" : "persistence off"}</span>
          <p>${escapeHtml(readable(readiness.mode || "preview_only_gate"))} / replay events: ${escapeHtml(readiness.replay_event_count || 0)} / worker commit required: ${readiness.worker_commit_required ? "yes" : "no"}</p>
          <small>Run: ${escapeHtml(readiness.run_id || "unknown")} / Workspace: ${escapeHtml(readiness.workspace_id || "unknown")}</small>
        </div>
        <section>
          <p class="work-order-label">Proposed snapshot</p>
          <ul class="work-order-list">
            <li>
              <strong>${escapeHtml(snapshot.id || "snapshot_preview")}</strong>
              <span>persisted: ${snapshot.persisted ? "yes" : "no"} / publishable: ${snapshot.publishable ? "yes" : "no"}</span>
              <small>nodes: ${escapeHtml(snapshot.graph_node_count || 0)} / evidence: ${escapeHtml(snapshot.evidence_count || 0)} / challenges: ${escapeHtml(snapshot.challenge_count || 0)}</small>
            </li>
          </ul>
        </section>
        <section>
          <p class="work-order-label">Readiness checks</p>
          <ul class="work-order-list">${checks || "<li>No readiness checks returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Snapshot safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No snapshot safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderWorkerResultCommitIntent(intent) {
    const panel = byId("worker-result-commit-intent-panel");
    if (!panel) return;
    commitIntentLoaded = Boolean(intent);
    if (!intent) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Worker commit intent</strong>
            <p>Prepare a rejected commit intent to inspect idempotency and hosted blockers.</p>
          </div>
          <span class="quota-state quota-state--deferred">rejected</span>
        </article>
      `;
      return;
    }

    const blockers = (intent.blocking_checks || []).map((check) => `
      <li>
        <strong>${escapeHtml(check.label || check.id)}</strong>
        <span>${escapeHtml(check.id || "blocking_check")}</span>
        <small>${escapeHtml(check.note || "No blocker note.")}</small>
      </li>
    `).join("");
    const writes = (intent.event_writes || []).map((write) => `
      <li>
        <strong>${escapeHtml(write.event_kind || write.id)}</strong>
        <span>${escapeHtml(write.owner || "future worker")} / allowed now: ${write.allowed_now ? "yes" : "no"} / idempotency: ${write.idempotency_required ? "required" : "not required"}</span>
        <small>${escapeHtml(write.note || "No event-write note.")}</small>
      </li>
    `).join("");
    const safeguards = (intent.safeguards || [])
      .slice(0, 7)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card commit-card">
        <div class="work-order-header">
          <strong>Worker commit intent</strong>
          <span class="quota-state quota-state--deferred">${intent.commit_allowed ? "commit allowed" : "commit rejected"}</span>
          <p>${escapeHtml(readable(intent.mode || "preview_only_from_snapshot_readiness"))} / ${escapeHtml(readable(intent.status || "rejected_until_hosted_gates"))}</p>
          <small>Run: ${escapeHtml(intent.run_id || "unknown")} / Idempotency key: ${escapeHtml(intent.idempotency_key_preview || "missing")}</small>
        </div>
        <section>
          <p class="work-order-label">Future event writes</p>
          <ul class="work-order-list">${writes || "<li>No future event writes returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Blocking gates</p>
          <ul class="work-order-list">${blockers || "<li>No blocking checks returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Commit safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No commit safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderStoragePlan(plan) {
    const panel = byId("storage-boundary-panel");
    if (!panel) return;
    if (!plan) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Hosted storage plan</strong>
            <p>Store boundaries load from the Pro API; no database connections are open.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const components = (plan.components || []).slice(0, 5).map((component) => `
      <li>
        <strong>${escapeHtml(component.id)}</strong>
        <span>${escapeHtml(component.target)} / ${escapeHtml(component.owner)}</span>
        <small>${escapeHtml(component.purpose)}</small>
      </li>
    `).join("");
    const boundaries = [...(plan.tenant_boundaries || []).slice(0, 2), ...(plan.worker_ownership || []).slice(0, 2)].map((boundary) => `
      <li>
        <strong>${escapeHtml(boundary.id)}</strong>
        <span>${escapeHtml(boundary.owner)}</span>
        <small>${escapeHtml(boundary.rule)}</small>
      </li>
    `).join("");

    panel.innerHTML = `
      <article class="work-order-card storage-card">
        <div class="work-order-header">
          <strong>Hosted storage boundary</strong>
          <span class="quota-state quota-state--deferred">${plan.connections_enabled ? "connections on" : "connections off"}</span>
          <p>${escapeHtml(readable(plan.mode || "planned_no_connections"))}</p>
        </div>
        <section>
          <p class="work-order-label">Target stores</p>
          <ol class="work-order-list">${components || "<li>No storage components returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Boundaries</p>
          <ul class="work-order-list">${boundaries || "<li>No boundaries returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderCredentialVaultBoundary(boundary) {
    const panel = byId("credential-vault-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Credential vault boundary</strong>
            <p>Vault rules load from the Pro API; no credentials are accepted or stored.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const classes = (boundary.credential_classes || []).slice(0, 4).map((item) => `
      <li>
        <strong>${escapeHtml(item.label)}</strong>
        <span>${escapeHtml(readable(item.storage_status))} / ${escapeHtml(readable(item.visibility))}</span>
        <small>${escapeHtml(item.owner)}: ${escapeHtml(item.purpose)}</small>
      </li>
    `).join("");
    const accessRules = (boundary.access_rules || []).slice(0, 3).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${rule.allowed_now ? "allowed now" : "blocked now"} / ${escapeHtml(rule.actor)}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || [])
      .slice(0, 3)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card vault-card">
        <div class="work-order-header">
          <strong>Credential vault boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.connections_enabled ? "connections on" : "connections off"}</span>
          <p>${escapeHtml(readable(boundary.mode || "planned_no_secrets"))} / secret values returned: ${boundary.secret_values_returned ? "yes" : "no"}</p>
        </div>
        <section>
          <p class="work-order-label">Credential classes</p>
          <ol class="work-order-list">${classes || "<li>No credential classes returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Access rules</p>
          <ul class="work-order-list">${accessRules || "<li>No access rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Vault safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No vault safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  function renderQuotaLedgerBoundary(boundary) {
    const panel = byId("quota-ledger-panel");
    if (!panel) return;
    if (!boundary) {
      panel.innerHTML = `
        <article class="queue-meter queue-meter--empty">
          <div>
            <strong>Quota ledger boundary</strong>
            <p>Ledger and billing rules load from the Pro API; no billable usage is written.</p>
          </div>
          <span class="quota-state quota-state--deferred">planned</span>
        </article>
      `;
      return;
    }

    const lanes = (boundary.quota_lanes || []).slice(0, 5).map((lane) => `
      <li>
        <strong>${escapeHtml(lane.label)}</strong>
        <span>${escapeHtml(readable(lane.quota_owner))} / ${escapeHtml(readable(lane.accounting_status))} / billable: ${lane.billable_now ? "yes" : "no"}</span>
        <small>${escapeHtml(lane.id)}: ${escapeHtml(lane.note)}</small>
      </li>
    `).join("");
    const metering = (boundary.metering_rules || []).slice(0, 4).map((rule) => `
      <li>
        <strong>${escapeHtml(rule.id)}</strong>
        <span>${escapeHtml(rule.lane_id)} / billable: ${rule.billable_now ? "yes" : "no"}</span>
        <small>${escapeHtml(rule.requirement)}</small>
      </li>
    `).join("");
    const safeguards = (boundary.safeguards || [])
      .slice(0, 4)
      .map((guard) => `<li>${escapeHtml(guard)}</li>`)
      .join("");

    panel.innerHTML = `
      <article class="work-order-card ledger-card">
        <div class="work-order-header">
          <strong>Quota ledger boundary</strong>
          <span class="quota-state quota-state--deferred">${boundary.ledger_mutation_enabled ? "ledger mutation on" : "ledger mutation off"}</span>
          <p>${escapeHtml(readable(boundary.mode || "planned_no_mutation"))} / payment provider: ${boundary.payment_provider_connected ? "on" : "off"} / billing: ${escapeHtml(readable(boundary.billing_decision || "preview_denied"))}</p>
        </div>
        <section>
          <p class="work-order-label">Quota lanes</p>
          <ol class="work-order-list">${lanes || "<li>No quota lanes returned.</li>"}</ol>
        </section>
        <section>
          <p class="work-order-label">Metering rules</p>
          <ul class="work-order-list">${metering || "<li>No metering rules returned.</li>"}</ul>
        </section>
        <section>
          <p class="work-order-label">Billing safeguards</p>
          <ul class="work-order-list">${safeguards || "<li>No billing safeguards returned.</li>"}</ul>
        </section>
      </article>
    `;
  }

  async function refreshExecutionJobs() {
    const jobs = await fetchJson("/api/execution-jobs");
    renderExecutionJobs(jobs);
    setText("execution-queue-mode", `${jobs.length} preview job${jobs.length === 1 ? "" : "s"}`);
    return jobs;
  }

  async function fetchJson(path, options) {
    const response = await fetch(`${apiBase}${path}`, options);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async function refreshRuns(selectedId) {
    const picker = byId("run-picker");
    if (!picker) return;
    const runs = await fetchJson("/api/runs");
    picker.innerHTML = runs.map((run) => `
      <option value="${escapeHtml(run.id)}"${run.id === selectedId ? " selected" : ""}>${escapeHtml(run.title)}</option>
    `).join("");
  }

  async function loadRun(runId) {
    if (!runId) return;
    const [run, graphPayload, eventTimeline, eventReplay, reviewComparison] = await Promise.all([
      fetchJson(`/api/runs/${encodeURIComponent(runId)}`),
      fetchJson(`/api/runs/${encodeURIComponent(runId)}/graph`),
      fetchJson(`/api/runs/${encodeURIComponent(runId)}/events`),
      fetchJson(`/api/runs/${encodeURIComponent(runId)}/event-replay`),
      fetchJson(`/api/runs/${encodeURIComponent(runId)}/review-comparison`),
    ]);
    run.graph = graphPayload.graph;
    renderRun(run);
    renderRunEvents(eventTimeline);
    renderEventReplay(eventReplay);
    renderReviewComparison(reviewComparison);
    renderWorkerResultDryRun(null);
    renderResultSnapshotReadiness(null);
    renderWorkerResultCommitIntent(null);
    await refreshRuns(run.id);
    setStatus(`Loaded ${run.id}`);
  }

  async function createRun(event) {
    event.preventDefault();
    const question = byId("run-question-input")?.value || "";
    const title = byId("run-title-input")?.value || "";
    setStatus("Creating run...");
    const created = await fetchJson("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: "workspace_web",
        title: title.trim() || null,
        question,
      }),
    });
    await loadRun(created.id);
  }

  async function queuePreviewJob() {
    const question = currentRun?.question || byId("run-question-input")?.value || "";
    setText("execution-queue-status", "Queueing preview job...");
    const job = await fetchJson("/api/execution-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: currentRun?.workspace_id || "workspace_web",
        query: question,
        scenario: "auto",
        source_policy: "balanced",
      }),
    });
    setText("execution-queue-status", `Queued ${job.id}; provider execution remains disabled.`);
    await refreshExecutionJobs();
    await inspectWorkOrder(job.id);
  }

  async function runProviderAdapterDryRun() {
    const question = currentRun?.question || byId("run-question-input")?.value || "";
    setText("provider-adapter-dry-run-status", "Running adapter dry-run...");
    const result = await fetchJson("/api/provider-adapter/dry-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: currentRun?.workspace_id || "workspace_web",
        query: question,
        provider_lane_id: "uploaded_evidence_lane",
        source_policy: "balanced",
      }),
    });
    renderProviderAdapterDryRun(result);
    setText(
      "provider-adapter-dry-run-status",
      `Dry-run loaded for ${result.provider_lane_id}; provider calls remain disabled.`,
    );
  }

  async function runProviderAdapterGateCheck() {
    setText("live-adapter-gate-check-status", "Checking live adapter gates...");
    const result = await fetchJson("/api/provider-adapter/gate-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: currentRun?.workspace_id || "workspace_web",
        candidate_id: selectedAdapterCandidateId,
        dry_run_observed: Boolean(lastAdapterDryRun),
        auth_context_observed: workspaceAccessLoaded,
        quota_owner_confirmed: providerStatusLoaded,
        event_timeline_observed: runEventsLoaded,
      }),
    });
    renderProviderAdapterGateCheck(result);
    setText(
      "live-adapter-gate-check-status",
      `Gate check denied live execution for ${result.candidate_id}; ${result.blocking_reasons?.length || 0} blockers remain.`,
    );
  }

  async function checkExecutionReadiness() {
    const runId = currentRun?.id || "run_semiconductor_controls_001";
    setText("execution-readiness-status", "Checking composed execution readiness...");
    const result = await fetchJson("/api/execution-readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: currentRun?.workspace_id || "workspace_demo",
        run_id: runId,
        candidate_id: selectedAdapterCandidateId,
        dry_run_observed: Boolean(lastAdapterDryRun),
        auth_context_observed: workspaceAccessLoaded,
        quota_owner_confirmed: providerStatusLoaded,
        event_timeline_observed: runEventsLoaded,
        work_order_observed: workOrderLoaded,
        commit_intent_observed: commitIntentLoaded,
      }),
    });
    renderExecutionReadiness(result);
    setText(
      "execution-readiness-status",
      `Execution remains ${result.execution_allowed ? "allowed" : "denied"}; ${result.blocking_reasons?.length || 0} blockers returned.`,
    );
  }

  async function checkExecutionAdmission() {
    const runId = currentRun?.id || "run_semiconductor_controls_001";
    setText("execution-admission-status", "Checking server-side execution admission...");
    const decision = await fetchJson("/api/execution-admission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: currentRun?.workspace_id || "workspace_demo",
        run_id: runId,
        job_id: lastInspectedJobId,
        action: "execute_provider_calls",
      }),
    });
    renderExecutionAdmission(decision);
    setText(
      "execution-admission-status",
      `Admission remains ${decision.admitted ? "allowed" : "denied"}; ${decision.gates?.length || 0} gates returned.`,
    );
  }

  async function runWorkerResultDryRun() {
    const runId = currentRun?.id;
    if (!runId) {
      throw new Error("No run selected for result dry-run.");
    }
    setText("worker-result-dry-run-status", "Running worker result dry-run...");
    const result = await fetchJson(`/api/runs/${encodeURIComponent(runId)}/worker-result-dry-run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    renderWorkerResultDryRun(result);
    setText(
      "worker-result-dry-run-status",
      `Dry-run loaded from ${result.replay_event_count || 0} replay event(s); result writes remain disabled.`,
    );
  }

  async function checkResultSnapshotReadiness() {
    const runId = currentRun?.id;
    if (!runId) {
      throw new Error("No run selected for result snapshot readiness.");
    }
    setText("result-snapshot-readiness-status", "Checking result snapshot gate...");
    const readiness = await fetchJson(`/api/runs/${encodeURIComponent(runId)}/result-snapshot-readiness`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    renderResultSnapshotReadiness(readiness);
    setText(
      "result-snapshot-readiness-status",
      `Snapshot persistence remains ${readiness.snapshot_persistence_allowed ? "allowed" : "blocked"}; ${readiness.readiness_checks?.length || 0} checks returned.`,
    );
  }

  async function prepareWorkerResultCommitIntent() {
    const runId = currentRun?.id;
    if (!runId) {
      throw new Error("No run selected for worker result commit intent.");
    }
    setText("worker-result-commit-intent-status", "Preparing worker commit intent...");
    const intent = await fetchJson(`/api/runs/${encodeURIComponent(runId)}/worker-result-commit-intent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    renderWorkerResultCommitIntent(intent);
    setText(
      "worker-result-commit-intent-status",
      `Commit intent remains ${intent.commit_allowed ? "allowed" : "rejected"}; ${intent.blocking_checks?.length || 0} blockers returned.`,
    );
  }

  async function checkWorkspaceAccessGate() {
    const action = byId("workspace-access-action")?.value || "inspect_knowledge_graph";
    const resource = action === "execute_provider_calls"
      ? "ofoxai_model_candidate"
      : (currentRun?.id || "run_semiconductor_controls_001");
    setText("workspace-access-gate-status", "Checking server access gate...");
    const decision = await fetchJson("/api/workspace/access-gate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: "workspace_demo",
        action,
        resource,
      }),
    });
    renderWorkspaceAccessGate(decision);
    setText(
      "workspace-access-gate-status",
      `Gate ${decision.allowed ? "allows preview access" : "denies hosted access"} for ${readable(decision.action)}.`,
    );
  }

  byId("run-create-form")?.addEventListener("submit", (event) => {
    createRun(event).catch((error) => setStatus(`API error: ${error.message}`));
  });
  byId("load-run-button")?.addEventListener("click", () => {
    loadRun(byId("run-picker")?.value).catch((error) => setStatus(`API error: ${error.message}`));
  });
  byId("run-picker")?.addEventListener("change", (event) => {
    loadRun(event.target.value).catch((error) => setStatus(`API error: ${error.message}`));
  });
  byId("queue-preview-button")?.addEventListener("click", () => {
    queuePreviewJob().catch((error) => setText("execution-queue-status", `Queue error: ${error.message}`));
  });
  byId("worker-result-dry-run-button")?.addEventListener("click", () => {
    runWorkerResultDryRun()
      .catch((error) => setText("worker-result-dry-run-status", `Result dry-run error: ${error.message}`));
  });
  byId("result-snapshot-readiness-button")?.addEventListener("click", () => {
    checkResultSnapshotReadiness()
      .catch((error) => setText("result-snapshot-readiness-status", `Snapshot gate error: ${error.message}`));
  });
  byId("worker-result-commit-intent-button")?.addEventListener("click", () => {
    prepareWorkerResultCommitIntent()
      .catch((error) => setText("worker-result-commit-intent-status", `Commit intent error: ${error.message}`));
  });
  byId("workspace-access-gate-button")?.addEventListener("click", () => {
    checkWorkspaceAccessGate()
      .catch((error) => setText("workspace-access-gate-status", `Access gate error: ${error.message}`));
  });
  byId("provider-adapter-dry-run-button")?.addEventListener("click", () => {
    runProviderAdapterDryRun()
      .catch((error) => setText("provider-adapter-dry-run-status", `Dry-run error: ${error.message}`));
  });
  byId("live-adapter-gate-check-button")?.addEventListener("click", () => {
    runProviderAdapterGateCheck()
      .catch((error) => setText("live-adapter-gate-check-status", `Gate check error: ${error.message}`));
  });
  byId("execution-readiness-button")?.addEventListener("click", () => {
    checkExecutionReadiness()
      .catch((error) => setText("execution-readiness-status", `Readiness error: ${error.message}`));
  });
  byId("execution-admission-button")?.addEventListener("click", () => {
    checkExecutionAdmission()
      .catch((error) => setText("execution-admission-status", `Admission error: ${error.message}`));
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-review-kind][data-review-id]");
    if (!button) return;
    focusReviewItem(button.dataset.reviewKind, button.dataset.reviewId);
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-work-order-job-id]");
    if (!button) return;
    inspectWorkOrder(button.dataset.workOrderJobId)
      .catch((error) => setText("execution-queue-status", `Work order error: ${error.message}`));
  });

  renderRun(seed);
  renderWorkspaceAccess(null);
  renderWorkspaceAccessGate(null);
  renderRunEvents(null);
  renderEventReplay(null);
  renderReviewComparison(null);
  renderProviderStatus(providerSeed);
  renderProviderAdapterContract(null);
  renderProviderAdapterDryRun(null);
  renderProviderAdapterCandidates(null);
  renderProviderAdapterGateCheck(null);
  renderExecutionReadiness(null);
  renderExecutionAdmission(null);
  renderExecutionPreflightBoundary(null);
  renderExecutionJobs([]);
  renderWorkOrder(null);
  renderExecutionHandoffPreview(null);
  renderExecutionIntentPreview(null);
  renderExecutionIntentStoreBoundary(null);
  renderExecutionLifecycle(null);
  renderWorkerLeaseBoundary(null);
  renderResultCommitBoundary(null);
  renderWorkerResultDryRun(null);
  renderResultSnapshotReadiness(null);
  renderWorkerResultCommitIntent(null);
  renderStoragePlan(null);
  renderCredentialVaultBoundary(null);
  renderQuotaLedgerBoundary(null);
  fetchJson("/api/workspace/access-context")
    .then(renderWorkspaceAccess)
    .catch(() => {
      renderWorkspaceAccess(null);
    });
  fetchJson(`/api/runs/${encodeURIComponent(seed.id)}/events`)
    .then(renderRunEvents)
    .catch(() => {
      renderRunEvents(null);
    });
  fetchJson(`/api/runs/${encodeURIComponent(seed.id)}/event-replay`)
    .then(renderEventReplay)
    .catch(() => {
      renderEventReplay(null);
    });
  fetchJson(`/api/runs/${encodeURIComponent(seed.id)}/review-comparison`)
    .then(renderReviewComparison)
    .catch(() => {
      renderReviewComparison(null);
    });
  fetchJson("/api/provider-status")
    .then(renderProviderStatus)
    .catch(() => {
      renderProviderStatus(providerSeed);
    });
  fetchJson("/api/provider-adapter-contract")
    .then(renderProviderAdapterContract)
    .catch(() => {
      renderProviderAdapterContract(null);
    });
  fetchJson("/api/provider-adapter/candidates")
    .then(renderProviderAdapterCandidates)
    .catch(() => {
      renderProviderAdapterCandidates(null);
    });
  fetchJson("/api/execution-lifecycle")
    .then(renderExecutionLifecycle)
    .catch(() => {
      renderExecutionLifecycle(null);
    });
  fetchJson("/api/execution-preflight-boundary")
    .then(renderExecutionPreflightBoundary)
    .catch(() => {
      renderExecutionPreflightBoundary(null);
    });
  fetchJson("/api/worker-lease-boundary")
    .then(renderWorkerLeaseBoundary)
    .catch(() => {
      renderWorkerLeaseBoundary(null);
    });
  fetchJson("/api/execution-intent-store-boundary")
    .then(renderExecutionIntentStoreBoundary)
    .catch(() => {
      renderExecutionIntentStoreBoundary(null);
    });
  fetchJson("/api/result-commit-boundary")
    .then(renderResultCommitBoundary)
    .catch(() => {
      renderResultCommitBoundary(null);
    });
  fetchJson("/api/storage-plan")
    .then(renderStoragePlan)
    .catch(() => {
      renderStoragePlan(null);
    });
  fetchJson("/api/credential-vault-boundary")
    .then(renderCredentialVaultBoundary)
    .catch(() => {
      renderCredentialVaultBoundary(null);
    });
  fetchJson("/api/quota-ledger-boundary")
    .then(renderQuotaLedgerBoundary)
    .catch(() => {
      renderQuotaLedgerBoundary(null);
    });
  refreshExecutionJobs().catch(() => {
    setText("execution-queue-status", `Queue API offline: start retrocause-pro-api at ${apiBase}`);
  });
  refreshRuns(seed.id).catch(() => {
    setStatus(`API offline: start retrocause-pro-api at ${apiBase}`);
  });
})();
"#
}

fn wire_path(source: &GraphNode, target: &GraphNode) -> String {
    let start_x = i32::from(source.x) + 168;
    let start_y = i32::from(source.y) + 86;
    let end_x = i32::from(target.x);
    let end_y = i32::from(target.y) + 86;
    let control_x = (start_x + end_x) / 2;
    format!("M {start_x} {start_y} C {control_x} {start_y}, {control_x} {end_y}, {end_x} {end_y}")
}

fn percent(value: f32) -> String {
    format!("{:.0}%", value * 100.0)
}

fn node_kind_label(kind: NodeKind) -> &'static str {
    match kind {
        NodeKind::Driver => "driver",
        NodeKind::Enabler => "enabler",
        NodeKind::Risk => "risk",
        NodeKind::Outcome => "outcome",
    }
}

fn run_status_label(status: RunStatus) -> &'static str {
    match status {
        RunStatus::Queued => "queued",
        RunStatus::Running => "running",
        RunStatus::CoolingDown => "cooling down",
        RunStatus::PartialLive => "partial live",
        RunStatus::NeedsFollowup => "needs follow-up",
        RunStatus::ReadyForReview => "ready for review",
        RunStatus::Blocked => "blocked",
    }
}

fn source_status_label(status: SourceStatus) -> &'static str {
    match status {
        SourceStatus::Verified => "verified",
        SourceStatus::Cached => "cached",
        SourceStatus::RateLimited => "rate_limited",
    }
}

fn ledger_category_label(category: retrocause_pro_domain::LedgerCategory) -> &'static str {
    match category {
        retrocause_pro_domain::LedgerCategory::Model => "model",
        retrocause_pro_domain::LedgerCategory::Search => "search",
        retrocause_pro_domain::LedgerCategory::Evidence => "evidence",
    }
}

fn quota_owner_label(owner: retrocause_pro_domain::QuotaOwner) -> &'static str {
    match owner {
        retrocause_pro_domain::QuotaOwner::ManagedPro => "managed Pro",
        retrocause_pro_domain::QuotaOwner::Workspace => "workspace",
        retrocause_pro_domain::QuotaOwner::UserProvided => "user provided",
    }
}

fn credential_policy_label(policy: retrocause_pro_domain::CredentialPolicy) -> &'static str {
    match policy {
        retrocause_pro_domain::CredentialPolicy::ManagedProLater => "managed later",
        retrocause_pro_domain::CredentialPolicy::WorkspaceManagedLater => "workspace later",
        retrocause_pro_domain::CredentialPolicy::ByokLater => "BYOK later",
        retrocause_pro_domain::CredentialPolicy::UserEvidenceOnly => "user evidence only",
    }
}

fn provider_readiness_label(readiness: retrocause_pro_domain::ProviderReadiness) -> &'static str {
    match readiness {
        retrocause_pro_domain::ProviderReadiness::Ready => "ready",
        retrocause_pro_domain::ProviderReadiness::NotConfigured => "not_configured",
        retrocause_pro_domain::ProviderReadiness::CoolingDown => "cooling_down",
        retrocause_pro_domain::ProviderReadiness::Deferred => "deferred",
    }
}

fn provider_status_mode_label(mode: retrocause_pro_domain::ProviderStatusMode) -> &'static str {
    match mode {
        retrocause_pro_domain::ProviderStatusMode::LocalAlphaNoCredentials => {
            "local alpha / no credentials"
        }
    }
}

fn evidence_stance_label(stance: EvidenceStance) -> &'static str {
    match stance {
        EvidenceStance::Supports => "supports",
        EvidenceStance::Refutes => "refutes",
        EvidenceStance::Context => "context",
    }
}

fn evidence_freshness_label(freshness: EvidenceFreshness) -> &'static str {
    match freshness {
        EvidenceFreshness::Fresh => "fresh",
        EvidenceFreshness::Cached => "cached",
        EvidenceFreshness::UserProvided => "user evidence",
    }
}

fn challenge_status_label(status: ChallengeStatus) -> &'static str {
    match status {
        ChallengeStatus::Checked => "checked",
        ChallengeStatus::NeedsPrimarySource => "needs primary source",
        ChallengeStatus::MissingCounterevidence => "missing counterevidence",
    }
}

fn step_state_label(state: StepState) -> &'static str {
    match state {
        StepState::Done => "done",
        StepState::Watching => "watching",
        StepState::Waiting => "waiting",
    }
}

fn styles() -> &'static str {
    r#"
:root {
  color-scheme: dark;
  --bg: oklch(0.16 0.016 148);
  --bg-lift: oklch(0.2 0.018 148);
  --panel: oklch(0.24 0.018 148 / 0.9);
  --panel-hard: oklch(0.29 0.02 148 / 0.96);
  --line: oklch(0.74 0.075 96);
  --text: oklch(0.93 0.01 118);
  --muted: oklch(0.72 0.026 132);
  --accent: oklch(0.78 0.09 95);
  --danger: oklch(0.66 0.13 27);
  --driver: oklch(0.76 0.08 95);
  --enabler: oklch(0.78 0.06 168);
  --risk: oklch(0.7 0.12 27);
  --outcome: oklch(0.76 0.05 205);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  background:
    linear-gradient(color-mix(in oklch, var(--text) 4%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in oklch, var(--text) 4%, transparent) 1px, transparent 1px),
    var(--bg);
  background-size: 36px 36px, 36px 36px, auto;
  color: var(--text);
}

.field-shell {
  min-height: 100vh;
  padding: 0.75rem;
}

.graph-field {
  min-height: calc(100vh - 1.5rem);
  position: relative;
  overflow: hidden;
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 8px;
  background:
    linear-gradient(115deg, color-mix(in oklch, var(--bg-lift) 88%, black), var(--bg));
  box-shadow: 0 30px 70px rgba(0, 0, 0, 0.32);
}

.hud,
.question-band,
.graph-inspector,
.focus-docket,
.source-pulse,
.quota-console,
.execution-console,
.evidence-dock,
.command-deck,
.seed-drawer {
  position: absolute;
  z-index: 5;
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel) 92%, black);
  backdrop-filter: blur(14px);
}

.hud--top {
  top: 0.9rem;
  left: 0.9rem;
  right: 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1rem;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-mark {
  width: 2.6rem;
  height: 2.6rem;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--accent);
  color: oklch(0.18 0.018 148);
  font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 700;
}

.run-state,
.command-clusters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.state-token,
.command-clusters span {
  border: 1px solid color-mix(in oklch, var(--text) 11%, transparent);
  border-radius: 999px;
  padding: 0.32rem 0.62rem;
  color: color-mix(in oklch, var(--text) 88%, var(--muted));
  background: color-mix(in oklch, var(--panel-hard) 82%, black);
  font-size: 0.78rem;
}

.state-token--live {
  color: oklch(0.9 0.05 128);
}

.question-band {
  top: 5.5rem;
  left: 0.9rem;
  max-width: min(420px, calc(100% - 1.8rem));
  max-height: calc(100vh - 7rem);
  overflow: auto;
  padding: 0.95rem 1rem;
  display: grid;
  gap: 0.55rem;
}

.run-console {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.25rem;
}

.run-console label {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.run-console textarea,
.run-console input,
.run-console select {
  width: 100%;
  border: 1px solid color-mix(in oklch, var(--text) 12%, transparent);
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 80%, black);
  color: var(--text);
  font: inherit;
  padding: 0.62rem 0.7rem;
}

.run-console button {
  border: 1px solid color-mix(in oklch, var(--accent) 32%, transparent);
  border-radius: 8px;
  background: color-mix(in oklch, var(--accent) 82%, black);
  color: oklch(0.16 0.016 148);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.62rem 0.8rem;
}

.create-grid {
  display: grid;
  gap: 0.5rem;
  grid-template-columns: minmax(0, 1fr) auto;
}

.console-status {
  color: var(--muted);
  font-size: 0.78rem;
}

.graph-viewport {
  position: absolute;
  inset: 17rem 1rem 5.7rem;
  overflow: auto;
  border-radius: 8px;
  background:
    linear-gradient(color-mix(in oklch, var(--text) 5%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in oklch, var(--text) 5%, transparent) 1px, transparent 1px),
    color-mix(in oklch, var(--bg-lift) 88%, black);
  background-size: 42px 42px, 42px 42px, auto;
  border: 1px solid color-mix(in oklch, var(--text) 8%, transparent);
}

.axis-line {
  position: absolute;
  background: color-mix(in oklch, var(--accent) 28%, transparent);
  opacity: 0.35;
}

.axis-line--x {
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
}

.axis-line--y {
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
}

.graph-wires {
  position: absolute;
  left: 0;
  top: 0;
  width: 1220px;
  height: 720px;
}

#graph-nodes {
  position: absolute;
  inset: 0;
  width: 1220px;
  height: 720px;
}

.wire-shadow {
  fill: none;
  stroke: rgba(0, 0, 0, 0.55);
  stroke-width: 7;
  stroke-linecap: round;
}

.wire {
  fill: none;
  stroke: color-mix(in oklch, var(--line) 78%, var(--text));
  stroke-width: 2.4;
  stroke-linecap: round;
}

.wire-label {
  fill: color-mix(in oklch, var(--text) 72%, var(--muted));
  font-size: 11px;
}

.graph-node {
  position: absolute;
  width: 248px;
  padding: 0.86rem;
  display: grid;
  gap: 0.5rem;
  border-radius: 8px;
  border: 1px solid color-mix(in oklch, white 22%, transparent);
  color: oklch(0.18 0.018 148);
  cursor: pointer;
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.28);
}

.graph-node.driver { background: color-mix(in oklch, var(--driver) 88%, white); }
.graph-node.enabler { background: color-mix(in oklch, var(--enabler) 88%, white); }
.graph-node.risk { background: color-mix(in oklch, var(--risk) 86%, white); }
.graph-node.outcome { background: color-mix(in oklch, var(--outcome) 88%, white); }
.graph-node.is-selected {
  outline: 3px solid color-mix(in oklch, var(--accent) 88%, white);
  outline-offset: 4px;
}

.node-head,
.source-meter {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: baseline;
}

.node-kind,
.eyebrow {
  margin: 0;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.node-kind {
  color: color-mix(in oklch, black 58%, transparent);
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1,
h2,
h3 {
  font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 600;
}

h1 { font-size: 1.34rem; }
h2 { font-size: 1.1rem; }
h3 { font-size: 0.98rem; }

p {
  line-height: 1.55;
  color: color-mix(in oklch, var(--text) 84%, var(--muted));
}

.graph-node p {
  color: color-mix(in oklch, black 76%, transparent);
}

.graph-inspector {
  left: 1rem;
  top: 19.4rem;
  width: min(340px, calc(100% - 2rem));
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

.inspector-card {
  display: grid;
  gap: 0.6rem;
}

.inspector-head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
}

.inspector-head span {
  color: var(--accent);
  font-weight: 700;
}

.inspector-links {
  display: grid;
  gap: 0.28rem;
}

.inspector-links ul {
  display: grid;
  gap: 0.22rem;
  margin: 0;
  padding-left: 1.05rem;
}

.inspector-links p,
.inspector-links li {
  color: color-mix(in oklch, var(--text) 76%, var(--muted));
  font-size: 0.78rem;
}

.focus-link {
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 65%, black);
  color: color-mix(in oklch, var(--text) 86%, var(--muted));
  cursor: pointer;
  font: inherit;
  padding: 0.34rem 0.48rem;
  text-align: left;
}

.focus-docket {
  left: 1rem;
  bottom: 6.1rem;
  width: min(360px, calc(100% - 2rem));
  padding: 0.9rem 1rem;
}

.focus-docket ol {
  margin: 0.7rem 0 0;
  padding-left: 1.15rem;
  display: grid;
  gap: 0.62rem;
}

.source-pulse {
  right: 1rem;
  top: 5.5rem;
  width: min(340px, calc(100% - 2rem));
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

.quota-console {
  right: 1rem;
  top: 19.2rem;
  width: min(380px, calc(100% - 2rem));
  max-height: 14rem;
  overflow: auto;
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

.execution-console {
  right: 1rem;
  top: 35.2rem;
  z-index: 7;
  width: min(380px, calc(100% - 2rem));
  max-height: 13rem;
  overflow: auto;
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

.quota-console button,
.execution-console button {
  border: 1px solid color-mix(in oklch, var(--accent) 32%, transparent);
  border-radius: 8px;
  background: color-mix(in oklch, var(--accent) 82%, black);
  color: oklch(0.16 0.016 148);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.62rem 0.8rem;
}

#source-list {
  display: grid;
  gap: 0.65rem;
}

#provider-status-list {
  display: grid;
  gap: 0.65rem;
}

#provider-adapter-panel {
  display: grid;
  gap: 0.65rem;
}

#provider-adapter-dry-run-result {
  display: grid;
  gap: 0.65rem;
}

#provider-adapter-candidate-panel,
#live-adapter-gate-check-result,
#execution-readiness-result,
#execution-preflight-panel {
  display: grid;
  gap: 0.65rem;
}

#workspace-access-panel,
#workspace-access-gate-panel {
  display: grid;
  gap: 0.65rem;
}

#run-event-panel,
#event-replay-panel {
  display: grid;
  gap: 0.65rem;
}

#review-comparison-panel {
  display: grid;
  gap: 0.65rem;
}

#execution-job-list {
  display: grid;
  gap: 0.65rem;
}

#execution-work-order-detail,
#execution-admission-panel,
#execution-handoff-panel,
#execution-intent-panel,
#execution-intent-store-panel,
#execution-lifecycle-panel,
#worker-lease-panel,
#result-commit-panel,
#worker-result-dry-run-panel,
#result-snapshot-readiness-panel,
#worker-result-commit-intent-panel,
#storage-boundary-panel,
#credential-vault-panel,
#quota-ledger-panel {
  display: grid;
  gap: 0.65rem;
}

.queue-action {
  margin-top: 0.48rem;
  width: 100%;
}

.work-order-card {
  display: grid;
  gap: 0.72rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.access-card {
  display: grid;
  gap: 0.65rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.52 0.07 175));
}

.event-card {
  display: grid;
  gap: 0.65rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.58 0.07 110));
}

.review-card {
  display: grid;
  gap: 0.65rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.58 0.06 250));
}

.lifecycle-card {
  background: color-mix(in oklch, var(--panel-hard) 68%, var(--accent));
}

.lease-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.55 0.08 35));
}

.commit-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.54 0.07 125));
}

.storage-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.47 0.08 250));
}

.vault-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.52 0.07 310));
}

.ledger-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.62 0.07 75));
}

.intent-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.56 0.08 210));
}

.admission-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.48 0.07 185));
}

.adapter-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.58 0.08 190));
}

.work-order-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.32rem 0.7rem;
  align-items: start;
}

.work-order-header p,
.work-order-header small {
  grid-column: 1 / -1;
}

.work-order-label {
  margin-bottom: 0.32rem;
  color: color-mix(in oklch, var(--text) 78%, var(--muted));
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.work-order-list {
  display: grid;
  gap: 0.42rem;
  margin: 0;
  padding-left: 1.1rem;
}

.work-order-list li {
  min-width: 0;
}

.work-order-list li strong,
.work-order-list li span,
.work-order-list li small {
  display: block;
}

.evidence-dock {
  right: 1rem;
  top: 49.2rem;
  width: min(360px, calc(100% - 2rem));
  max-height: 18rem;
  overflow: auto;
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

.source-meter {
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.quota-meter {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.7rem;
  align-items: start;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.queue-meter {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.7rem;
  align-items: start;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.evidence-chip {
  display: grid;
  gap: 0.42rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.evidence-chip p,
.evidence-chip span,
.access-card small,
.quota-meter small,
.queue-meter small,
.work-order-header small,
.work-order-list li span,
.work-order-list li small,
.verdict span,
.focus-docket li span,
.graph-node small,
.challenge-strip span {
  color: color-mix(in oklch, var(--text) 72%, var(--muted));
  font-size: 0.78rem;
}

.challenge-strip {
  display: grid;
  gap: 0.42rem;
}

.challenge-strip span {
  border-radius: 8px;
  padding: 0.36rem 0.42rem;
}

.evidence-chip.is-focused,
.challenge-strip span.is-focused {
  outline: 2px solid color-mix(in oklch, var(--accent) 86%, white);
  outline-offset: 3px;
  background: color-mix(in oklch, var(--panel-hard) 88%, var(--accent));
}

.focus-docket li {
  display: grid;
  gap: 0.18rem;
}

.source-meter p {
  font-size: 0.82rem;
  margin-top: 0.22rem;
}

.quota-meter p {
  font-size: 0.8rem;
  margin-top: 0.22rem;
}

.queue-meter p {
  font-size: 0.8rem;
  margin-top: 0.22rem;
}

.quota-state {
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 999px;
  color: color-mix(in oklch, var(--text) 82%, var(--muted));
  font-size: 0.72rem;
  padding: 0.24rem 0.42rem;
  white-space: nowrap;
}

.quota-state--ready { color: oklch(0.86 0.08 145); }
.quota-state--not_configured { color: oklch(0.83 0.08 92); }
.quota-state--cooling_down { color: var(--danger); }
.quota-state--deferred { color: color-mix(in oklch, var(--text) 72%, var(--muted)); }

.status-dot {
  width: 0.7rem;
  height: 0.7rem;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--muted);
}

.status-dot--verified { background: oklch(0.74 0.12 150); }
.status-dot--cached { background: oklch(0.75 0.08 205); }
.status-dot--rate_limited { background: var(--danger); }

.command-deck {
  left: 1rem;
  right: 1rem;
  bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.86rem 1rem;
}

.verdict {
  display: grid;
  gap: 0.25rem;
}

.seed-drawer {
  right: 1rem;
  bottom: 6.1rem;
  width: min(420px, calc(100% - 2rem));
  padding: 0.8rem 0.9rem;
}

.seed-drawer summary {
  cursor: pointer;
  font-weight: 700;
}

.seed-drawer pre {
  max-height: 220px;
  overflow: auto;
  margin: 0.7rem 0 0;
  padding: 0.75rem;
  border-radius: 8px;
  background: color-mix(in oklch, black 24%, var(--panel-hard));
  color: color-mix(in oklch, var(--text) 88%, var(--muted));
  font-size: 0.78rem;
}

@media (max-width: 1080px) {
  .hud--top,
  .command-deck {
    align-items: start;
    flex-direction: column;
  }

  .graph-field {
    overflow: visible;
    display: grid;
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .hud,
  .question-band,
  .graph-inspector,
  .focus-docket,
  .source-pulse,
  .quota-console,
  .execution-console,
  .evidence-dock,
  .command-deck,
  .seed-drawer,
  .graph-viewport {
    position: relative;
    inset: auto;
    width: auto;
  }

  .graph-viewport {
    min-height: 980px;
  }

  .execution-console {
    max-height: none;
    overflow: visible;
  }

  .quota-console {
    max-height: none;
    overflow: visible;
  }
}
"#
}

#[tokio::main]
async fn main() {
    let port = std::env::var("PRO_WEB_PORT")
        .ok()
        .and_then(|value| value.parse::<u16>().ok())
        .unwrap_or(3007);
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", port))
        .await
        .expect("bind pro web listener");

    println!("RetroCause Pro Web listening on http://127.0.0.1:{port}");
    axum::serve(listener, router())
        .await
        .expect("serve pro web");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wire_path_contains_expected_curve_command() {
        let run = sample_run();
        let path = wire_path(&run.graph.nodes[0], &run.graph.nodes[1]);
        assert!(path.starts_with('M'));
        assert!(path.contains('C'));
    }

    #[test]
    fn rendered_page_contains_graph_first_sections() {
        let page = render_page(&sample_run(), "http://127.0.0.1:8787").into_string();
        assert!(page.contains("Knowledge graph operating field"));
        assert!(page.contains("graph-viewport"));
        assert!(page.contains("node-inspector"));
        assert!(page.contains("data-node-id"));
        assert!(page.contains("data-evidence-id"));
        assert!(page.contains("data-challenge-id"));
        assert!(page.contains("data-review-kind"));
        assert!(page.contains("function selectNode"));
        assert!(page.contains("function focusReviewItem"));
        assert!(page.contains("run-create-form"));
        assert!(page.contains("workspace-access-panel"));
        assert!(page.contains("workspace-access-gate-panel"));
        assert!(page.contains("workspace-access-gate-button"));
        assert!(page.contains("/api/workspace/access-context"));
        assert!(page.contains("/api/workspace/access-gate"));
        assert!(page.contains("function renderWorkspaceAccess"));
        assert!(page.contains("function renderWorkspaceAccessGate"));
        assert!(page.contains("function checkWorkspaceAccessGate"));
        assert!(page.contains("run-event-panel"));
        assert!(page.contains("/api/runs/${encodeURIComponent(runId)}/events"));
        assert!(page.contains("function renderRunEvents"));
        assert!(page.contains("Run event timeline"));
        assert!(page.contains("event-replay-panel"));
        assert!(page.contains("/api/runs/${encodeURIComponent(runId)}/event-replay"));
        assert!(page.contains("function renderEventReplay"));
        assert!(page.contains("Event replay"));
        assert!(page.contains("review-comparison-panel"));
        assert!(page.contains("/api/runs/${encodeURIComponent(runId)}/review-comparison"));
        assert!(page.contains("function renderReviewComparison"));
        assert!(page.contains("Review comparison"));
        assert!(page.contains("provider-status-list"));
        assert!(page.contains("provider-adapter-panel"));
        assert!(page.contains("provider-adapter-dry-run-button"));
        assert!(page.contains("provider-adapter-dry-run-result"));
        assert!(page.contains("provider-adapter-candidate-panel"));
        assert!(page.contains("live-adapter-gate-check-button"));
        assert!(page.contains("live-adapter-gate-check-result"));
        assert!(page.contains("execution-readiness-button"));
        assert!(page.contains("execution-readiness-result"));
        assert!(page.contains("execution-admission-button"));
        assert!(page.contains("execution-admission-panel"));
        assert!(page.contains("execution-preflight-panel"));
        assert!(page.contains("/api/provider-status"));
        assert!(page.contains("/api/provider-adapter-contract"));
        assert!(page.contains("/api/provider-adapter/dry-run"));
        assert!(page.contains("/api/provider-adapter/candidates"));
        assert!(page.contains("/api/provider-adapter/gate-check"));
        assert!(page.contains("/api/execution-readiness"));
        assert!(page.contains("/api/execution-admission"));
        assert!(page.contains("/api/execution-preflight-boundary"));
        assert!(page.contains("execution-job-list"));
        assert!(page.contains("execution-work-order-detail"));
        assert!(page.contains("execution-handoff-panel"));
        assert!(page.contains("execution-intent-panel"));
        assert!(page.contains("execution-intent-store-panel"));
        assert!(page.contains("execution-lifecycle-panel"));
        assert!(page.contains("worker-lease-panel"));
        assert!(page.contains("result-commit-panel"));
        assert!(page.contains("worker-result-dry-run-panel"));
        assert!(page.contains("worker-result-dry-run-button"));
        assert!(page.contains("result-snapshot-readiness-panel"));
        assert!(page.contains("result-snapshot-readiness-button"));
        assert!(page.contains("worker-result-commit-intent-panel"));
        assert!(page.contains("worker-result-commit-intent-button"));
        assert!(page.contains("storage-boundary-panel"));
        assert!(page.contains("credential-vault-panel"));
        assert!(page.contains("quota-ledger-panel"));
        assert!(page.contains("/api/execution-jobs"));
        assert!(page.contains("/work-order"));
        assert!(page.contains("/handoff-preview"));
        assert!(page.contains("/intent-preview"));
        assert!(page.contains("/api/execution-intent-store-boundary"));
        assert!(page.contains("/api/execution-lifecycle"));
        assert!(page.contains("/api/worker-lease-boundary"));
        assert!(page.contains("/api/result-commit-boundary"));
        assert!(page.contains("/api/runs/${encodeURIComponent(runId)}/worker-result-dry-run"));
        assert!(page.contains("/api/runs/${encodeURIComponent(runId)}/result-snapshot-readiness"));
        assert!(
            page.contains("/api/runs/${encodeURIComponent(runId)}/worker-result-commit-intent")
        );
        assert!(page.contains("/api/storage-plan"));
        assert!(page.contains("/api/credential-vault-boundary"));
        assert!(page.contains("/api/quota-ledger-boundary"));
        assert!(page.contains("data-work-order-job-id"));
        assert!(page.contains("function renderWorkOrder"));
        assert!(page.contains("function renderExecutionHandoffPreview"));
        assert!(page.contains("function renderExecutionIntentPreview"));
        assert!(page.contains("function renderExecutionIntentStoreBoundary"));
        assert!(page.contains("function renderExecutionLifecycle"));
        assert!(page.contains("function renderWorkerLeaseBoundary"));
        assert!(page.contains("function renderResultCommitBoundary"));
        assert!(page.contains("function renderWorkerResultDryRun"));
        assert!(page.contains("function runWorkerResultDryRun"));
        assert!(page.contains("function renderResultSnapshotReadiness"));
        assert!(page.contains("function checkResultSnapshotReadiness"));
        assert!(page.contains("function renderWorkerResultCommitIntent"));
        assert!(page.contains("function prepareWorkerResultCommitIntent"));
        assert!(page.contains("function renderStoragePlan"));
        assert!(page.contains("function renderCredentialVaultBoundary"));
        assert!(page.contains("function renderQuotaLedgerBoundary"));
        assert!(page.contains("function renderProviderAdapterContract"));
        assert!(page.contains("function renderProviderAdapterDryRun"));
        assert!(page.contains("function renderProviderAdapterCandidates"));
        assert!(page.contains("function renderProviderAdapterGateCheck"));
        assert!(page.contains("function renderExecutionReadiness"));
        assert!(page.contains("function renderExecutionAdmission"));
        assert!(page.contains("function renderExecutionPreflightBoundary"));
        assert!(page.contains("function runProviderAdapterDryRun"));
        assert!(page.contains("function runProviderAdapterGateCheck"));
        assert!(page.contains("function checkExecutionReadiness"));
        assert!(page.contains("function checkExecutionAdmission"));
        assert!(page.contains("queue-preview-button"));
        assert!(page.contains("fetch(`${apiBase}${path}`"));
        assert!(page.contains("POST"));
        assert!(page.contains("Focus queue"));
        assert!(page.contains("Source pulse"));
        assert!(page.contains("Evidence anchors"));
        assert!(page.contains("challenge checks"));
    }
}
