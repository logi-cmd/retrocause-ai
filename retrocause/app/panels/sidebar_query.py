from __future__ import annotations

import streamlit as st

from retrocause.app.demo_data import topic_aware_demo_result
from retrocause.models import AnalysisResult


def render_sidebar_query(result: AnalysisResult | None) -> AnalysisResult | None:
    with st.sidebar:
        st.header("Query Input")
        st.caption("OSS runs a keyless local/demo analysis path.")

        query = st.text_input("Causal query", value="Why did dinosaurs go extinct?")

        col1, col2 = st.columns(2)
        with col1:
            run_clicked = st.button("Run Analysis", use_container_width=True)
        with col2:
            demo_clicked = st.button("Load Demo", use_container_width=True)

        st.divider()
        st.subheader("Pipeline Progress")

        pipeline_steps = [
            "Semantic parsing",
            "Evidence collection",
            "Causal graph construction",
            "Hypothesis chain generation",
            "Evidence anchoring",
            "Counterfactual verification",
            "Debate refinement",
        ]

        if result is not None:
            for step in pipeline_steps:
                st.progress(1.0, text=f"done: {step}")
        else:
            for step in pipeline_steps:
                st.progress(0.0, text=f"pending: {step}")

        if run_clicked or demo_clicked:
            demo = topic_aware_demo_result(query)
            demo.is_demo = True
            return demo

    return result
