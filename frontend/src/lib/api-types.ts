export type ApiNode = {
  id: string;
  label: string;
  description: string;
  probability: number;
  type: string;
  depth: number;
  upstream_ids: string[];
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
  uncertainty?: {
    uncertainty_types: string[];
    overall_score: number;
    data_uncertainty: number;
    model_uncertainty: number;
    explanation: string;
  } | null;
};

export type ApiEdge = {
  id: string;
  source: string;
  target: string;
  strength: number;
  type: string;
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
  citation_spans?: Array<{
    evidence_id: string;
    start_char: number;
    end_char: number;
    quoted_text: string;
    relevance_score: number;
  }>;
  evidence_conflict?: string;
  refutation_status?: string;
};

export type ApiEvidence = {
  id: string;
  content: string;
  source: string;
  reliability: string;
  is_supporting: boolean;
  source_tier?: string;
  freshness?: string;
  timestamp?: string | null;
  extraction_method?: string;
  stance?: "supporting" | "refuting" | "context";
  stance_basis?: string;
};

export type ApiChain = {
  chain_id: string;
  label: string;
  description: string;
  probability: number;
  depth: number;
  nodes: ApiNode[];
  edges: ApiEdge[];
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
  refutation_status?: string;
};

export type ApiRetrievalTrace = {
  source: string;
  source_label?: string;
  source_kind?: string;
  stability?: string;
  query: string;
  result_count: number;
  cache_hit?: boolean;
  error?: string | null;
  status?: string | null;
  retry_after_seconds?: number | null;
  cache_policy?: string | null;
};

export type ApiChallengeCheck = {
  edge_id: string;
  source: string;
  target: string;
  query: string;
  result_count: number;
  refuting_count: number;
  context_count: number;
  status: string;
};

export type ApiAnalysisBrief = {
  answer: string;
  confidence: number;
  top_reasons: string[];
  challenge_summary: string;
  missing_evidence: string[];
  source_coverage: string;
};

export type ApiHarnessCheck = {
  id: string;
  label: string;
  status: "pass" | "warn" | "fail" | string;
  detail: string;
};

export type ApiProductHarness = {
  name: string;
  score: number;
  status: string;
  user_value_summary: string;
  checks: ApiHarnessCheck[];
  next_actions: string[];
};

export type ApiScenario = {
  key: string;
  label: string;
  confidence: number;
  detection_method: string;
  user_value: string;
};

export type ApiProductionBriefItem = {
  title: string;
  summary: string;
  evidence_ids: string[];
  confidence: number;
};

export type ApiProductionBriefSection = {
  kind: string;
  title: string;
  items: ApiProductionBriefItem[];
};

export type ApiProductionBrief = {
  title: string;
  scenario_key: string;
  executive_summary: string;
  sections: ApiProductionBriefSection[];
  limits: string[];
  next_verification_steps: string[];
};

export type ApiProductionHarness = {
  status: string;
  score: number;
  scenario_key: string;
  checks: Array<{
    name: string;
    passed: boolean;
    severity: string;
    message: string;
  }>;
  next_actions: string[];
};

export type ApiProviderPreflight = {
  provider: string;
  model_name: string;
  status: string;
  can_run_analysis: boolean;
  failure_code?: string | null;
  diagnosis: string;
  user_action: string;
  checks: ApiHarnessCheck[];
};

export type ApiRunStep = {
  id: string;
  label: string;
  status: string;
  detail: string;
};

export type ApiUsageLedgerItem = {
  category: string;
  name: string;
  quota_owner: string;
  status: string;
  count: number;
  detail: string;
};

export type ApiSavedRunSummary = {
  run_id: string;
  query: string;
  run_status: string;
  analysis_mode: string;
  created_at: string;
  scenario_key: string;
};

export type AnalyzeResponseV2 = {
  query: string;
  run_id?: string | null;
  run_status?: string;
  run_steps?: ApiRunStep[];
  usage_ledger?: ApiUsageLedgerItem[];
  is_demo: boolean;
  demo_topic: string | null;
  analysis_mode: "live" | "partial_live" | "demo";
  freshness_status: string;
  time_range?: string | null;
  partial_live_reasons?: string[];
  recommended_chain_id: string | null;
  evidences: ApiEvidence[];
  chains: ApiChain[];
  retrieval_trace?: ApiRetrievalTrace[];
  challenge_checks?: ApiChallengeCheck[];
  analysis_brief?: ApiAnalysisBrief | null;
  markdown_brief?: string | null;
  product_harness?: ApiProductHarness | null;
  scenario?: ApiScenario | null;
  production_brief?: ApiProductionBrief | null;
  production_harness?: ApiProductionHarness | null;
  evaluation?: {
    evidence_sufficiency: number;
    probability_coherence: number;
    chain_diversity: number;
    overall_confidence: number;
    weaknesses: string[];
    recommended_actions: string[];
  } | null;
  uncertainty_report?: {
    per_node: Record<
      string,
      {
        uncertainty_types: string[];
        overall_score: number;
        data_uncertainty: number;
        model_uncertainty: number;
        explanation: string;
      }
    >;
    per_edge: Record<
      string,
      {
        uncertainty_types: string[];
        overall_score: number;
        data_uncertainty: number;
        model_uncertainty: number;
        explanation: string;
      }
    >;
    evidence_conflicts: Record<string, string>;
    overall_uncertainty: number;
    dominant_uncertainty_type: string | null;
    summary: string;
  } | null;
  error?: string | null;
};

export type AnalysisUiState = {
  isDemo: boolean;
  demoTopic: string | null;
  loading: boolean;
  mode: "live" | "partial_live" | "demo";
  freshnessStatus: string;
  timeRange: string | null;
  partialLiveReasons: string[];
};
