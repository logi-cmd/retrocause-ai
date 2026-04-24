use retrocause_pro_domain::{
    CooldownKind, LedgerCategory, ProviderQuotaStatus, ProviderReadiness, ProviderStatusSnapshot,
    QuotaOwner, provider_status_snapshot,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize)]
pub struct RoutingPreviewRequest {
    pub workspace_id: Option<String>,
    pub query: String,
    pub scenario: Option<RoutingScenario>,
    pub source_policy: Option<SourcePolicy>,
}

#[derive(Clone, Debug, Serialize)]
pub struct RoutingPreviewPlan {
    pub workspace_id: String,
    pub query: String,
    pub scenario: RoutingScenario,
    pub source_policy: SourcePolicy,
    pub mode: RoutingMode,
    pub execution_allowed: bool,
    pub selected_lane_id: Option<String>,
    pub steps: Vec<RoutingStep>,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct RoutingStep {
    pub lane_id: String,
    pub label: String,
    pub category: LedgerCategory,
    pub quota_owner: QuotaOwner,
    pub readiness: ProviderReadiness,
    pub decision: RoutingDecision,
    pub action: RoutingAction,
    pub retry_after_seconds: Option<u32>,
    pub reason: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingScenario {
    Auto,
    Market,
    Policy,
    Postmortem,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SourcePolicy {
    Balanced,
    PrimaryOnly,
    UserEvidenceOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingMode {
    PreviewOnly,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingDecision {
    Selectable,
    CoolingDown,
    NotConfigured,
    Deferred,
}

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoutingAction {
    UseUploadedEvidence,
    WaitForCooldown,
    ConfigureWorkspaceQuota,
    DeferHostedProvider,
}

#[derive(Debug)]
pub enum RoutingPreviewError {
    QueryRequired,
}

pub fn build_routing_preview(
    request: RoutingPreviewRequest,
) -> Result<RoutingPreviewPlan, RoutingPreviewError> {
    build_routing_preview_from_status(request, provider_status_snapshot())
}

pub fn build_routing_preview_from_status(
    request: RoutingPreviewRequest,
    snapshot: ProviderStatusSnapshot,
) -> Result<RoutingPreviewPlan, RoutingPreviewError> {
    let query = request.query.trim();
    if query.is_empty() {
        return Err(RoutingPreviewError::QueryRequired);
    }

    let scenario = request.scenario.unwrap_or(RoutingScenario::Auto);
    let source_policy = request.source_policy.unwrap_or(SourcePolicy::Balanced);
    let workspace_id = request
        .workspace_id
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or(snapshot.workspace_id.as_str())
        .to_string();

    let steps = snapshot
        .entries
        .iter()
        .map(|entry| routing_step_for(entry, source_policy))
        .collect::<Vec<RoutingStep>>();
    let selected_lane_id = steps
        .iter()
        .find(|step| matches!(step.decision, RoutingDecision::Selectable))
        .map(|step| step.lane_id.clone());

    Ok(RoutingPreviewPlan {
        workspace_id,
        query: query.to_string(),
        scenario,
        source_policy,
        mode: RoutingMode::PreviewOnly,
        execution_allowed: false,
        selected_lane_id,
        steps,
        warnings: vec![
            "preview_only_no_provider_calls".to_string(),
            "hosted_provider_execution_deferred".to_string(),
        ],
    })
}

fn routing_step_for(entry: &ProviderQuotaStatus, source_policy: SourcePolicy) -> RoutingStep {
    let (decision, action, reason) = match entry.readiness {
        ProviderReadiness::Ready => {
            if source_policy == SourcePolicy::PrimaryOnly
                && matches!(entry.category, LedgerCategory::Evidence)
            {
                (
                    RoutingDecision::Deferred,
                    RoutingAction::DeferHostedProvider,
                    "Primary-only routing needs hosted source adapters that are not connected yet.",
                )
            } else {
                (
                    RoutingDecision::Selectable,
                    RoutingAction::UseUploadedEvidence,
                    "User-provided evidence is locally usable without provider credentials.",
                )
            }
        }
        ProviderReadiness::CoolingDown => (
            RoutingDecision::CoolingDown,
            RoutingAction::WaitForCooldown,
            "Shared provider lane is cooling down; future executor should queue or use another lane.",
        ),
        ProviderReadiness::NotConfigured => (
            RoutingDecision::NotConfigured,
            RoutingAction::ConfigureWorkspaceQuota,
            "Workspace-managed quota is not configured.",
        ),
        ProviderReadiness::Deferred => (
            RoutingDecision::Deferred,
            RoutingAction::DeferHostedProvider,
            "Hosted provider execution is planned but not implemented in this keyless slice.",
        ),
    };

    RoutingStep {
        lane_id: entry.id.clone(),
        label: entry.label.clone(),
        category: entry.category,
        quota_owner: entry.quota_owner,
        readiness: entry.readiness,
        decision,
        action,
        retry_after_seconds: match entry.cooldown.state {
            CooldownKind::CoolingDown => entry.cooldown.retry_after_seconds,
            CooldownKind::Clear | CooldownKind::NotApplicable => None,
        },
        reason: reason.to_string(),
    }
}

impl std::fmt::Display for RoutingPreviewError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::QueryRequired => write!(formatter, "query_required"),
        }
    }
}

impl std::error::Error for RoutingPreviewError {}

#[cfg(test)]
mod tests {
    use super::{
        RoutingDecision, RoutingPreviewError, RoutingPreviewRequest, RoutingScenario, SourcePolicy,
        build_routing_preview,
    };

    #[test]
    fn preview_selects_user_evidence_without_allowing_execution() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: Some(" workspace_alpha ".to_string()),
            query: "Why did renewal conversion drop?".to_string(),
            scenario: Some(RoutingScenario::Postmortem),
            source_policy: Some(SourcePolicy::Balanced),
        })
        .expect("routing preview should build");

        assert_eq!(plan.workspace_id, "workspace_alpha");
        assert_eq!(plan.scenario, RoutingScenario::Postmortem);
        assert!(!plan.execution_allowed);
        assert_eq!(
            plan.selected_lane_id.as_deref(),
            Some("uploaded_evidence_lane")
        );
        assert!(
            plan.warnings
                .contains(&"preview_only_no_provider_calls".to_string())
        );
    }

    #[test]
    fn preview_surfaces_cooling_down_lanes() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "Why did chip stocks move?".to_string(),
            scenario: Some(RoutingScenario::Market),
            source_policy: None,
        })
        .expect("routing preview should build");

        let cooldown = plan
            .steps
            .iter()
            .find(|step| step.lane_id == "market_search_cooldown")
            .expect("cooldown lane should be present");

        assert_eq!(cooldown.decision, RoutingDecision::CoolingDown);
        assert_eq!(cooldown.retry_after_seconds, Some(900));
    }

    #[test]
    fn primary_only_policy_does_not_select_uploaded_evidence_lane() {
        let plan = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "Why did a policy update matter?".to_string(),
            scenario: None,
            source_policy: Some(SourcePolicy::PrimaryOnly),
        })
        .expect("routing preview should build");

        assert_eq!(plan.source_policy, SourcePolicy::PrimaryOnly);
        assert_eq!(plan.selected_lane_id, None);
    }

    #[test]
    fn blank_query_is_rejected() {
        let error = build_routing_preview(RoutingPreviewRequest {
            workspace_id: None,
            query: "   ".to_string(),
            scenario: None,
            source_policy: None,
        })
        .expect_err("blank query should fail");

        assert!(matches!(error, RoutingPreviewError::QueryRequired));
        assert_eq!(error.to_string(), "query_required");
    }
}
