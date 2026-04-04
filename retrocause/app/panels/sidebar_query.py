from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult
from retrocause.app.demo_data import PROVIDERS, demo_result, run_real_analysis


def render_sidebar_query(result: AnalysisResult | None) -> AnalysisResult | None:
    with st.sidebar:
        st.header("🔬 Query Input")

        provider_key = st.selectbox(
            "LLM Provider",
            options=list(PROVIDERS.keys()),
            format_func=lambda k: PROVIDERS[k]["label"],
            index=0,
        )
        provider = PROVIDERS[provider_key]

        model_options = list(provider["models"].keys())
        selected_model = st.selectbox(
            "Model",
            options=model_options,
            format_func=lambda m: f"{m} — {provider['models'][m]}",
            index=0,
        )

        api_key = st.text_input(
            "API Key",
            type="password",
            help=f"Enter your {provider['label']} API key. Leave empty for demo mode.",
        )

        query = st.text_input("Causal query", value="恐龙为什么灭绝？")

        col1, col2 = st.columns(2)
        with col1:
            run_clicked = st.button("🚀 Run Analysis", use_container_width=True)
        with col2:
            demo_clicked = st.button("📋 Load Demo", use_container_width=True)

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
            for i, step in enumerate(pipeline_steps):
                st.progress(1.0, text=f"✅ {step}")
        else:
            for step in pipeline_steps:
                st.progress(0.0, text=f"⬜ {step}")

        if run_clicked:
            if api_key:
                with st.spinner(f"Running causal inference with {selected_model}..."):
                    try:
                        new_result = run_real_analysis(
                            query, api_key, selected_model, provider["base_url"]
                        )
                        if new_result:
                            st.success("✅ Analysis complete!")
                            return new_result
                        else:
                            st.warning(
                                "Pipeline produced no results. Check API key or try a different query."
                            )
                    except Exception as exc:
                        st.error(f"❌ Analysis failed: {exc}")
            else:
                st.info(
                    "No API key provided — using demo data. Add a key to enable real inference."
                )
                return demo_result()

        if demo_clicked:
            return demo_result()

    return result
