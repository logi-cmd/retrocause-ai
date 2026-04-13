from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult
from retrocause.app.helpers import _get_evidences


def render_sidebar_evidence(result: AnalysisResult) -> None:
    with st.sidebar:
        st.divider()
        st.header("📚 Evidence Library")
        st.caption(f"{result.total_evidence_count} evidence items")

        source_types = list(set(e.source_type.value for e in _get_evidences(result)))
        selected_type = st.selectbox(
            "Filter by source",
            options=["All"] + source_types,
            key="evidence_filter",
        )

        for ev in _get_evidences(result):
            if selected_type != "全部" and ev.source_type.value != selected_type:
                continue

            with st.expander(f"[{ev.source_type.value}] {ev.id}"):
                st.write(ev.content)
                if ev.source_url:
                    st.markdown(f"[Source]({ev.source_url})")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Prior reliability", f"{ev.prior_reliability:.2f}")
                with col_b:
                    st.metric("Posterior reliability", f"{ev.posterior_reliability:.2f}")
                if ev.linked_variables:
                    st.caption(f"Linked variables: {', '.join(ev.linked_variables)}")
