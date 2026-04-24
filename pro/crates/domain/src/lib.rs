use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KnowledgeGraph {
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GraphEdge {
    pub id: String,
    pub source: String,
    pub target: String,
    pub label: String,
    pub strength: f32,
    pub evidence_ids: Vec<String>,
    pub challenge_ids: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EvidenceAnchor {
    pub id: String,
    pub title: String,
    pub source: String,
    pub stance: EvidenceStance,
    pub freshness: EvidenceFreshness,
    pub excerpt: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChallengeCheck {
    pub id: String,
    pub title: String,
    pub status: ChallengeStatus,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceStatusCard {
    pub source: String,
    pub status: SourceStatus,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct UsageLedgerEntry {
    pub category: LedgerCategory,
    pub name: String,
    pub quota_owner: QuotaOwner,
    pub status: LedgerStatus,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProviderStatusSnapshot {
    pub workspace_id: String,
    pub mode: ProviderStatusMode,
    pub generated_at: String,
    pub entries: Vec<ProviderQuotaStatus>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkspaceAccessContext {
    pub workspace_id: String,
    pub auth_mode: WorkspaceAuthMode,
    pub enforcement_mode: WorkspaceEnforcementMode,
    pub actor: WorkspaceActor,
    pub permissions: Vec<WorkspacePermission>,
    pub safeguards: Vec<String>,
    pub sensitive_data_rules: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkspaceActor {
    pub actor_id: String,
    pub display_name: String,
    pub role: WorkspaceRole,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkspacePermission {
    pub id: String,
    pub label: String,
    pub scope: String,
    pub status: WorkspacePermissionStatus,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunEventTimeline {
    pub run_id: String,
    pub workspace_id: String,
    pub current_status: RunStatus,
    pub generated_at: String,
    pub durable: bool,
    pub events: Vec<RunEvent>,
    pub status_vocabulary: Vec<RunStatusVocabularyEntry>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunReviewComparison {
    pub run_id: String,
    pub baseline_run_id: String,
    pub workspace_id: String,
    pub mode: ReviewComparisonMode,
    pub generated_at: String,
    pub evidence_summary: ReviewDeltaSummary,
    pub challenge_summary: ReviewDeltaSummary,
    pub evidence_deltas: Vec<ReviewEvidenceDelta>,
    pub challenge_deltas: Vec<ReviewChallengeDelta>,
    pub safeguards: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReviewDeltaSummary {
    pub added: usize,
    pub changed: usize,
    pub removed: usize,
    pub unchanged: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReviewEvidenceDelta {
    pub evidence_id: String,
    pub title: String,
    pub source: String,
    pub delta: ReviewDeltaKind,
    pub stance: EvidenceStance,
    pub freshness: EvidenceFreshness,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReviewChallengeDelta {
    pub challenge_id: String,
    pub title: String,
    pub delta: ReviewDeltaKind,
    pub status: ChallengeStatus,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunEvent {
    pub id: String,
    pub sequence: u32,
    pub status: RunStatus,
    pub kind: RunEventKind,
    pub title: String,
    pub detail: String,
    pub occurred_at: String,
    pub source: RunEventSource,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunStatusVocabularyEntry {
    pub status: RunStatus,
    pub label: String,
    pub reviewable: bool,
    pub terminal: bool,
    pub requires_worker: bool,
    pub description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CooldownState {
    pub state: CooldownKind,
    pub retry_after_seconds: Option<u32>,
    pub reason: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VerificationStep {
    pub id: String,
    pub title: String,
    pub state: StepState,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
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

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    Driver,
    Enabler,
    Risk,
    Outcome,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceStance {
    Supports,
    Refutes,
    Context,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceFreshness {
    Fresh,
    Cached,
    UserProvided,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ChallengeStatus {
    Checked,
    NeedsPrimarySource,
    MissingCounterevidence,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SourceStatus {
    Verified,
    Cached,
    RateLimited,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LedgerCategory {
    Model,
    Search,
    Evidence,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum QuotaOwner {
    ManagedPro,
    Workspace,
    UserProvided,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LedgerStatus {
    Available,
    Cached,
    CoolingDown,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StepState {
    Done,
    Watching,
    Waiting,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderStatusMode {
    LocalAlphaNoCredentials,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderReadiness {
    Ready,
    NotConfigured,
    CoolingDown,
    Deferred,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CredentialPolicy {
    ManagedProLater,
    WorkspaceManagedLater,
    ByokLater,
    UserEvidenceOnly,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CooldownKind {
    Clear,
    CoolingDown,
    NotApplicable,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkspaceAuthMode {
    LocalPreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkspaceEnforcementMode {
    NotEnforcedPreview,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkspaceRole {
    PreviewOperator,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WorkspacePermissionStatus {
    PreviewAllowed,
    RequiresAuthLater,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunEventKind {
    RunAccepted,
    RetrievalStarted,
    CooldownEntered,
    PartialEvidenceReady,
    FollowupRequired,
    ReviewReady,
    Blocked,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunEventSource {
    DerivedFromRunRecord,
    FutureDurableEventStore,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ReviewComparisonMode {
    DerivedPreviousCheckpoint,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ReviewDeltaKind {
    Added,
    Changed,
    Removed,
    Unchanged,
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

pub fn workspace_access_context() -> WorkspaceAccessContext {
    WorkspaceAccessContext {
        workspace_id: s("workspace_demo"),
        auth_mode: WorkspaceAuthMode::LocalPreviewOnly,
        enforcement_mode: WorkspaceEnforcementMode::NotEnforcedPreview,
        actor: WorkspaceActor {
            actor_id: s("local_preview_operator"),
            display_name: s("Local preview operator"),
            role: WorkspaceRole::PreviewOperator,
        },
        permissions: vec![
            WorkspacePermission {
                id: s("create_preview_run"),
                label: s("Create preview runs"),
                scope: s("workspace_demo"),
                status: WorkspacePermissionStatus::PreviewAllowed,
            },
            WorkspacePermission {
                id: s("inspect_knowledge_graph"),
                label: s("Inspect graph and evidence"),
                scope: s("workspace_demo"),
                status: WorkspacePermissionStatus::PreviewAllowed,
            },
            WorkspacePermission {
                id: s("enqueue_preview_job"),
                label: s("Queue preview-only jobs"),
                scope: s("workspace_demo"),
                status: WorkspacePermissionStatus::PreviewAllowed,
            },
            WorkspacePermission {
                id: s("execute_provider_calls"),
                label: s("Execute provider calls"),
                scope: s("provider_lanes"),
                status: WorkspacePermissionStatus::RequiresAuthLater,
            },
            WorkspacePermission {
                id: s("manage_workspace_credentials"),
                label: s("Manage workspace credentials"),
                scope: s("credential_vault"),
                status: WorkspacePermissionStatus::RequiresAuthLater,
            },
            WorkspacePermission {
                id: s("view_billing_and_quota"),
                label: s("View billing and quota ledger"),
                scope: s("billing"),
                status: WorkspacePermissionStatus::RequiresAuthLater,
            },
        ],
        safeguards: vec![
            s("auth_enforcement_disabled_preview_only"),
            s("no_sessions_or_cookies_issued"),
            s("no_jwt_validation_in_this_slice"),
            s("no_provider_credentials_read"),
            s("no_billing_or_quota_mutation"),
        ],
        sensitive_data_rules: vec![
            s("requests_must_not_carry_provider_keys"),
            s("future_credentials_live_in_vault_owned_by_worker_boundary"),
            s("workspace_id_is_demo_tenant_not_acl"),
        ],
    }
}

pub fn run_event_timeline(run: &ProRun) -> RunEventTimeline {
    let mut events = Vec::new();
    push_run_event(
        &mut events,
        run,
        RunStatus::Queued,
        RunEventKind::RunAccepted,
        "Run accepted",
        format!("Question captured for workspace {}.", run.workspace_id),
    );

    match run.status {
        RunStatus::Queued => {}
        RunStatus::Running => {
            push_run_event(
                &mut events,
                run,
                RunStatus::Running,
                RunEventKind::RetrievalStarted,
                "Retrieval started",
                "A future worker would now retrieve sources and normalize evidence.",
            );
        }
        RunStatus::CoolingDown => {
            push_run_event(
                &mut events,
                run,
                RunStatus::Running,
                RunEventKind::RetrievalStarted,
                "Retrieval started",
                "The run attempted provider or source work before entering cooldown.",
            );
            push_run_event(
                &mut events,
                run,
                RunStatus::CoolingDown,
                RunEventKind::CooldownEntered,
                "Cooldown entered",
                "A provider or source lane is cooling down; retry-after state should be visible.",
            );
        }
        RunStatus::PartialLive => {
            push_retrieval_and_partial_events(&mut events, run);
        }
        RunStatus::NeedsFollowup => {
            push_retrieval_and_partial_events(&mut events, run);
            push_run_event(
                &mut events,
                run,
                RunStatus::NeedsFollowup,
                RunEventKind::FollowupRequired,
                "Follow-up required",
                "Review found a gap that must be checked before the run is ready.",
            );
        }
        RunStatus::ReadyForReview => {
            push_retrieval_and_partial_events(&mut events, run);
            push_run_event(
                &mut events,
                run,
                RunStatus::ReadyForReview,
                RunEventKind::ReviewReady,
                "Ready for review",
                format!(
                    "Run has {} graph nodes, {} evidence anchors, and {} challenge checks.",
                    run.graph.nodes.len(),
                    run.evidence.len(),
                    run.challenge_checks.len()
                ),
            );
        }
        RunStatus::Blocked => {
            push_run_event(
                &mut events,
                run,
                RunStatus::Blocked,
                RunEventKind::Blocked,
                "Run blocked",
                "The run cannot progress until a missing precondition is resolved.",
            );
        }
    }

    RunEventTimeline {
        run_id: run.id.clone(),
        workspace_id: run.workspace_id.clone(),
        current_status: run.status,
        generated_at: format!("derived-from:{}", run.updated_at),
        durable: false,
        events,
        status_vocabulary: run_status_vocabulary(),
        safeguards: vec![
            s("non_durable_timeline_derived_from_run_record"),
            s("no_event_store_connection_in_this_slice"),
            s("no_worker_or_provider_execution_from_events"),
            s("event_ids_are_preview_only"),
        ],
    }
}

pub fn run_status_vocabulary() -> Vec<RunStatusVocabularyEntry> {
    vec![
        status_vocabulary_entry(
            RunStatus::Queued,
            "Queued",
            false,
            false,
            false,
            "Run was accepted, but provider/search work has not started.",
        ),
        status_vocabulary_entry(
            RunStatus::Running,
            "Running",
            false,
            false,
            true,
            "A worker is expected to retrieve, extract, or synthesize evidence.",
        ),
        status_vocabulary_entry(
            RunStatus::CoolingDown,
            "Cooling down",
            false,
            false,
            true,
            "A provider or source lane needs a retry-after window before continuing.",
        ),
        status_vocabulary_entry(
            RunStatus::PartialLive,
            "Partial live",
            true,
            false,
            true,
            "Some evidence is inspectable while one or more lanes are degraded.",
        ),
        status_vocabulary_entry(
            RunStatus::NeedsFollowup,
            "Needs follow-up",
            true,
            false,
            true,
            "The run has usable findings but still needs a targeted review action.",
        ),
        status_vocabulary_entry(
            RunStatus::ReadyForReview,
            "Ready for review",
            true,
            true,
            false,
            "The run has enough evidence, challenge checks, and source state to review.",
        ),
        status_vocabulary_entry(
            RunStatus::Blocked,
            "Blocked",
            false,
            true,
            false,
            "The run cannot continue until a missing requirement is resolved.",
        ),
    ]
}

pub fn run_review_comparison(run: &ProRun) -> RunReviewComparison {
    let baseline = review_baseline_for_run(run);
    run_review_comparison_between(run, &baseline)
}

pub fn run_review_comparison_between(run: &ProRun, baseline: &ProRun) -> RunReviewComparison {
    let evidence_deltas = evidence_deltas(run, baseline);
    let challenge_deltas = challenge_deltas(run, baseline);

    RunReviewComparison {
        run_id: run.id.clone(),
        baseline_run_id: baseline.id.clone(),
        workspace_id: run.workspace_id.clone(),
        mode: ReviewComparisonMode::DerivedPreviousCheckpoint,
        generated_at: format!("derived-review-comparison:{}", run.updated_at),
        evidence_summary: summarize_evidence_deltas(&evidence_deltas),
        challenge_summary: summarize_challenge_deltas(&challenge_deltas),
        evidence_deltas,
        challenge_deltas,
        safeguards: vec![
            s("comparison_preview_derived_from_current_run"),
            s("no_historical_run_store_query_in_this_slice"),
            s("no_cross_workspace_access_or_auth_enforcement"),
            s("no_provider_calls_or_credential_reads"),
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

fn review_baseline_for_run(run: &ProRun) -> ProRun {
    let mut baseline = run.clone();
    baseline.id = format!("{}_previous_checkpoint", run.id);
    baseline.updated_at = format!("derived-before:{}", run.updated_at);
    baseline.status = match run.status {
        RunStatus::ReadyForReview => RunStatus::NeedsFollowup,
        RunStatus::NeedsFollowup => RunStatus::PartialLive,
        status => status,
    };
    baseline.evidence.pop();
    baseline.challenge_checks.pop();
    baseline
}

fn evidence_deltas(run: &ProRun, baseline: &ProRun) -> Vec<ReviewEvidenceDelta> {
    let baseline_by_id = baseline
        .evidence
        .iter()
        .map(|evidence| (evidence.id.as_str(), evidence))
        .collect::<HashMap<_, _>>();
    let current_by_id = run
        .evidence
        .iter()
        .map(|evidence| (evidence.id.as_str(), evidence))
        .collect::<HashMap<_, _>>();

    let mut deltas = run
        .evidence
        .iter()
        .map(|evidence| match baseline_by_id.get(evidence.id.as_str()) {
            Some(previous) if same_evidence(evidence, previous) => evidence_delta(
                evidence,
                ReviewDeltaKind::Unchanged,
                "Already present in the derived previous checkpoint.",
            ),
            Some(_) => evidence_delta(
                evidence,
                ReviewDeltaKind::Changed,
                "Evidence metadata or excerpt changed since the derived previous checkpoint.",
            ),
            None => evidence_delta(
                evidence,
                ReviewDeltaKind::Added,
                "New evidence anchor visible in the current run preview.",
            ),
        })
        .collect::<Vec<_>>();

    deltas.extend(
        baseline
            .evidence
            .iter()
            .filter(|evidence| !current_by_id.contains_key(evidence.id.as_str()))
            .map(|evidence| {
                evidence_delta(
                    evidence,
                    ReviewDeltaKind::Removed,
                    "Evidence anchor existed in the derived previous checkpoint but is absent now.",
                )
            }),
    );
    deltas
}

fn challenge_deltas(run: &ProRun, baseline: &ProRun) -> Vec<ReviewChallengeDelta> {
    let baseline_by_id = baseline
        .challenge_checks
        .iter()
        .map(|challenge| (challenge.id.as_str(), challenge))
        .collect::<HashMap<_, _>>();
    let current_by_id = run
        .challenge_checks
        .iter()
        .map(|challenge| (challenge.id.as_str(), challenge))
        .collect::<HashMap<_, _>>();

    let mut deltas = run
        .challenge_checks
        .iter()
        .map(
            |challenge| match baseline_by_id.get(challenge.id.as_str()) {
                Some(previous) if same_challenge(challenge, previous) => challenge_delta(
                    challenge,
                    ReviewDeltaKind::Unchanged,
                    "Challenge check was already present in the derived previous checkpoint.",
                ),
                Some(_) => challenge_delta(
                    challenge,
                    ReviewDeltaKind::Changed,
                    "Challenge check status or note changed since the derived previous checkpoint.",
                ),
                None => challenge_delta(
                    challenge,
                    ReviewDeltaKind::Added,
                    "New challenge check visible in the current run preview.",
                ),
            },
        )
        .collect::<Vec<_>>();

    deltas.extend(
        baseline
            .challenge_checks
            .iter()
            .filter(|challenge| !current_by_id.contains_key(challenge.id.as_str()))
            .map(|challenge| {
                challenge_delta(
                    challenge,
                    ReviewDeltaKind::Removed,
                    "Challenge check existed in the derived previous checkpoint but is absent now.",
                )
            }),
    );
    deltas
}

fn evidence_delta(
    evidence: &EvidenceAnchor,
    delta: ReviewDeltaKind,
    note: &str,
) -> ReviewEvidenceDelta {
    ReviewEvidenceDelta {
        evidence_id: evidence.id.clone(),
        title: evidence.title.clone(),
        source: evidence.source.clone(),
        delta,
        stance: evidence.stance,
        freshness: evidence.freshness,
        note: note.to_string(),
    }
}

fn challenge_delta(
    challenge: &ChallengeCheck,
    delta: ReviewDeltaKind,
    note: &str,
) -> ReviewChallengeDelta {
    ReviewChallengeDelta {
        challenge_id: challenge.id.clone(),
        title: challenge.title.clone(),
        delta,
        status: challenge.status,
        note: note.to_string(),
    }
}

fn same_evidence(left: &EvidenceAnchor, right: &EvidenceAnchor) -> bool {
    left.title == right.title
        && left.source == right.source
        && left.stance == right.stance
        && left.freshness == right.freshness
        && left.excerpt == right.excerpt
}

fn same_challenge(left: &ChallengeCheck, right: &ChallengeCheck) -> bool {
    left.title == right.title && left.status == right.status && left.note == right.note
}

fn summarize_evidence_deltas(deltas: &[ReviewEvidenceDelta]) -> ReviewDeltaSummary {
    summarize_deltas(deltas.iter().map(|delta| delta.delta))
}

fn summarize_challenge_deltas(deltas: &[ReviewChallengeDelta]) -> ReviewDeltaSummary {
    summarize_deltas(deltas.iter().map(|delta| delta.delta))
}

fn summarize_deltas(kinds: impl Iterator<Item = ReviewDeltaKind>) -> ReviewDeltaSummary {
    let mut summary = ReviewDeltaSummary {
        added: 0,
        changed: 0,
        removed: 0,
        unchanged: 0,
    };

    for kind in kinds {
        match kind {
            ReviewDeltaKind::Added => summary.added += 1,
            ReviewDeltaKind::Changed => summary.changed += 1,
            ReviewDeltaKind::Removed => summary.removed += 1,
            ReviewDeltaKind::Unchanged => summary.unchanged += 1,
        }
    }
    summary
}

fn push_retrieval_and_partial_events(events: &mut Vec<RunEvent>, run: &ProRun) {
    push_run_event(
        events,
        run,
        RunStatus::Running,
        RunEventKind::RetrievalStarted,
        "Retrieval started",
        "Source and provider routing produced evidence candidates for graph synthesis.",
    );
    push_run_event(
        events,
        run,
        RunStatus::PartialLive,
        RunEventKind::PartialEvidenceReady,
        "Evidence available",
        format!(
            "{} evidence anchors and {} source cards are visible for inspection.",
            run.evidence.len(),
            run.sources.len()
        ),
    );
}

fn push_run_event(
    events: &mut Vec<RunEvent>,
    run: &ProRun,
    status: RunStatus,
    kind: RunEventKind,
    title: &str,
    detail: impl Into<String>,
) {
    let sequence = (events.len() + 1) as u32;
    events.push(RunEvent {
        id: format!(
            "{}_event_{sequence:02}_{}",
            run.id,
            run_event_kind_slug(kind)
        ),
        sequence,
        status,
        kind,
        title: title.to_string(),
        detail: detail.into(),
        occurred_at: format!("{}#event-{sequence:02}", run.updated_at),
        source: RunEventSource::DerivedFromRunRecord,
    });
}

fn run_event_kind_slug(kind: RunEventKind) -> &'static str {
    match kind {
        RunEventKind::RunAccepted => "run_accepted",
        RunEventKind::RetrievalStarted => "retrieval_started",
        RunEventKind::CooldownEntered => "cooldown_entered",
        RunEventKind::PartialEvidenceReady => "partial_evidence_ready",
        RunEventKind::FollowupRequired => "followup_required",
        RunEventKind::ReviewReady => "review_ready",
        RunEventKind::Blocked => "blocked",
    }
}

fn status_vocabulary_entry(
    status: RunStatus,
    label: &str,
    reviewable: bool,
    terminal: bool,
    requires_worker: bool,
    description: &str,
) -> RunStatusVocabularyEntry {
    RunStatusVocabularyEntry {
        status,
        label: label.to_string(),
        reviewable,
        terminal,
        requires_worker,
        description: description.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::{
        CooldownKind, CreateRunRequest, ProviderReadiness, ReviewComparisonMode, ReviewDeltaKind,
        RunEventKind, RunEventSource, RunStatus, WorkspaceEnforcementMode,
        WorkspacePermissionStatus, create_run_from_request, provider_status_snapshot,
        run_event_timeline, run_review_comparison, run_status_vocabulary, sample_run,
        sample_run_by_id, sample_run_summaries, validate_run_references, workspace_access_context,
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

    #[test]
    fn workspace_access_context_is_preview_only_and_non_enforcing() {
        let context = workspace_access_context();

        assert_eq!(context.workspace_id, "workspace_demo");
        assert_eq!(
            context.enforcement_mode,
            WorkspaceEnforcementMode::NotEnforcedPreview
        );
        assert!(
            context
                .permissions
                .iter()
                .any(|permission| permission.id == "create_preview_run"
                    && permission.status == WorkspacePermissionStatus::PreviewAllowed)
        );
        assert!(
            context
                .permissions
                .iter()
                .any(|permission| permission.id == "execute_provider_calls"
                    && permission.status == WorkspacePermissionStatus::RequiresAuthLater)
        );
        assert!(
            context
                .safeguards
                .contains(&"no_provider_credentials_read".to_string())
        );
        assert!(
            context
                .sensitive_data_rules
                .contains(&"workspace_id_is_demo_tenant_not_acl".to_string())
        );
    }

    #[test]
    fn run_event_timeline_is_derived_and_contains_status_vocabulary() {
        let timeline = run_event_timeline(&sample_run());

        assert_eq!(timeline.run_id, "run_semiconductor_controls_001");
        assert_eq!(timeline.current_status, RunStatus::ReadyForReview);
        assert!(!timeline.durable);
        assert!(
            timeline
                .events
                .iter()
                .any(|event| event.kind == RunEventKind::ReviewReady
                    && event.status == RunStatus::ReadyForReview)
        );
        assert!(
            timeline
                .status_vocabulary
                .iter()
                .any(|entry| entry.status == RunStatus::PartialLive && entry.reviewable)
        );
        assert!(
            timeline
                .safeguards
                .contains(&"no_event_store_connection_in_this_slice".to_string())
        );
    }

    #[test]
    fn queued_run_event_timeline_stays_non_durable_and_minimal() {
        let run = create_run_from_request(
            8,
            CreateRunRequest {
                workspace_id: None,
                title: None,
                question: "Why did activation fall?".to_string(),
            },
        )
        .expect("valid question should create a run");

        let timeline = run_event_timeline(&run);

        assert_eq!(timeline.events.len(), 1);
        assert_eq!(timeline.events[0].status, RunStatus::Queued);
        assert_eq!(
            timeline.events[0].source,
            RunEventSource::DerivedFromRunRecord
        );
        assert_eq!(run_status_vocabulary().len(), 7);
    }

    #[test]
    fn run_review_comparison_summarizes_evidence_and_challenge_deltas() {
        let comparison = run_review_comparison(&sample_run());

        assert_eq!(comparison.run_id, "run_semiconductor_controls_001");
        assert_eq!(
            comparison.baseline_run_id,
            "run_semiconductor_controls_001_previous_checkpoint"
        );
        assert_eq!(
            comparison.mode,
            ReviewComparisonMode::DerivedPreviousCheckpoint
        );
        assert_eq!(comparison.evidence_summary.added, 1);
        assert_eq!(comparison.challenge_summary.added, 1);
        assert!(comparison.evidence_summary.unchanged > 0);
        assert!(
            comparison
                .evidence_deltas
                .iter()
                .any(|delta| delta.evidence_id == "ev_market_move"
                    && delta.delta == ReviewDeltaKind::Added)
        );
        assert!(
            comparison
                .challenge_deltas
                .iter()
                .any(|delta| delta.challenge_id == "cc_countermove"
                    && delta.delta == ReviewDeltaKind::Added)
        );
        assert!(
            comparison
                .safeguards
                .contains(&"no_provider_calls_or_credential_reads".to_string())
        );
    }

    #[test]
    fn queued_run_review_comparison_keeps_preview_deltas_local() {
        let run = create_run_from_request(
            9,
            CreateRunRequest {
                workspace_id: Some("workspace_alpha".to_string()),
                title: None,
                question: "Why did activation fall?".to_string(),
            },
        )
        .expect("valid question should create a run");

        let comparison = run_review_comparison(&run);

        assert_eq!(comparison.workspace_id, "workspace_alpha");
        assert_eq!(comparison.evidence_summary.added, 1);
        assert_eq!(comparison.challenge_summary.added, 1);
        assert_eq!(comparison.evidence_deltas[0].delta, ReviewDeltaKind::Added);
    }
}
