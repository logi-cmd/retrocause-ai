from __future__ import annotations

import streamlit as st

from retrocause.models import AnalysisResult
from retrocause.app.helpers import _render_graph


def render_graph_panel(result: AnalysisResult) -> None:
    st.header("🕸️ Causal Graph (DAG)")
    st.caption(
        "Node size/opacity = posterior support | Edge width/color = conditional probability (green=high, red=low)"
    )

    selected = _render_graph(result)

    if selected:
        var_map = {v.name: v for v in result.variables}
        if selected in var_map:
            v = var_map[selected]
            with st.sidebar:
                st.divider()
                st.subheader(f"📌 {v.name}")
                st.write(v.description)
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.metric("后验支持", f"{v.posterior_support:.2f}")
                with col_s2:
                    st.metric("不确定性贡献", f"{v.uncertainty_contribution:.2f}")
                if v.evidence_ids:
                    st.caption(f"关联证据: {', '.join(v.evidence_ids)}")
