from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult


def render_counterfactual_panel(result: AnalysisResult) -> None:
    st.header("⚡ Counterfactual Analysis")
    st.caption("Compare original vs. intervened probabilities to assess causal pathway sensitivity")

    for hyp in result.hypotheses:
        if not hyp.counterfactual_results:
            continue

        st.subheader(f"🔬 {hyp.name}")

        for cf in hyp.counterfactual_results:
            with st.container():
                col_label, col_reach = st.columns([4, 1])
                with col_label:
                    st.markdown(f"**Intervened variable:** `{cf.intervention_var}`")
                with col_reach:
                    reach_icon = "✅ Reachable" if cf.still_reachable else "❌ Blocked"
                    st.markdown(
                        f"<div style='text-align:center; font-size:1.1em'>{reach_icon}</div>",
                        unsafe_allow_html=True,
                    )

                col_orig, col_vs, col_int = st.columns([5, 1, 5])
                with col_orig:
                    st.write("**Original probability**")
                    st.progress(cf.original_path_prob, text=f"{cf.original_path_prob:.0%}")
                with col_vs:
                    st.markdown(
                        "<div style='text-align:center; padding-top:2em; font-size:1.5em'>→</div>",
                        unsafe_allow_html=True,
                    )
                with col_int:
                    st.write("**After intervention**")
                    st.progress(cf.intervened_path_prob, text=f"{cf.intervened_path_prob:.0%}")

                delta_col, sens_col, score_col = st.columns(3)
                with delta_col:
                    st.metric("Probability Δ", f"{cf.probability_delta:+.0%}")
                with sens_col:
                    st.metric(
                        "Sensitivity range",
                        f"[{cf.sensitivity_lower:.2f}, {cf.sensitivity_upper:.2f}]",
                    )
                with score_col:
                    st.metric("CF Score", f"{cf.counterfactual_score:.2f}")

                st.caption("―" * 40)
