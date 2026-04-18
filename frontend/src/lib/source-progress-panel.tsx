type PipelineProgress = {
  step: string;
  stepIndex: number;
  totalSteps: number;
  message: string;
} | null;

const progressStageOrder = [
  "EvidenceCollectionStep",
  "GraphBuildingStep",
  "HypothesisGenerationStep",
  "EvidenceAnchoringStep",
  "CausalRAGStep",
  "RefutationCoverageStep",
  "CounterfactualVerificationStep",
  "UncertaintyAssessmentStep",
  "EvaluationStep",
];

function progressStageLabel(step: string, locale: "zh" | "en"): string {
  const labels: Record<string, { en: string; zh: string }> = {
    EvidenceCollectionStep: { en: "Finding and reading evidence", zh: "\u68c0\u7d22\u5e76\u8bfb\u53d6\u8bc1\u636e" },
    GraphBuildingStep: { en: "Building the causal map", zh: "\u6784\u5efa\u56e0\u679c\u56fe" },
    HypothesisGenerationStep: { en: "Comparing explanation chains", zh: "\u751f\u6210\u89e3\u91ca\u94fe" },
    EvidenceAnchoringStep: { en: "Linking evidence to edges", zh: "\u7ed1\u5b9a\u8bc1\u636e\u94fe" },
    CausalRAGStep: { en: "Filling weak coverage", zh: "\u8865\u5145\u8584\u5f31\u8bc1\u636e" },
    RefutationCoverageStep: { en: "Searching for challenges", zh: "\u68c0\u7d22\u53cd\u8bc1\u4e0e\u66ff\u4ee3\u89e3\u91ca" },
    CounterfactualVerificationStep: { en: "Checking what-if signals", zh: "\u6821\u9a8c\u53cd\u4e8b\u5b9e\u4fe1\u53f7" },
    DebateRefinementStep: { en: "Refining claims", zh: "\u7cbe\u70bc\u7ed3\u8bba" },
    UncertaintyAssessmentStep: { en: "Estimating uncertainty", zh: "\u8bc4\u4f30\u4e0d\u786e\u5b9a\u6027" },
    EvaluationStep: { en: "Scoring result quality", zh: "\u8bc4\u4f30\u7ed3\u679c\u8d28\u91cf" },
  };
  const label = labels[step];
  if (label) return locale === "en" ? label.en : label.zh;
  return step.replace(/([a-z])([A-Z])/g, "$1 $2");
}

type SourceProgressPanelProps = {
  loading: boolean;
  mode: "live" | "partial_live" | "demo";
  pipelineProgress: PipelineProgress;
  partialLiveReasons: string[];
  locale: "zh" | "en";
};

export function SourceProgressPanel({
  loading,
  mode,
  pipelineProgress,
  partialLiveReasons,
  locale,
}: SourceProgressPanelProps) {
  const activeProgressIndex = pipelineProgress
    ? Math.max(
        progressStageOrder.indexOf(pipelineProgress.step),
        Math.max(0, pipelineProgress.stepIndex - 1)
      )
    : -1;

  const showProgress = loading && pipelineProgress;
  const showPartialReasons = mode === "partial_live" && partialLiveReasons.length > 0;

  if (!showProgress && !showPartialReasons) return null;

  return (
    <>
      {showProgress && (
        <div className="retrieval-progress" style={{ marginTop: "10px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "8px",
              marginBottom: "8px",
            }}
          >
            <span
              style={{
                fontSize: "0.52rem",
                color: "#4a7a9e",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              {locale === "en" ? "Retrieval trace" : "\u68c0\u7d22\u8f68\u8ff9"}
            </span>
            <span style={{ fontSize: "0.52rem", color: "#8b7355" }}>
              {pipelineProgress.stepIndex}/{pipelineProgress.totalSteps}
            </span>
          </div>
          <div style={{ display: "grid", gap: "4px" }}>
            {progressStageOrder.map((step, index) => {
              const isActive = index === activeProgressIndex;
              const isDone = index < activeProgressIndex;
              return (
                <div
                  key={step}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "0.55rem",
                    color: isActive ? "#3b6ea5" : isDone ? "#5a7a52" : "#8b7355",
                    opacity: isActive || isDone ? 1 : 0.58,
                  }}
                >
                  <span
                    style={{
                      width: "7px",
                      height: "7px",
                      borderRadius: "999px",
                      background: isActive
                        ? "#3b6ea5"
                        : isDone
                          ? "#5a7a52"
                          : "rgba(160,140,110,0.28)",
                      boxShadow: isActive ? "0 0 0 4px rgba(59,110,165,0.12)" : undefined,
                      flex: "0 0 auto",
                    }}
                  />
                  <span>{progressStageLabel(step, locale)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {showPartialReasons && (
        <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px dashed rgba(160,140,110,0.18)" }}>
          <div
            style={{
              fontSize: "0.52rem",
              color: "#8b7355",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "4px",
            }}
          >
            {locale === "en" ? "Why partial live" : "\u90e8\u5206 live \u539f\u56e0"}
          </div>
          {partialLiveReasons.slice(0, 3).map((reason, index) => (
            <div
              key={`${reason}-${index}`}
              style={{ fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45, marginBottom: "3px" }}
            >
              {locale === "en" ? "- " : "- "}
              {reason}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
