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
                link rel="preconnect" href="https://fonts.googleapis.com";
                link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="";
                link
                    href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap"
                    rel="stylesheet";
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
                        }

                        aside class="execution-console" aria-label="Execution queue" {
                            p class="eyebrow" { "Execution queue" }
                            strong id="execution-queue-mode" { "preview-only" }
                            button id="queue-preview-button" type="button" { "Queue preview job" }
                            p id="execution-queue-status" class="console-status" {
                                "Queue uses the current run question; execution stays disabled."
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
                            div id="execution-lifecycle-panel" class="lifecycle-panel" {
                                article class="queue-meter queue-meter--empty" {
                                    div {
                                        strong { "Worker lifecycle planned" }
                                        p { "Lifecycle states load from the Pro API; execution remains disabled." }
                                    }
                                    span class="quota-state quota-state--deferred" { "planned" }
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

  function renderProviderStatus(snapshot) {
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
    if (!order) {
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

  async function inspectWorkOrder(jobId) {
    if (!jobId) return;
    setText("execution-queue-status", `Inspecting ${jobId} work order...`);
    const order = await fetchJson(`/api/execution-jobs/${encodeURIComponent(jobId)}/work-order`);
    renderWorkOrder(order);
    setText("execution-queue-status", `Loaded ${jobId} route steps; execution remains disabled.`);
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
    const [run, graphPayload] = await Promise.all([
      fetchJson(`/api/runs/${encodeURIComponent(runId)}`),
      fetchJson(`/api/runs/${encodeURIComponent(runId)}/graph`),
    ]);
    run.graph = graphPayload.graph;
    renderRun(run);
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
  renderProviderStatus(providerSeed);
  renderProviderAdapterContract(null);
  renderExecutionJobs([]);
  renderWorkOrder(null);
  renderExecutionLifecycle(null);
  renderStoragePlan(null);
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
  fetchJson("/api/execution-lifecycle")
    .then(renderExecutionLifecycle)
    .catch(() => {
      renderExecutionLifecycle(null);
    });
  fetchJson("/api/storage-plan")
    .then(renderStoragePlan)
    .catch(() => {
      renderStoragePlan(null);
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
  font-family: "Hanken Grotesk", sans-serif;
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
  font-family: "Sora", sans-serif;
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
  font-family: "Sora", sans-serif;
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
  width: min(380px, calc(100% - 2rem));
  max-height: 13rem;
  overflow: auto;
  padding: 0.9rem;
  display: grid;
  gap: 0.65rem;
}

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

#execution-job-list {
  display: grid;
  gap: 0.65rem;
}

#execution-work-order-detail,
#execution-lifecycle-panel,
#storage-boundary-panel {
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

.lifecycle-card {
  background: color-mix(in oklch, var(--panel-hard) 68%, var(--accent));
}

.storage-card {
  background: color-mix(in oklch, var(--panel-hard) 72%, oklch(0.47 0.08 250));
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
        assert!(page.contains("provider-status-list"));
        assert!(page.contains("provider-adapter-panel"));
        assert!(page.contains("/api/provider-status"));
        assert!(page.contains("/api/provider-adapter-contract"));
        assert!(page.contains("execution-job-list"));
        assert!(page.contains("execution-work-order-detail"));
        assert!(page.contains("execution-lifecycle-panel"));
        assert!(page.contains("storage-boundary-panel"));
        assert!(page.contains("/api/execution-jobs"));
        assert!(page.contains("/work-order"));
        assert!(page.contains("/api/execution-lifecycle"));
        assert!(page.contains("/api/storage-plan"));
        assert!(page.contains("data-work-order-job-id"));
        assert!(page.contains("function renderWorkOrder"));
        assert!(page.contains("function renderExecutionLifecycle"));
        assert!(page.contains("function renderStoragePlan"));
        assert!(page.contains("function renderProviderAdapterContract"));
        assert!(page.contains("queue-preview-button"));
        assert!(page.contains("fetch(`${apiBase}${path}`"));
        assert!(page.contains("POST"));
        assert!(page.contains("Focus queue"));
        assert!(page.contains("Source pulse"));
        assert!(page.contains("Evidence anchors"));
        assert!(page.contains("challenge checks"));
    }
}
