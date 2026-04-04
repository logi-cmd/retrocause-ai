from __future__ import annotations

import streamlit as st

from retrocause.app.demo_data import DEMO_EVIDENCES, PROVIDERS, demo_result, run_real_analysis  # noqa: F401
from retrocause.app.helpers import (  # noqa: F401
    _get_evidences,
    _prob_color,
    _render_graph,
    _status_badge,
)
from retrocause.app.panels import (
    render_counterfactual_panel,
    render_factor_impact_panel,
    render_graph_panel,
    render_hypotheses_panel,
    render_sidebar_evidence,
    render_sidebar_query,
)

st.set_page_config(
    page_title="RetroCause — Causal Inference Explorer",
    page_icon="🔬",
    layout="wide",
)


def main() -> None:
    if "result" not in st.session_state:
        st.session_state["result"] = None

    new_result = render_sidebar_query(st.session_state["result"])
    if new_result is not None:
        st.session_state["result"] = new_result
        if "demo_evidences" not in st.session_state:
            st.session_state["demo_evidences"] = list(DEMO_EVIDENCES)

    result = st.session_state["result"]

    if result is None:
        st.session_state["result"] = demo_result()
        st.session_state["demo_evidences"] = list(DEMO_EVIDENCES)
        result = st.session_state["result"]

    render_graph_panel(result)

    st.divider()

    st.header("📊 Analysis Results")
    col_q, col_d, col_e = st.columns([3, 1, 1])
    with col_q:
        st.subheader(f"**Query:** {result.query}")
    with col_d:
        st.metric("Domain", result.domain.replace("_", " ").title())
    with col_e:
        st.metric("Evidence", result.total_evidence_count)
    st.caption(f"Uncertainty score: {result.total_uncertainty:.2f} — Lower is better")

    if result.hypotheses:
        top_hyp = max(result.hypotheses, key=lambda h: h.posterior_probability)
        st.success(
            f"**Leading hypothesis:** {top_hyp.name} "
            f"(posterior: {top_hyp.posterior_probability:.0%}, "
            f"confidence: [{top_hyp.confidence_interval[0]:.0%}–{top_hyp.confidence_interval[1]:.0%}])"
        )

    st.divider()

    render_hypotheses_panel(result)

    render_counterfactual_panel(result)

    render_factor_impact_panel(result)

    render_sidebar_evidence(result)

    st.divider()
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.metric("Total Evidence", result.total_evidence_count)
    with col_f2:
        st.metric("Uncertainty", f"{result.total_uncertainty:.2f}")
    with col_f3:
        st.metric("Domain", result.domain.replace("_", " ").title())

    if result.recommended_next_steps:
        with st.expander("💡 Recommended Next Steps"):
            for step in result.recommended_next_steps:
                st.write(f"- {step}")

    st.caption("Built with RetroCause — Open source causal inference framework")


if __name__ == "__main__":
    main()
