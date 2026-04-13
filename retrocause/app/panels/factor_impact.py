from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult, FactorIntervention
from retrocause.counterfactual import compute_factor_impact, compute_sensitivity_profile
from retrocause.app.helpers import _status_badge


def render_factor_impact_panel(result: AnalysisResult) -> None:
    st.header("🎛️ Factor Impact Analysis")
    st.caption("Adjust a factor's support to see how it affects each hypothesis path probability")

    if not result.variables or not result.hypotheses:
        st.info("No variables or hypotheses available for analysis.")
        return

    variable_map = {variable.name: variable for variable in result.variables}
    variable_names = list(variable_map.keys())
    selected_var = st.selectbox("Select a factor", options=variable_names, key="factor_variable")
    selected = variable_map[selected_var]
    panel_left, panel_right = st.columns([3, 2])

    with panel_left:
        intervention_mode = st.radio(
            "Intervention mode",
            options=["probability", "remove"],
            format_func=lambda value: "Adjust support"
            if value == "probability"
            else "Remove factor",
            horizontal=True,
            key="factor_mode",
        )

        current_value = max(0.0, min(1.0, selected.posterior_support))
        new_value = 0.0
        if intervention_mode == "probability":
            new_value = st.slider(
                "New posterior support",
                min_value=0.0,
                max_value=1.0,
                value=float(current_value),
                step=0.05,
                key="factor_new_value",
            )

        if st.button("📊 Analyze Impact", use_container_width=True):
            intervention = FactorIntervention(
                variable_name=selected_var,
                original_value=current_value,
                new_value=new_value,
                intervention_type=intervention_mode,
            )
            st.session_state["factor_impact"] = compute_factor_impact(result, intervention)
            st.session_state["factor_sensitivity"] = compute_sensitivity_profile(
                result,
                selected_var,
                current_value,
                [0.0, 0.25, 0.5, 0.75, 1.0],
            )

    with panel_right:
        st.markdown("**Factor Summary**")
        st.metric("Current support", f"{current_value:.0%}")
        st.metric("Uncertainty contrib.", f"{selected.uncertainty_contribution:.2f}")
        if selected.evidence_ids:
            st.caption(f"Evidence count: {len(selected.evidence_ids)}")

    impact = st.session_state.get("factor_impact")
    if impact is None or impact.intervention.variable_name != selected_var:
        return

    st.subheader(
        f"{impact.intervention.variable_name}: {impact.intervention.original_value:.0%} → "
        f"{impact.intervention.new_value:.0%}"
    )
    st.caption(f"Affected variables: {', '.join(impact.affected_variables)}")

    ranked_deltas = sorted(
        impact.probability_deltas.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    if ranked_deltas:
        top_hypothesis_id, top_delta = ranked_deltas[0]
        hypothesis_map = {hypothesis.id: hypothesis for hypothesis in result.hypotheses}
        if top_hypothesis_id in hypothesis_map:
            top_hypothesis = hypothesis_map[top_hypothesis_id]
            share_text = (
                f"Changing {impact.intervention.variable_name} from "
                f"{impact.intervention.original_value:.0%} to {impact.intervention.new_value:.0%} "
                f"changes '{top_hypothesis.name}' by {top_delta:+.0%}."
            )
            st.info(share_text)
            st.code(share_text, language="text")

    for hypothesis in result.hypotheses:
        original_prob = impact.original_result_probs.get(hypothesis.id, hypothesis.path_probability)
        new_prob = impact.new_result_probs.get(hypothesis.id, original_prob)
        delta = impact.probability_deltas.get(hypothesis.id, 0.0)

        with st.container():
            st.markdown(f"**{hypothesis.name}**")
            col_orig, col_arrow, col_new = st.columns([5, 1, 5])
            with col_orig:
                st.write("Original path prob.")
                st.progress(float(original_prob), text=f"{original_prob:.0%}")
            with col_arrow:
                st.markdown(
                    "<div style='text-align:center; padding-top:2em; font-size:1.5em'>→</div>",
                    unsafe_allow_html=True,
                )
            with col_new:
                st.write("Adjusted path prob.")
                st.progress(float(new_prob), text=f"{new_prob:.0%}")

            delta_col, coverage_col, status_col = st.columns(3)
            with delta_col:
                st.metric("Change Δ", f"{delta:+.0%}")
            with coverage_col:
                st.metric("Coverage", f"{hypothesis.evidence_coverage:.0%}")
            with status_col:
                st.metric("Status", _status_badge(hypothesis.status))

            st.caption("―" * 40)

    sensitivity = st.session_state.get("factor_sensitivity")
    if sensitivity:
        st.subheader("📈 Sensitivity Profile")
        sensitivity_rows: list[dict[str, float | str]] = []
        for point in sensitivity:
            row: dict[str, float | str] = {"tested_value": point.tested_value}
            for hypothesis in result.hypotheses:
                row[hypothesis.name] = point.hypothesis_probs.get(hypothesis.id, 0.0)
            sensitivity_rows.append(row)
        st.line_chart(sensitivity_rows, x="tested_value")
        with st.expander("View raw sensitivity data"):
            st.dataframe(sensitivity_rows, use_container_width=True)
