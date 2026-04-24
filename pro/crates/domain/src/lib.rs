use serde::{Deserialize, Serialize};
use std::collections::HashSet;

#[derive(Clone, Debug, Serialize)]
pub struct ProRun {
    pub id: String,
    pub workspace_id: String,
    pub title: String,
    pub question: String,
    pub status: RunStatus,
    pub updated_at: String,
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
    pub id: String,
    pub workspace_id: String,
    pub title: String,
    pub question: String,
    pub status: RunStatus,
    pub confidence: f32,
    pub updated_at: String,
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
    pub id: String,
    pub title: String,
    pub summary: String,
    pub kind: NodeKind,
    pub confidence: f32,
    pub x: u16,
    pub y: u16,
    pub evidence_ids: Vec<String>,
    pub challenge_ids: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct GraphEdge {
    pub id: String,
    pub source: String,
    pub target: String,
    pub label: String,
    pub strength: f32,
    pub evidence_ids: Vec<String>,
    pub challenge_ids: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct EvidenceAnchor {
    pub id: String,
    pub title: String,
    pub source: String,
    pub stance: EvidenceStance,
    pub freshness: EvidenceFreshness,
    pub excerpt: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ChallengeCheck {
    pub id: String,
    pub title: String,
    pub status: ChallengeStatus,
    pub note: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct SourceStatusCard {
    pub source: String,
    pub status: SourceStatus,
    pub note: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct UsageLedgerEntry {
    pub category: LedgerCategory,
    pub name: String,
    pub quota_owner: QuotaOwner,
    pub status: LedgerStatus,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderStatusSnapshot {
    pub workspace_id: String,
    pub mode: ProviderStatusMode,
    pub generated_at: String,
    pub entries: Vec<ProviderQuotaStatus>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProviderQuotaStatus {
    pub id: String,
    pub label: String,
    pub category: LedgerCategory,
    pub quota_owner: QuotaOwner,
    pub readiness: ProviderReadiness,
    pub credential_policy: CredentialPolicy,
    pub cooldown: CooldownState,
    pub note: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct CooldownState {
    pub state: CooldownKind,
    pub retry_after_seconds: Option<u32>,
    pub reason: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct VerificationStep {
    pub id: String,
    pub title: String,
    pub state: StepState,
}

#[derive(Clone, Debug, Serialize)]
pub struct OperatorSummary {
    pub headline: String,
    pub current_read: String,
    pub caveat: String,
}

#[derive(Clone, Debug, Deserialize)]
pub struct CreateRunRequest {
    pub workspace_id: Option<String>,
    pub title: Option<String>,
    pub question: String,
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

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderStatusMode {
    LocalAlphaNoCredentials,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderReadiness {
    Ready,
    NotConfigured,
    CoolingDown,
    Deferred,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CredentialPolicy {
    ManagedProLater,
    WorkspaceManagedLater,
    ByokLater,
    UserEvidenceOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CooldownKind {
    Clear,
    CoolingDown,
    NotApplicable,
}

pub fn create_run_from_request(sequence: u64, request: CreateRunRequest) -> Result<ProRun, String> {
    let question = request.question.trim();
    if question.is_empty() {
        return Err("question_required".to_string());
    }

    let workspace_id = non_empty_or_default(request.workspace_id, "workspace_default");
    let title = non_empty_or_else(request.title, || generated_title(question));
    let run_id = format!("run_local_{sequence:06}");
    let evidence_id = format!("{run_id}_question");
    let challenge_id = format!("{run_id}_primary_source_check");

    let run = ProRun {
        id: run_id.clone(),
        workspace_id,
        title,
        question: question.to_string(),
        status: RunStatus::Queued,
        updated_at: format!("local-seq-{sequence:06}"),
        confidence: 0.2,
        operator_summary: OperatorSummary {
            headline: "Run accepted; retrieval has not started yet.".to_string(),
            current_read: "The Pro API has captured the question and created an inspectable graph shell for the upcoming retrieval and synthesis pipeline.".to_string(),
            caveat: "This is an in-memory alpha run. It is not durable and it does not call model or search providers yet.".to_string(),
        },
        graph: KnowledgeGraph {
            nodes: vec![
                GraphNode {
                    id: format!("{run_id}_question_node"),
                    title: "Question framed".to_string(),
                    summary: "The submitted question is the starting point for the causal graph.".to_string(),
                    kind: NodeKind::Driver,
                    confidence: 0.35,
                    x: 120,
                    y: 180,
                    evidence_ids: vec![evidence_id.clone()],
                    challenge_ids: vec![challenge_id.clone()],
                },
                GraphNode {
                    id: format!("{run_id}_evidence_node"),
                    title: "Evidence intake pending".to_string(),
                    summary: "Provider routing, source policy, and evidence collection are queued for the next Pro slice.".to_string(),
                    kind: NodeKind::Risk,
                    confidence: 0.25,
                    x: 460,
                    y: 210,
                    evidence_ids: vec![evidence_id.clone()],
                    challenge_ids: vec![challenge_id.clone()],
                },
                GraphNode {
                    id: format!("{run_id}_review_node"),
                    title: "Review graph pending".to_string(),
                    summary: "The run is visible now so operators can inspect status before live synthesis exists.".to_string(),
                    kind: NodeKind::Outcome,
                    confidence: 0.2,
                    x: 800,
                    y: 180,
                    evidence_ids: vec![evidence_id.clone()],
                    challenge_ids: vec![challenge_id.clone()],
                },
            ],
            edges: vec![
                GraphEdge {
                    id: format!("{run_id}_edge_question_to_evidence"),
                    source: format!("{run_id}_question_node"),
                    target: format!("{run_id}_evidence_node"),
                    label: "requires source retrieval".to_string(),
                    strength: 0.3,
                    evidence_ids: vec![evidence_id.clone()],
                    challenge_ids: vec![challenge_id.clone()],
                },
                GraphEdge {
                    id: format!("{run_id}_edge_evidence_to_review"),
                    source: format!("{run_id}_evidence_node"),
                    target: format!("{run_id}_review_node"),
                    label: "feeds graph synthesis".to_string(),
                    strength: 0.25,
                    evidence_ids: vec![evidence_id.clone()],
                    challenge_ids: vec![challenge_id.clone()],
                },
            ],
        },
        evidence: vec![EvidenceAnchor {
            id: evidence_id,
            title: "Submitted question".to_string(),
            source: "User input".to_string(),
            stance: EvidenceStance::Context,
            freshness: EvidenceFreshness::UserProvided,
            excerpt: question.to_string(),
        }],
        challenge_checks: vec![ChallengeCheck {
            id: challenge_id,
            title: "Attach primary evidence before review".to_string(),
            status: ChallengeStatus::NeedsPrimarySource,
            note: "The run is created before provider retrieval exists, so it must not be treated as a causal conclusion yet.".to_string(),
        }],
        sources: vec![SourceStatusCard {
            source: "User input".to_string(),
            status: SourceStatus::Verified,
            note: "Question captured locally in the Pro API process.".to_string(),
        }],
        usage_ledger: vec![
            UsageLedgerEntry {
                category: LedgerCategory::Evidence,
                name: "submitted_question".to_string(),
                quota_owner: QuotaOwner::UserProvided,
                status: LedgerStatus::Available,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Search,
                name: "retrieval_queue".to_string(),
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::CoolingDown,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Model,
                name: "graph_synthesis_queue".to_string(),
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::CoolingDown,
            },
        ],
        next_steps: vec![
            VerificationStep {
                id: format!("{run_id}_step_sources"),
                title: "Route the question through provider and source policy.".to_string(),
                state: StepState::Waiting,
            },
            VerificationStep {
                id: format!("{run_id}_step_evidence"),
                title: "Attach evidence anchors before raising confidence.".to_string(),
                state: StepState::Waiting,
            },
            VerificationStep {
                id: format!("{run_id}_step_review"),
                title: "Recompute the graph after retrieval and challenge checks finish.".to_string(),
                state: StepState::Waiting,
            },
        ],
    };

    validate_run_references(&run)?;
    Ok(run)
}

pub fn sample_run() -> ProRun {
    ProRun {
        id: s("run_semiconductor_controls_001"),
        workspace_id: s("workspace_demo"),
        title: s("Semiconductor controls reaction map"),
        question: s(
            "Why did the latest semiconductor export-control update hit AI infrastructure names so sharply?",
        ),
        status: RunStatus::ReadyForReview,
        updated_at: s("2026-04-24T03:18:00Z"),
        confidence: 0.78,
        operator_summary: OperatorSummary {
            headline: s("Policy shock explains the move, but demand offsets are still visible."),
            current_read: s(
                "Tighter export-control language hit short-term demand expectations, while hyperscaler capex and domestic substitution still support the medium-term thesis.",
            ),
            caveat: s(
                "Primary-source confirmation is still needed for the final scope of controlled SKUs.",
            ),
        },
        graph: KnowledgeGraph {
            nodes: vec![
                GraphNode {
                    id: s("policy_update"),
                    title: s("Control scope tightened"),
                    summary: s(
                        "The new language expanded perceived export risk for advanced AI infrastructure sales.",
                    ),
                    kind: NodeKind::Driver,
                    confidence: 0.82,
                    x: 96,
                    y: 84,
                    evidence_ids: vec![s("ev_policy_release")],
                    challenge_ids: vec![s("cc_scope")],
                },
                GraphNode {
                    id: s("customer_pause"),
                    title: s("Customer pause"),
                    summary: s(
                        "Buyers temporarily slowed purchasing while they parsed what still ships cleanly.",
                    ),
                    kind: NodeKind::Risk,
                    confidence: 0.73,
                    x: 364,
                    y: 104,
                    evidence_ids: vec![s("ev_channel_check")],
                    challenge_ids: vec![s("cc_scope")],
                },
                GraphNode {
                    id: s("inventory_buffer"),
                    title: s("Inventory buffer"),
                    summary: s(
                        "Channel and inventory already in place softened the immediate hit.",
                    ),
                    kind: NodeKind::Enabler,
                    confidence: 0.64,
                    x: 360,
                    y: 308,
                    evidence_ids: vec![s("ev_company_guidance")],
                    challenge_ids: vec![s("cc_inventory")],
                },
                GraphNode {
                    id: s("hyperscaler_capex"),
                    title: s("Hyperscaler capex intact"),
                    summary: s(
                        "Cloud platform spending stayed supportive even as policy headlines worsened sentiment.",
                    ),
                    kind: NodeKind::Enabler,
                    confidence: 0.81,
                    x: 652,
                    y: 130,
                    evidence_ids: vec![s("ev_capex_transcript")],
                    challenge_ids: vec![s("cc_capex")],
                },
                GraphNode {
                    id: s("domestic_substitution"),
                    title: s("Domestic substitution bid"),
                    summary: s(
                        "Local supply-chain beneficiaries regained support as substitution narratives strengthened.",
                    ),
                    kind: NodeKind::Driver,
                    confidence: 0.69,
                    x: 660,
                    y: 332,
                    evidence_ids: vec![s("ev_local_supply_chain")],
                    challenge_ids: vec![s("cc_substitution")],
                },
                GraphNode {
                    id: s("price_reaction"),
                    title: s("Sharp equity reaction"),
                    summary: s(
                        "The market priced a near-term revenue slowdown faster than the longer demand offset.",
                    ),
                    kind: NodeKind::Outcome,
                    confidence: 0.78,
                    x: 948,
                    y: 218,
                    evidence_ids: vec![s("ev_market_move"), s("ev_policy_release")],
                    challenge_ids: vec![s("cc_countermove")],
                },
            ],
            edges: vec![
                GraphEdge {
                    id: s("edge-policy-pause"),
                    source: s("policy_update"),
                    target: s("customer_pause"),
                    label: s("raises compliance uncertainty"),
                    strength: 0.84,
                    evidence_ids: vec![s("ev_policy_release"), s("ev_channel_check")],
                    challenge_ids: vec![s("cc_scope")],
                },
                GraphEdge {
                    id: s("edge-pause-price"),
                    source: s("customer_pause"),
                    target: s("price_reaction"),
                    label: s("drives near-term revenue fear"),
                    strength: 0.79,
                    evidence_ids: vec![s("ev_channel_check"), s("ev_market_move")],
                    challenge_ids: vec![s("cc_countermove")],
                },
                GraphEdge {
                    id: s("edge-inventory-price"),
                    source: s("inventory_buffer"),
                    target: s("price_reaction"),
                    label: s("limits the downside"),
                    strength: 0.56,
                    evidence_ids: vec![s("ev_company_guidance")],
                    challenge_ids: vec![s("cc_inventory")],
                },
                GraphEdge {
                    id: s("edge-capex-price"),
                    source: s("hyperscaler_capex"),
                    target: s("price_reaction"),
                    label: s("keeps the medium-term thesis alive"),
                    strength: 0.71,
                    evidence_ids: vec![s("ev_capex_transcript")],
                    challenge_ids: vec![s("cc_capex")],
                },
                GraphEdge {
                    id: s("edge-substitution-price"),
                    source: s("domestic_substitution"),
                    target: s("price_reaction"),
                    label: s("supports local winners"),
                    strength: 0.67,
                    evidence_ids: vec![s("ev_local_supply_chain")],
                    challenge_ids: vec![s("cc_substitution")],
                },
            ],
        },
        evidence: vec![
            EvidenceAnchor {
                id: s("ev_policy_release"),
                title: s("Official export-control language"),
                source: s("Official policy release"),
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: s(
                    "The control update widened perceived risk around advanced AI infrastructure shipments.",
                ),
            },
            EvidenceAnchor {
                id: s("ev_channel_check"),
                title: s("Customer compliance pause"),
                source: s("Market search"),
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Cached,
                excerpt: s(
                    "Channel checks pointed to temporary purchasing pauses while buyers interpreted the rule language.",
                ),
            },
            EvidenceAnchor {
                id: s("ev_company_guidance"),
                title: s("Inventory and backlog buffer"),
                source: s("Company guidance"),
                stance: EvidenceStance::Context,
                freshness: EvidenceFreshness::Cached,
                excerpt: s(
                    "The latest transcript still referenced backlog and inventory buffers that reduce immediate downside.",
                ),
            },
            EvidenceAnchor {
                id: s("ev_capex_transcript"),
                title: s("Hyperscaler capex support"),
                source: s("Company guidance"),
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: s(
                    "Cloud platform commentary kept AI infrastructure spending plans intact.",
                ),
            },
            EvidenceAnchor {
                id: s("ev_local_supply_chain"),
                title: s("Substitution narrative"),
                source: s("Market search"),
                stance: EvidenceStance::Context,
                freshness: EvidenceFreshness::Fresh,
                excerpt: s(
                    "Local supply-chain beneficiaries drew renewed attention as substitution narratives strengthened.",
                ),
            },
            EvidenceAnchor {
                id: s("ev_market_move"),
                title: s("Price and sentiment reaction"),
                source: s("Market search"),
                stance: EvidenceStance::Supports,
                freshness: EvidenceFreshness::Fresh,
                excerpt: s(
                    "The sharp equity move appeared before detailed issuer guidance could absorb the policy shock.",
                ),
            },
        ],
        challenge_checks: vec![
            ChallengeCheck {
                id: s("cc_scope"),
                title: s("Does the rule actually cover the affected SKUs?"),
                status: ChallengeStatus::NeedsPrimarySource,
                note: s(
                    "Needs final primary-source mapping between controlled language and issuer product lines.",
                ),
            },
            ChallengeCheck {
                id: s("cc_inventory"),
                title: s("Could inventory explain more of the move?"),
                status: ChallengeStatus::Checked,
                note: s("Inventory evidence explains downside limits, not the initial shock."),
            },
            ChallengeCheck {
                id: s("cc_capex"),
                title: s("Did capex guidance weaken at the same time?"),
                status: ChallengeStatus::Checked,
                note: s("Current capex evidence stays supportive."),
            },
            ChallengeCheck {
                id: s("cc_substitution"),
                title: s("Is substitution enough to offset lost export demand?"),
                status: ChallengeStatus::MissingCounterevidence,
                note: s("No direct counterevidence attached yet; keep this as a watch item."),
            },
            ChallengeCheck {
                id: s("cc_countermove"),
                title: s("Was the equity move market-wide instead of policy-specific?"),
                status: ChallengeStatus::Checked,
                note: s("The timing and sector concentration favor a policy-specific read."),
            },
        ],
        sources: vec![
            SourceStatusCard {
                source: s("Official policy release"),
                status: SourceStatus::Verified,
                note: s("Primary language captured and dated."),
            },
            SourceStatusCard {
                source: s("Company guidance"),
                status: SourceStatus::Cached,
                note: s("Latest transcript is reused from the last verified run."),
            },
            SourceStatusCard {
                source: s("Market search"),
                status: SourceStatus::RateLimited,
                note: s("Fallback source pack filled the gap; live refresh is queued."),
            },
        ],
        usage_ledger: vec![
            UsageLedgerEntry {
                category: LedgerCategory::Model,
                name: s("graph_synthesis"),
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::Available,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Search,
                name: s("market_search"),
                quota_owner: QuotaOwner::ManagedPro,
                status: LedgerStatus::CoolingDown,
            },
            UsageLedgerEntry {
                category: LedgerCategory::Evidence,
                name: s("company_guidance_cache"),
                quota_owner: QuotaOwner::Workspace,
                status: LedgerStatus::Cached,
            },
        ],
        next_steps: vec![
            VerificationStep {
                id: s("step_scope"),
                title: s("Check whether the next official filing narrows the control scope."),
                state: StepState::Waiting,
            },
            VerificationStep {
                id: s("step_capex"),
                title: s("Re-run after the next hyperscaler capex transcript lands."),
                state: StepState::Watching,
            },
            VerificationStep {
                id: s("step_substitution"),
                title: s(
                    "Verify whether domestic substitution announcements changed the demand floor.",
                ),
                state: StepState::Watching,
            },
        ],
    }
}

pub fn sample_run_summaries() -> Vec<RunSummary> {
    let run = sample_run();
    vec![run.summary()]
}

pub fn provider_status_snapshot() -> ProviderStatusSnapshot {
    ProviderStatusSnapshot {
        workspace_id: s("workspace_demo"),
        mode: ProviderStatusMode::LocalAlphaNoCredentials,
        generated_at: s("local-alpha-static"),
        entries: vec![
            ProviderQuotaStatus {
                id: s("managed_model_pool"),
                label: s("Managed model pool"),
                category: LedgerCategory::Model,
                quota_owner: QuotaOwner::ManagedPro,
                readiness: ProviderReadiness::Deferred,
                credential_policy: CredentialPolicy::ManagedProLater,
                cooldown: CooldownState {
                    state: CooldownKind::NotApplicable,
                    retry_after_seconds: None,
                    reason: Some(s("Hosted model execution is not connected in this slice.")),
                },
                note: s(
                    "Reserved for Pro-managed model capacity after auth, billing, and queue boundaries exist.",
                ),
            },
            ProviderQuotaStatus {
                id: s("workspace_search_pool"),
                label: s("Workspace search pool"),
                category: LedgerCategory::Search,
                quota_owner: QuotaOwner::Workspace,
                readiness: ProviderReadiness::NotConfigured,
                credential_policy: CredentialPolicy::WorkspaceManagedLater,
                cooldown: CooldownState {
                    state: CooldownKind::Clear,
                    retry_after_seconds: None,
                    reason: Some(s("No workspace search connector is configured yet.")),
                },
                note: s(
                    "Future workspace-managed search quota will live behind explicit tenant controls.",
                ),
            },
            ProviderQuotaStatus {
                id: s("byok_search_lane"),
                label: s("BYOK search lane"),
                category: LedgerCategory::Search,
                quota_owner: QuotaOwner::UserProvided,
                readiness: ProviderReadiness::Deferred,
                credential_policy: CredentialPolicy::ByokLater,
                cooldown: CooldownState {
                    state: CooldownKind::NotApplicable,
                    retry_after_seconds: None,
                    reason: Some(s(
                        "BYOK storage and permissions are deliberately not implemented yet.",
                    )),
                },
                note: s(
                    "BYOK is tracked as a future ownership mode, not as a local credential field.",
                ),
            },
            ProviderQuotaStatus {
                id: s("uploaded_evidence_lane"),
                label: s("Uploaded evidence lane"),
                category: LedgerCategory::Evidence,
                quota_owner: QuotaOwner::UserProvided,
                readiness: ProviderReadiness::Ready,
                credential_policy: CredentialPolicy::UserEvidenceOnly,
                cooldown: CooldownState {
                    state: CooldownKind::Clear,
                    retry_after_seconds: None,
                    reason: Some(s(
                        "User-provided evidence does not consume hosted provider quota.",
                    )),
                },
                note: s(
                    "Local user-provided evidence can be attached without provider credentials.",
                ),
            },
            ProviderQuotaStatus {
                id: s("market_search_cooldown"),
                label: s("Market search cooldown bucket"),
                category: LedgerCategory::Search,
                quota_owner: QuotaOwner::ManagedPro,
                readiness: ProviderReadiness::CoolingDown,
                credential_policy: CredentialPolicy::ManagedProLater,
                cooldown: CooldownState {
                    state: CooldownKind::CoolingDown,
                    retry_after_seconds: Some(900),
                    reason: Some(s(
                        "Example cooldown state for future shared-provider pressure.",
                    )),
                },
                note: s(
                    "This static bucket lets the UI expose cooldown semantics before live routing exists.",
                ),
            },
        ],
    }
}

pub fn sample_run_by_id(run_id: &str) -> Option<ProRun> {
    let run = sample_run();
    (run.id == run_id).then_some(run)
}

impl ProRun {
    pub fn summary(&self) -> RunSummary {
        RunSummary {
            id: self.id.clone(),
            workspace_id: self.workspace_id.clone(),
            title: self.title.clone(),
            question: self.question.clone(),
            status: self.status,
            confidence: self.confidence,
            updated_at: self.updated_at.clone(),
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
        .map(|node| node.id.as_str())
        .collect::<HashSet<_>>();
    let evidence_ids = run
        .evidence
        .iter()
        .map(|evidence| evidence.id.as_str())
        .collect::<HashSet<_>>();
    let challenge_ids = run
        .challenge_checks
        .iter()
        .map(|challenge| challenge.id.as_str())
        .collect::<HashSet<_>>();

    for edge in &run.graph.edges {
        if !node_ids.contains(edge.source.as_str()) || !node_ids.contains(edge.target.as_str()) {
            return Err(format!("edge {} references an unknown node", edge.id));
        }
        assert_known_references(
            edge.id.as_str(),
            &edge.evidence_ids,
            &evidence_ids,
            "evidence",
        )?;
        assert_known_references(
            edge.id.as_str(),
            &edge.challenge_ids,
            &challenge_ids,
            "challenge",
        )?;
    }

    for node in &run.graph.nodes {
        assert_known_references(
            node.id.as_str(),
            &node.evidence_ids,
            &evidence_ids,
            "evidence",
        )?;
        assert_known_references(
            node.id.as_str(),
            &node.challenge_ids,
            &challenge_ids,
            "challenge",
        )?;
    }

    Ok(())
}

fn assert_known_references(
    owner_id: &str,
    refs: &[String],
    known_ids: &HashSet<&str>,
    label: &str,
) -> Result<(), String> {
    for referenced_id in refs {
        if !known_ids.contains(referenced_id.as_str()) {
            return Err(format!(
                "{owner_id} references unknown {label} id {referenced_id}"
            ));
        }
    }
    Ok(())
}

fn s(value: &str) -> String {
    value.to_string()
}

fn non_empty_or_default(value: Option<String>, default: &str) -> String {
    value
        .and_then(|candidate| {
            let trimmed = candidate.trim();
            (!trimmed.is_empty()).then(|| trimmed.to_string())
        })
        .unwrap_or_else(|| default.to_string())
}

fn non_empty_or_else(value: Option<String>, fallback: impl FnOnce() -> String) -> String {
    value
        .and_then(|candidate| {
            let trimmed = candidate.trim();
            (!trimmed.is_empty()).then(|| trimmed.to_string())
        })
        .unwrap_or_else(fallback)
}

fn generated_title(question: &str) -> String {
    let prefix: String = question.chars().take(72).collect();
    if question.chars().count() > 72 {
        format!("Run: {prefix}...")
    } else {
        format!("Run: {prefix}")
    }
}

#[cfg(test)]
mod tests {
    use super::{
        CooldownKind, CreateRunRequest, ProviderReadiness, RunStatus, create_run_from_request,
        provider_status_snapshot, sample_run, sample_run_by_id, sample_run_summaries,
        validate_run_references,
    };
    use std::collections::HashSet;

    #[test]
    fn sample_run_has_unique_nodes_and_bounded_scores() {
        let run = sample_run();
        let mut ids = HashSet::new();

        assert!((0.0..=1.0).contains(&run.confidence));
        assert!(!run.graph.nodes.is_empty());
        assert!(!run.graph.edges.is_empty());

        for node in &run.graph.nodes {
            assert!(ids.insert(node.id.as_str()));
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
        assert_eq!(summaries[0].id.as_str(), "run_semiconductor_controls_001");
    }

    #[test]
    fn create_run_from_request_builds_valid_in_memory_run() {
        let run = create_run_from_request(
            7,
            CreateRunRequest {
                workspace_id: Some(" workspace_alpha ".to_string()),
                title: None,
                question: "Why did renewal conversion fall?".to_string(),
            },
        )
        .expect("valid question should create a run");

        assert_eq!(run.id, "run_local_000007");
        assert_eq!(run.workspace_id, "workspace_alpha");
        assert_eq!(run.status, RunStatus::Queued);
        assert!(run.title.contains("renewal conversion"));
        assert_eq!(run.evidence[0].excerpt, "Why did renewal conversion fall?");
        validate_run_references(&run).expect("created run references should be valid");
    }

    #[test]
    fn create_run_from_request_rejects_blank_question() {
        let error = create_run_from_request(
            1,
            CreateRunRequest {
                workspace_id: None,
                title: None,
                question: "   ".to_string(),
            },
        )
        .expect_err("blank question should be rejected");

        assert_eq!(error, "question_required");
    }

    #[test]
    fn provider_status_snapshot_keeps_quota_ownership_explicit() {
        let snapshot = provider_status_snapshot();

        assert_eq!(snapshot.entries.len(), 5);
        assert!(
            snapshot
                .entries
                .iter()
                .any(|entry| matches!(entry.readiness, ProviderReadiness::NotConfigured))
        );
        assert!(
            snapshot
                .entries
                .iter()
                .any(|entry| matches!(entry.cooldown.state, CooldownKind::CoolingDown))
        );
        assert!(snapshot.entries.iter().all(|entry| {
            let combined = format!("{} {} {}", entry.id, entry.label, entry.note).to_lowercase();
            !combined.contains("api_key") && !combined.contains("secret")
        }));
    }
}
