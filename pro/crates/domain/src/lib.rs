use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: &'static str,
    pub title: &'static str,
    pub summary: &'static str,
    pub kind: NodeKind,
    pub confidence: f32,
    pub x: u16,
    pub y: u16,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GraphEdge {
    pub id: &'static str,
    pub source: &'static str,
    pub target: &'static str,
    pub label: &'static str,
    pub strength: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceStatusCard {
    pub source: &'static str,
    pub status: &'static str,
    pub note: &'static str,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunSeed {
    pub title: &'static str,
    pub question: &'static str,
    pub verdict: &'static str,
    pub confidence: f32,
    pub run_state: &'static str,
    pub next_steps: [&'static str; 3],
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
    pub source_status: Vec<SourceStatusCard>,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    Driver,
    Enabler,
    Risk,
    Outcome,
}

pub fn sample_run() -> RunSeed {
    RunSeed {
        title: "Semiconductor controls reaction map",
        question: "Why did the latest semiconductor export-control update hit AI infrastructure names so sharply?",
        verdict: "The current explanation is that tighter export-control language hit short-term demand expectations, while hyperscaler capex and domestic substitution still support the medium-term thesis.",
        confidence: 0.78,
        run_state: "ready_for_review",
        next_steps: [
            "Check whether the next official filing narrows the control scope.",
            "Re-run after the next hyperscaler capex transcript lands.",
            "Verify whether Chinese domestic substitution announcements changed the demand floor.",
        ],
        nodes: vec![
            GraphNode {
                id: "policy_update",
                title: "Control scope tightened",
                summary: "The new language expanded perceived export risk for advanced AI infrastructure sales.",
                kind: NodeKind::Driver,
                confidence: 0.82,
                x: 96,
                y: 84,
            },
            GraphNode {
                id: "customer_pause",
                title: "Customer pause",
                summary: "Buyers temporarily slowed purchasing while they parsed what still ships cleanly.",
                kind: NodeKind::Risk,
                confidence: 0.73,
                x: 364,
                y: 104,
            },
            GraphNode {
                id: "inventory_buffer",
                title: "Inventory buffer",
                summary: "Channel and inventory already in place softened the immediate hit.",
                kind: NodeKind::Enabler,
                confidence: 0.64,
                x: 360,
                y: 308,
            },
            GraphNode {
                id: "hyperscaler_capex",
                title: "Hyperscaler capex intact",
                summary: "Cloud platform spending stayed supportive even as policy headlines worsened sentiment.",
                kind: NodeKind::Enabler,
                confidence: 0.81,
                x: 652,
                y: 130,
            },
            GraphNode {
                id: "domestic_substitution",
                title: "Domestic substitution bid",
                summary: "Local supply-chain beneficiaries regained support as substitution narratives strengthened.",
                kind: NodeKind::Driver,
                confidence: 0.69,
                x: 660,
                y: 332,
            },
            GraphNode {
                id: "price_reaction",
                title: "Sharp equity reaction",
                summary: "The market priced a near-term revenue slowdown faster than the longer demand offset.",
                kind: NodeKind::Outcome,
                confidence: 0.78,
                x: 948,
                y: 218,
            },
        ],
        edges: vec![
            GraphEdge {
                id: "edge-policy-pause",
                source: "policy_update",
                target: "customer_pause",
                label: "raises compliance uncertainty",
                strength: 0.84,
            },
            GraphEdge {
                id: "edge-pause-price",
                source: "customer_pause",
                target: "price_reaction",
                label: "drives near-term revenue fear",
                strength: 0.79,
            },
            GraphEdge {
                id: "edge-inventory-price",
                source: "inventory_buffer",
                target: "price_reaction",
                label: "limits the downside",
                strength: 0.56,
            },
            GraphEdge {
                id: "edge-capex-price",
                source: "hyperscaler_capex",
                target: "price_reaction",
                label: "keeps the medium-term thesis alive",
                strength: 0.71,
            },
            GraphEdge {
                id: "edge-substitution-price",
                source: "domestic_substitution",
                target: "price_reaction",
                label: "supports local winners",
                strength: 0.67,
            },
        ],
        source_status: vec![
            SourceStatusCard {
                source: "Official policy release",
                status: "verified",
                note: "Primary language captured and dated.",
            },
            SourceStatusCard {
                source: "Company guidance",
                status: "cached",
                note: "Latest transcript is reused from the last verified run.",
            },
            SourceStatusCard {
                source: "Market search",
                status: "rate_limited",
                note: "Fallback source pack filled the gap; live refresh is queued.",
            },
        ],
    }
}

#[cfg(test)]
mod tests {
    use super::sample_run;
    use std::collections::HashSet;

    #[test]
    fn sample_run_has_unique_nodes_and_bounded_scores() {
        let run = sample_run();
        let mut ids = HashSet::new();

        assert!((0.0..=1.0).contains(&run.confidence));
        assert!(!run.nodes.is_empty());
        assert!(!run.edges.is_empty());

        for node in &run.nodes {
            assert!(ids.insert(node.id));
            assert!((0.0..=1.0).contains(&node.confidence));
        }

        for edge in &run.edges {
            assert!((0.0..=1.0).contains(&edge.strength));
        }
    }
}
