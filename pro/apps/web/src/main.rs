use axum::{
    Router,
    response::{Html, IntoResponse},
    routing::get,
};
use maud::{DOCTYPE, Markup, PreEscaped, html};
use retrocause_pro_domain::{GraphNode, NodeKind, RunSeed, sample_run};

const CANVAS_WIDTH: u16 = 1220;
const CANVAS_HEIGHT: u16 = 520;

fn router() -> Router {
    Router::new().route("/", get(index))
}

async fn index() -> impl IntoResponse {
    Html(render_page(&sample_run()).into_string())
}

fn render_page(run: &RunSeed) -> Markup {
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
                    href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap"
                    rel="stylesheet";
                style { (PreEscaped(styles())) }
            }
            body {
                main class="shell" {
                    header class="topbar" {
                        div class="brand" {
                            div class="brand-mark" { "RC" }
                            div {
                                p class="eyebrow" { "RetroCause Pro kickoff" }
                                h1 { "Knowledge graph review desk" }
                            }
                        }
                        div class="topbar-meta" {
                            span class="pill pill--state" { (run.run_state) }
                            span class="pill" { "confidence " (percent(run.confidence)) }
                            span class="pill" { (run.nodes.len()) " nodes / " (run.edges.len()) " edges" }
                        }
                    }

                    section class="workspace" {
                        aside class="rail rail--left" {
                            p class="rail-label" { "Operator summary" }
                            h2 { (run.title) }
                            p class="question" { (run.question) }
                            p class="verdict" { (run.verdict) }
                            div class="section-block" {
                                p class="section-label" { "Next review moves" }
                                ol {
                                    @for step in run.next_steps {
                                        li { (step) }
                                    }
                                }
                            }
                        }

                        section class="graph-stage" {
                            div class="stage-header" {
                                div {
                                    p class="rail-label" { "Primary surface" }
                                    h2 { "Graph-first run review" }
                                }
                                p class="stage-note" { "Pro starts from the graph, then expands into evidence and export." }
                            }
                            div class="graph-board" {
                                svg
                                    class="graph-wires"
                                    viewBox={(format!("0 0 {} {}", CANVAS_WIDTH, CANVAS_HEIGHT))}
                                    aria-hidden="true"
                                {
                                    @for edge in &run.edges {
                                        (render_edge(run, edge.source, edge.target, edge.label))
                                    }
                                }
                                @for node in &run.nodes {
                                    (render_node(node))
                                }
                            }
                        }

                        aside class="rail rail--right" {
                            p class="rail-label" { "Evidence and source health" }
                            div class="section-block" {
                                p class="section-label" { "Source ledger" }
                                ul class="source-list" {
                                    @for source in &run.source_status {
                                        li class="source-item" {
                                            div {
                                                strong { (source.source) }
                                                p { (source.note) }
                                            }
                                            span class=(format!("status {}", source.status)) { (source.status) }
                                        }
                                    }
                                }
                            }
                            div class="section-block" {
                                p class="section-label" { "Future data contract" }
                                p class="stage-note" { "The web shell already embeds the canonical run JSON for future hydration, diffing, and export." }
                                pre class="json-seed" { (seed_json) }
                            }
                        }
                    }
                }
            }
        }
    }
}

fn render_edge(run: &RunSeed, source_id: &str, target_id: &str, label: &str) -> Markup {
    let source = run
        .nodes
        .iter()
        .find(|node| node.id == source_id)
        .expect("known source node");
    let target = run
        .nodes
        .iter()
        .find(|node| node.id == target_id)
        .expect("known target node");

    let path = wire_path(source, target);
    let label_x = (source.x + target.x) / 2;
    let label_y = (source.y + target.y) / 2;

    html! {
        path class="wire" d=(path) {}
        text class="wire-label" x=(label_x) y=(label_y) { (label) }
    }
}

fn render_node(node: &GraphNode) -> Markup {
    html! {
        article
            class=(format!("graph-node {:?}", node.kind).to_lowercase().replace(' ', "-"))
            style=(format!("left:{}px; top:{}px;", node.x, node.y))
        {
            p class="node-kind" { (node_kind_label(node.kind)) }
            h3 { (node.title) }
            p class="node-summary" { (node.summary) }
            div class="node-meta" {
                span { "confidence " (percent(node.confidence)) }
            }
        }
    }
}

fn wire_path(source: &GraphNode, target: &GraphNode) -> String {
    let start_x = i32::from(source.x) + 150;
    let start_y = i32::from(source.y) + 70;
    let end_x = i32::from(target.x);
    let end_y = i32::from(target.y) + 70;
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

fn styles() -> &'static str {
    r#"
:root {
  color-scheme: dark;
  --bg: oklch(0.18 0.02 95);
  --panel: oklch(0.23 0.02 95);
  --panel-strong: oklch(0.28 0.02 95);
  --surface: oklch(0.92 0.02 95);
  --text: oklch(0.95 0.01 92);
  --muted: oklch(0.72 0.02 92);
  --line: oklch(0.46 0.05 45);
  --driver: oklch(0.78 0.09 78);
  --enabler: oklch(0.8 0.06 165);
  --risk: oklch(0.78 0.08 30);
  --outcome: oklch(0.78 0.08 250);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Familjen Grotesk", sans-serif;
  background:
    radial-gradient(circle at top, color-mix(in oklch, var(--panel-strong) 70%, transparent), transparent 38%),
    var(--bg);
  color: var(--text);
}

.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.topbar,
.rail,
.graph-stage {
  background: color-mix(in oklch, var(--panel) 92%, black);
  border: 1px solid color-mix(in oklch, var(--panel-strong) 72%, black);
  border-radius: 8px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.2rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.brand-mark {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: oklch(0.8 0.08 80);
  color: oklch(0.25 0.02 85);
  font-family: "Sora", sans-serif;
  font-weight: 700;
}

.eyebrow,
.rail-label,
.section-label,
.node-kind {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.72rem;
  color: var(--muted);
}

h1,
h2,
h3 {
  margin: 0;
  font-family: "Sora", sans-serif;
  font-weight: 600;
}

h1 { font-size: 1.35rem; }
h2 { font-size: 1.1rem; }
h3 { font-size: 1rem; }

.topbar-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.pill {
  border-radius: 999px;
  padding: 0.35rem 0.7rem;
  border: 1px solid color-mix(in oklch, var(--surface) 12%, transparent);
  background: color-mix(in oklch, var(--panel-strong) 70%, black);
  color: var(--surface);
  font-size: 0.82rem;
}

.pill--state {
  background: color-mix(in oklch, var(--enabler) 18%, var(--panel-strong));
}

.workspace {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 330px;
  gap: 1rem;
  min-height: calc(100vh - 7rem);
}

.rail,
.graph-stage {
  padding: 1rem;
}

.rail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.question,
.verdict,
.stage-note,
.node-summary,
.source-item p,
.json-seed {
  margin: 0;
  line-height: 1.55;
  color: color-mix(in oklch, var(--text) 88%, var(--muted));
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.9rem;
  border-top: 1px solid color-mix(in oklch, var(--surface) 10%, transparent);
}

ol {
  margin: 0;
  padding-left: 1.2rem;
  display: grid;
  gap: 0.75rem;
}

.graph-stage {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
}

.graph-board {
  position: relative;
  min-height: 560px;
  border-radius: 8px;
  overflow: hidden;
  background:
    linear-gradient(color-mix(in oklch, var(--surface) 6%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in oklch, var(--surface) 6%, transparent) 1px, transparent 1px),
    color-mix(in oklch, var(--panel-strong) 88%, black);
  background-size: 32px 32px, 32px 32px, auto;
}

.graph-wires {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.wire {
  fill: none;
  stroke: color-mix(in oklch, var(--line) 70%, var(--surface));
  stroke-width: 2.5;
  stroke-linecap: round;
}

.wire-label {
  fill: color-mix(in oklch, var(--surface) 80%, var(--muted));
  font-size: 11px;
  font-family: "Familjen Grotesk", sans-serif;
}

.graph-node {
  position: absolute;
  width: 220px;
  padding: 0.9rem;
  border-radius: 8px;
  border: 1px solid color-mix(in oklch, var(--surface) 10%, transparent);
  color: oklch(0.22 0.02 85);
  box-shadow: 0 18px 32px color-mix(in oklch, black 35%, transparent);
}

.graph-node.driver { background: color-mix(in oklch, var(--driver) 88%, white); }
.graph-node.enabler { background: color-mix(in oklch, var(--enabler) 88%, white); }
.graph-node.risk { background: color-mix(in oklch, var(--risk) 88%, white); }
.graph-node.outcome { background: color-mix(in oklch, var(--outcome) 88%, white); }

.node-meta {
  margin-top: 0.8rem;
  font-size: 0.82rem;
  color: color-mix(in oklch, black 45%, transparent);
}

.source-list {
  list-style: none;
  display: grid;
  gap: 0.75rem;
  padding: 0;
  margin: 0;
}

.source-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: start;
}

.status {
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.76rem;
  border: 1px solid color-mix(in oklch, var(--surface) 12%, transparent);
}

.status.verified { background: color-mix(in oklch, var(--enabler) 25%, var(--panel-strong)); }
.status.cached { background: color-mix(in oklch, var(--outcome) 24%, var(--panel-strong)); }
.status.rate_limited { background: color-mix(in oklch, var(--risk) 28%, var(--panel-strong)); }

.json-seed {
  max-height: 260px;
  overflow: auto;
  padding: 0.9rem;
  background: color-mix(in oklch, black 18%, var(--panel-strong));
  border-radius: 8px;
  font-size: 0.8rem;
}

@media (max-width: 1200px) {
  .workspace { grid-template-columns: 1fr; }
  .graph-board { min-height: 720px; }
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
        let path = wire_path(&run.nodes[0], &run.nodes[1]);
        assert!(path.starts_with('M'));
        assert!(path.contains('C'));
    }

    #[test]
    fn rendered_page_contains_primary_sections() {
        let page = render_page(&sample_run()).into_string();
        assert!(page.contains("Knowledge graph review desk"));
        assert!(page.contains("Graph-first run review"));
        assert!(page.contains("Source ledger"));
    }
}
