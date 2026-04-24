use axum::{
    Router,
    response::{Html, IntoResponse},
    routing::get,
};
use maud::{DOCTYPE, Markup, PreEscaped, html};
use retrocause_pro_domain::{
    ChallengeStatus, EvidenceFreshness, EvidenceStance, GraphEdge, GraphNode, NodeKind, ProRun,
    RunStatus, SourceStatus, StepState, sample_run,
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
                                    (render_node(node))
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

                        aside class="evidence-dock" aria-label="Evidence anchors" {
                            p class="eyebrow" { "Evidence anchors" }
                            div id="evidence-list" {
                                @for evidence in run.evidence.iter().take(3) {
                                    article class="evidence-chip" {
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
                                    span { (challenge_status_label(challenge.status)) ": " (challenge.title.as_str()) }
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

fn render_node(node: &GraphNode) -> Markup {
    html! {
        article
            class=(format!("graph-node {}", node_kind_label(node.kind)))
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

fn api_base() -> String {
    std::env::var("PRO_API_BASE").unwrap_or_else(|_| "http://127.0.0.1:8787".to_string())
}

fn client_script() -> &'static str {
    r#"
(() => {
  const apiBase = document.body.dataset.apiBase || "http://127.0.0.1:8787";
  const seed = JSON.parse(document.getElementById("seed-run-json").textContent || "{}");
  const byId = (id) => document.getElementById(id);

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
      <article class="graph-node ${escapeHtml(readable(node.kind).replaceAll(" ", "-"))}" style="left:${Number(node.x) || 0}px; top:${Number(node.y) || 0}px;">
        <div class="node-head">
          <p class="node-kind">${escapeHtml(readable(node.kind))}</p>
          <span>${percent(node.confidence)}</span>
        </div>
        <h3>${escapeHtml(node.title)}</h3>
        <p>${escapeHtml(node.summary)}</p>
        <small>${(node.evidence_ids || []).length} evidence / ${(node.challenge_ids || []).length} checks</small>
      </article>
    `).join("");
  }

  function renderRun(run) {
    renderGraph(run);
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
        <article class="evidence-chip">
          <div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.excerpt)}</p></div>
          <span>${escapeHtml(readable(item.stance))} / ${escapeHtml(readable(item.freshness))}</span>
        </article>
      `).join("");
    }

    const challenges = byId("challenge-strip");
    if (challenges) {
      challenges.innerHTML = (run.challenge_checks || []).map((challenge) => `
        <span>${escapeHtml(readable(challenge.status))}: ${escapeHtml(challenge.title)}</span>
      `).join("");
    }

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

  byId("run-create-form")?.addEventListener("submit", (event) => {
    createRun(event).catch((error) => setStatus(`API error: ${error.message}`));
  });
  byId("load-run-button")?.addEventListener("click", () => {
    loadRun(byId("run-picker")?.value).catch((error) => setStatus(`API error: ${error.message}`));
  });
  byId("run-picker")?.addEventListener("change", (event) => {
    loadRun(event.target.value).catch((error) => setStatus(`API error: ${error.message}`));
  });

  renderRun(seed);
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
.focus-docket,
.source-pulse,
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
  max-width: min(620px, calc(100% - 1.8rem));
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
  inset: 8.6rem 1rem 5.7rem;
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
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.28);
}

.graph-node.driver { background: color-mix(in oklch, var(--driver) 88%, white); }
.graph-node.enabler { background: color-mix(in oklch, var(--enabler) 88%, white); }
.graph-node.risk { background: color-mix(in oklch, var(--risk) 86%, white); }
.graph-node.outcome { background: color-mix(in oklch, var(--outcome) 88%, white); }

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

#source-list {
  display: grid;
  gap: 0.65rem;
}

.evidence-dock {
  right: 1rem;
  top: 19.2rem;
  width: min(360px, calc(100% - 2rem));
  max-height: calc(100vh - 26rem);
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

.evidence-chip {
  display: grid;
  gap: 0.42rem;
  padding: 0.72rem;
  border-radius: 8px;
  background: color-mix(in oklch, var(--panel-hard) 72%, black);
}

.evidence-chip p,
.evidence-chip span,
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

.focus-docket li {
  display: grid;
  gap: 0.18rem;
}

.source-meter p {
  font-size: 0.82rem;
  margin-top: 0.22rem;
}

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
  .focus-docket,
  .source-pulse,
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
        assert!(page.contains("run-create-form"));
        assert!(page.contains("fetch(`${apiBase}${path}`"));
        assert!(page.contains("POST"));
        assert!(page.contains("Focus queue"));
        assert!(page.contains("Source pulse"));
        assert!(page.contains("Evidence anchors"));
        assert!(page.contains("challenge checks"));
    }
}
