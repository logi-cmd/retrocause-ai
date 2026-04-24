use serde::Serialize;
use std::collections::HashSet;

#[derive(Clone, Debug, Serialize)]
pub struct ProRun {
    pub id: &'static str,
    pub workspace_id: &'static str,
    pub title: &'static str,
    pub question: &'static str,
    pub status: RunStatus,
    pub updated_at: &'static str,
    pub confidence: f32,
    pub operator_summary: OperatorSummary,
    pub graph: KnowledgeGraph,
    pub evidence: Vec<EvidenceAnchor>,
    pub challenge_checks: Vec<ChallengeCheck>,
    pub sources: Vec<SourceStatusCard>,
    pub usage_ledger: Vec<UsageLedgerEntry>,
    pub next_steps: Vec<VerificationStep>,
}

#[derive(Clone, Debug, Serialize)]
pub struct RunSummary {
    pub id: &'static str,
    pub workspace_id: &'static str,
    pub title: &'static str,
    pub question: &'static str,
    pub status: RunStatus,
    pub confidence: f32,
    pub updated_at: &'static str,
    pub node_count: usize,
    pub edge_count: usize,
}

#[derive(Clone, Debug, Serialize)]
pub struct KnowledgeGraph {
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
}

#[derive(Clone, Debug, Serialize)]
pub struct GraphNode {
    pub id: &'static str,
    pub title: &'static str,
    pub summary: &'static str,
    pub kind: NodeKind,
    pub confidence: f32,
    pub x: u16,
    pub y: u16,
    pub evidence_ids: Vec<&'static str>,
    pub challenge_ids: Vec<&'static str>,
}

#[derive(Clone, Debug, Serialize)]
pub struct GraphEdge {
    pub id: &'static str,
    pub source: &'static str,
    pub target: &'static str,
    pub label: &'static str,
    pub strength: f32,
    pub evidence_ids: Vec<&'static str>,
    pub challenge_ids: Vec<&'static str>,
}

#[derive(Clone, Debug, Serialize)]
pub struct EvidenceAnchor {
    pub id: &'static str,
    pub title: &'static str,
    pub source: &'static str,
    pub stance: EvidenceStance,
    pub freshness: EvidenceFreshness,
    pub excerpt: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct ChallengeCheck {
    pub id: &'static str,
    pub title: &'static str,
    pub status: ChallengeStatus,
    pub note: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct SourceStatusCard {
    pub source: &'static str,
    pub status: SourceStatus,
    pub note: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct UsageLedgerEntry {
    pub category: LedgerCategory,
    pub name: &'static str,
    pub quota_owner: QuotaOwner,
    pub status: LedgerStatus,
}

#[derive(Clone, Debug, Serialize)]
pub struct VerificationStep {
    pub id: &'static str,
    pub title: &'static str,
    pub state: StepState,
}

#[derive(Clone, Debug, Serialize)]
pub struct OperatorSummary {
    pub headline: &'static str,
    pub current_read: &'static str,
    pub caveat: &'static str,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunStatus {
    Queued,
    Running,
    CoolingDown,
    PartialLive,
    NeedsFollowup,
    ReadyForReview,
    Blocked,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    Driver,
    Enabler,
    Risk,
    Outcome,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceStance {
    Supports,
    Refutes,
    Context,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceFreshness {
    Fresh,
    Cached,
    UserProvided,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ChallengeStatus {
    Checked,
    NeedsPrimarySource,
    MissingCounterevidence,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SourceStatus {
    Verified,
    Cached,
    RateLimited,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LedgerCategory {
    Model,
    Search,
    Evidence,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum QuotaOwner {
    ManagedPro,
    Workspace,
    UserProvided,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LedgerStatus {
    Available,
    Cached,
    CoolingDown,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StepState {
    Done,
    Watching,
    Waiting,
}

pub fn sample_run() -> ProRun {
    ProRun {
        id: "run_semiconductor_controls_001",
        workspace_id: "workspace_demo",
        title: "Semiconductor controls reaction map",
        question: "Why did the latest semiconductor export-control update hit AI infrastructure names so sharply?",
        status: RunStatus::ReadyForReview,
        updated_at: "2026-04-24T03:18:00Z",
        confidence: 0.78,
        operator_summary: OperatorSummary {
            headline: "Policy shock explains the move, but demand offsets are still visible.",
            current_read: "Tighter export-control language hit short-term demand expectations, while hyperscaler capex and domestic substitution still support the medium-term thesis.",
            caveat: "Primary-source confirmation is still needed for the final scope of controlled SKUs.",
        },
        graph: KnowledgeGraph {
            nodes: vec![
                GraphNode {
                    id: "policy_update",
                    title: "Control scope tightened",
                    summary: "The new language expanded perceived export risk for advanced AI infrastructure sales.",
                    kind: NodeKind::Driver,
                    confidence: 0.82,
                    x: 96,
                    y: 84,
                    evidence_ids: vec!["ev_policy_release"],
                    challenge_ids: vec!["cc_scope"],
                },
                GraphNode {
                    id: "customer_pause",
                    title: "Customer pause",
                    summary: "Buyers temporarily slowed purchasing while they parsed what still ships cleanly.",
                    kind: NodeKind::Risk,
                    confidence: 0.73,
                    x: 364,
                    y: 104,
                    evidence_ids: vec!["ev_channel_check"],
                    challenge_ids: vec!["cc_scope"],
                },
                GraphNode {
                    id: "inventory_buffer",
                    title: "Inventory buffer",
                    summary: "Channel and inventory already in place softened the immediate hit.",
                    kind: NodeKind::Enabler,
                    confidence: 0.64,
                    x: 360,
                    y: 308,
                    evidence_ids: vec!["ev_company_guidance"],
                    challenge_ids: vec!["cc_inventory"],
                },
                GraphNode {
                    id: "hyperscaler_capex",
                    title: "Hyperscaler capex intact",
                    summary: "Cloud platform spending stayed supportive even as policy headlines worsened sentiment.",
                    kind: NodeKind::Enabler,
                    confidence: 0.81,
                    x: 652,
                    y: 130,
                    evidence_ids: vec!["ev_capex_transcript"],
                    challenge_ids: vec!["cc_capex"],
                },
                GraphNode {
                    id: "domestic_substitution",
                    title: "Domestic substitution bid",
                    summary: "Local supply-chain beneficiaries regained support as substitution narratives strengthened.",
                    kind: NodeKind::Driver,
                    confidence: 0.69,
                    x: 660,
                    y: 332,
                    evidence_ids: vec!["ev_local_supply_chain"],
                    challenge_ids: vec!["cc_substitution"],
                },
                GraphNode {
                    id: "price_reaction",
                    title: "Sharp equity reaction",
                    summary: "The market priced a near-term revenue slowdown faster than the longer demand offset.",
                    kind: NodeKind::Outcome,
                    confidence: 0.78,
                    x: 948,
                    y: 218,
                    evidence_ids: vec!["ev_market_move", "ev_policy_release"],
                    challenge_ids: vec!["cc_countermove"],
                },
            ],
            edges: vec![
                GraphEdge {
                    id: "edge-policy-pause",
                    source: "policy_update",
                    target: "customer_pause",
                    label: "raises compliance uncertainty",
                    strength: 0.84,
                    evidence_ids: vec!["ev_policy_release", "ev_channel_check"],
                    challenge_ids: vec!["cc_scope"],
                },
                GraphEdge {
                    id: "edge-pause-price",
                    source: "customer_pause",
                    target: "price_reaction",
                    label: "drives near-term revenue fear",
                    strength: 0.79,
                    evidence_ids: vec!["ev_channel_check", "ev_market_move"],
                    challenge_ids: vec!["cc_countermove"],
                },
                GraphEdge {
                    id: "edge-inventory-price",
                    source: "inventory_buffer",
                    target: "price_reaction",
                    label: "limits the downside",
                    strength: 0.56,
                    evidence_ids: vec!["ev_company_guidance"],
                    challenge_ids: vec!["cc_inventory"],
                },
                GraphEdge {
                    id: "edge-capex-price",
                    source: "hyperscaler_capex",
                    target: "price_reaction",
                    label: "keeps the medium-term thesis alive",
                    strength: 0.71,
                    evidence_ids: vec!["ev_capex_transcript"],
                    challenge_ids: vec!["cc_capex"],
                },
                GraphEdge {
                    id: "edge-substitution-price",
                    source: "domestic_substitution",
                    target: "price_reaction",
                    label: "supports local winners",
                    strength: 0.67,
                    evidence_ids: vec!["ev_local_supply_chain"],
                    challenge_ids: vec!["cc_substitution"],
                },
            ],
        },
        evidence: vec![
            EvidenceAnchor {
                id: "ev_policy_release",
                title: "Official export-control language",
                source: "Official policy release",
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: "The control update widened perceived risk around advanced AI infrastructure shipments.",
            },
            EvidenceAnchor {
                id: "ev_channel_check",
                title: "Customer compliance pause",
                source: "Market search",
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Cached,
                excerpt: "Channel checks pointed to temporary purchasing pauses while buyers interpreted the rule language.",
            },
            EvidenceAnchor {
                id: "ev_company_guidance",
                title: "Inventory and backlog buffer",
                source: "Company guidance",
                stance: EvidenceStance::Context,
                freshness: EvidenceFreshness::Cached,
                excerpt: "The latest transcript still referenced backlog and inventory buffers that reduce immediate downside.",
            },
            EvidenceAnchor {
                id: "ev_capex_transcript",
                title: "Hyperscaler capex support",
                source: "Company guidance",
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: "Cloud platform commentary kept AI infrastructure spending plans intact.",
            },
            EvidenceAnchor {
                id: "ev_local_supply_chain",
                title: "Substitution narrative",
                source: "Market search",
                stance: EvidenceStance::Context,
                freshness: EvidenceFreshness::Fresh,
                excerpt: "Local supply-chain beneficiaries drew renewed attention as substitution narratives strengthened.",
            },
            EvidenceAnchor {
                id: "ev_market_move",
                title: "Price and sentiment reaction",
                source: "Market search",
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: "The sharp equity move appeared before detailed issuer guidance could absorb the policy shock.",
            },
        ],
        challenge_checks: vec![
            ChallengeCheck {
                id: "cc_scope",
                title: "Does the rule actually cover the affected SKUs?",
                status: ChallengeStatus::NeedsPrimarySource,
                note: "Needs final primary-source mapping between controlled language and issuer product lines.",
            },
            ChallengeCheck {
                id: "cc_inventory",
                title: "Could inventory explain more of the move?",
                status: ChallengeStatus::Checked,
                note: "Inventory evidence explains downside limits, not the initial shock.",
            },
            ChallengeCheck {
                id: "cc_capex",
                title: "Did capex guidance weaken at the same time?",
                status: ChallengeStatus::Checked,
                note: "Current capex evidence stays supportive.",
            },
            ChallengeCheck {
                id: "cc_substitution",
                title: "Is substitution enough to offset lost export demand?",
                status: ChallengeStatus::MissingCounterevidence,
                note: "No direct counterevidence attached yet; keep this as a watch item.",
            },
            ChallengeCheck {
                id: "cc_countermove",
                title: "Was the equity move market-wide instead of policy-specific?",
                status: ChallengeStatus::Checked,
                note: "The timing and sector concentration favor a policy-specific read.",
            },
        ],
        sources: vec![
            SourceStatusCard {
                source: "Official policy release",
                status: SourceStatus::Verified,
                note: "Primary language captured and dated.",
            },
            SourceStatusCard {
                source: "Company guidance",
                status: SourceStatus::Cached,
                note: "Latest transcript is reused from the last verified run.",
            },
            SourceStatusCard {
                source: "Market search",
                status: SourceStatus::RateLimited,
                note: "Fallback source pack filled the gap; live refresh is queued.",
            },
        ],
        usage_ledger: vec![
            UsageLedgerEntry {
                category: LedgerCategory::Model,
                name: "graph_synthesis",
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::Available,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Search,
                name: "market_search",
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::CoolingDown,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Evidence,
                name: "company_guidance_cache",
                quota_owner: QuotaOwner::Workspace,
                status: LedgerStatus::Cached,
            },
        ],
        next_steps: vec![
            VerificationStep {
                id: "step_scope",
                title: "Check whether the next official filing narrows the control scope.",
                state: StepState::Waiting,
            },
            VerificationStep {
                id: "step_capex",
                title: "Re-run after the next hyperscaler capex transcript lands.",
                state: StepState::Watching,
            },
            VerificationStep {
                id: "step_substitution",
                title: "Verify whether domestic substitution announcements changed the demand floor.",
                state: StepState::Watching,
            },
        ],
    }
}

pub fn sample_run_summaries() -> Vec<RunSummary> {
    let run = sample_run();
    vec![run.summary()]
}

pub fn sample_run_by_id(run_id: &str) -> Option<ProRun> {
    let run = sample_run();
    (run.id == run_id).then_some(run)
}

impl ProRun {
    pub fn summary(&self) -> RunSummary {
        RunSummary {
            id: self.id,
            workspace_id: self.workspace_id,
            title: self.title,
            question: self.question,
            status: self.status,
            confidence: self.confidence,
            updated_at: self.updated_at,
            node_count: self.graph.nodes.len(),
            edge_count: self.graph.edges.len(),
        }
    }
}

pub fn validate_run_references(run: &ProRun) -> Result<(), String> {
    let node_ids = run
        .graph
        .nodes
        .iter()
        .map(|node| node.id)
        .collect::<HashSet<_>>();
    let evidence_ids = run
        .evidence
        .iter()
        .map(|evidence| evidence.id)
        .collect::<HashSet<_>>();
    let challenge_ids = run
        .challenge_checks
        .iter()
        .map(|challenge| challenge.id)
        .collect::<HashSet<_>>();

    for edge in &run.graph.edges {
        if !node_ids.contains(edge.source) || !node_ids.contains(edge.target) {
            return Err(format!("edge {} references an unknown node", edge.id));
        }
        assert_known_references(edge.id, &edge.evidence_ids, &evidence_ids, "evidence")?;
        assert_known_references(edge.id, &edge.challenge_ids, &challenge_ids, "challenge")?;
    }

    for node in &run.graph.nodes {
        assert_known_references(node.id, &node.evidence_ids, &evidence_ids, "evidence")?;
        assert_known_references(node.id, &node.challenge_ids, &challenge_ids, "challenge")?;
    }

    Ok(())
}

fn assert_known_references(
    owner_id: &str,
    refs: &[&'static str],
    known_ids: &HashSet<&'static str>,
    label: &str,
) -> Result<(), String> {
    for referenced_id in refs {
        if !known_ids.contains(referenced_id) {
            return Err(format!(
                "{owner_id} references unknown {label} id {referenced_id}"
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{sample_run, sample_run_by_id, sample_run_summaries, validate_run_references};
    use std::collections::HashSet;

    #[test]
    fn sample_run_has_unique_nodes_and_bounded_scores() {
        let run = sample_run();
        let mut ids = HashSet::new();

        assert!((0.0..=1.0).contains(&run.confidence));
        assert!(!run.graph.nodes.is_empty());
        assert!(!run.graph.edges.is_empty());

        for node in &run.graph.nodes {
            assert!(ids.insert(node.id));
            assert!((0.0..=1.0).contains(&node.confidence));
        }

        for edge in &run.graph.edges {
            assert!((0.0..=1.0).contains(&edge.strength));
        }
    }

    #[test]
    fn sample_run_references_existing_evidence_and_challenges() {
        let run = sample_run();
        validate_run_references(&run).expect("sample run references should be internally valid");
    }

    #[test]
    fn run_summary_matches_graph_counts() {
        let run = sample_run();
        let summary = run.summary();

        assert_eq!(summary.id, run.id);
        assert_eq!(summary.node_count, run.graph.nodes.len());
        assert_eq!(summary.edge_count, run.graph.edges.len());
    }

    #[test]
    fn sample_run_lookup_returns_known_run_only() {
        assert!(sample_run_by_id("run_semiconductor_controls_001").is_some());
        assert!(sample_run_by_id("missing").is_none());
    }

    #[test]
    fn sample_run_summaries_are_listable() {
        let summaries = sample_run_summaries();

        assert_eq!(summaries.len(), 1);
        assert_eq!(summaries[0].id, "run_semiconductor_controls_001");
    }
}
