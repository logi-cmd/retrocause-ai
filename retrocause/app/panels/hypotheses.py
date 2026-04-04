from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult
from retrocause.app.helpers import _status_badge


def render_hypotheses_panel(result: AnalysisResult) -> None:
    st.header("🔗 Hypothesis Chains")
    st.caption(f"{len(result.hypotheses)} competing hypotheses")

    for hyp in result.hypotheses:
        status_text = _status_badge(hyp.status)

        with st.container():
            col_name, col_status, col_cf = st.columns([3, 1, 1])
            with col_name:
                st.subheader(f"{hyp.name}")
            with col_status:
                st.markdown(
                    f"<div style='text-align:right'>{status_text}</div>", unsafe_allow_html=True
                )
            with col_cf:
                st.metric("CF Score", f"{hyp.counterfactual_score:.2f}")

            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Path Prob.", f"{hyp.path_probability:.0%}")
            with mc2:
                st.metric("Posterior", f"{hyp.posterior_probability:.0%}")
            with mc3:
                lo, hi = hyp.confidence_interval
                st.metric("CI", f"[{lo:.0%}, {hi:.0%}]")
            with mc4:
                st.metric("Coverage", f"{hyp.evidence_coverage:.0%}")

            st.write(hyp.description)

            with st.expander("📊 Details"):
                st.write("**Variables:**")
                for v in hyp.variables:
                    st.write(f"- `{v.name}` — {v.description} (support: {v.posterior_support:.2f})")

                if hyp.unanchored_edges:
                    st.warning(f"**Unanchored edges:** {', '.join(hyp.unanchored_edges)}")

                if hyp.debate_rounds:
                    st.write("**Debate rounds:**")
                    for rnd in hyp.debate_rounds:
                        round_num = rnd.get("round", "?")
                        with st.container():
                            st.markdown(f"**Round {round_num}**")
                            roles = [
                                "abductive",
                                "deductive",
                                "inductive",
                                "devil_advocate",
                                "arbitrator",
                            ]
                            role_names = [
                                "Abduction",
                                "Deduction",
                                "Induction",
                                "Devil's Advocate",
                                "Arbitrator",
                            ]
                            for role, role_name in zip(roles, role_names):
                                if role in rnd:
                                    st.markdown(f"- **{role_name}:** {rnd[role]}")

            st.divider()
