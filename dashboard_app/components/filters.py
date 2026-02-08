import streamlit as st
from utils.constants import METRIC_MAP


def ragas_metric_filters(df):
    st.sidebar.header("🎯 Metric Filters")

    # ---------------------------
    # Session defaults
    # ---------------------------
    if "metric_select" not in st.session_state:
        st.session_state.metric_select = "Answer Correctness"

    if "threshold_slider" not in st.session_state:
        st.session_state.threshold_slider = (0, 100)

    if "status_filter" not in st.session_state:
        st.session_state.status_filter = ["🔴 Critical", "🟠 Warning", "🟢 Good"]

    # ---------------------------
    # UI controls
    # ---------------------------
    selected_metric_label = st.sidebar.selectbox(
        "Select Metric",
        list(METRIC_MAP.keys()),
        key="metric_select"
    )

    selected_metric = METRIC_MAP[selected_metric_label]

    threshold_range = st.sidebar.slider(
        "Score Threshold (%)",
        min_value=0,
        max_value=100,
        key="threshold_slider"
    )

    status_filter = st.sidebar.multiselect(
        "Score Status",
        ["🔴 Critical", "🟠 Warning", "🟢 Good"],
        key="status_filter"
    )

    # ---------------------------
    # Filtering logic
    # ---------------------------
    def status_from_value(v):
        if v < 40:
            return "🔴 Critical"
        elif v < 70:
            return "🟠 Warning"
        else:
            return "🟢 Good"

    filtered_df = df.copy()
    filtered_df["_metric_pct"] = filtered_df[selected_metric] * 100

    filtered_df = filtered_df[
        (filtered_df["_metric_pct"] >= threshold_range[0]) &
        (filtered_df["_metric_pct"] <= threshold_range[1])
    ]

    filtered_df = filtered_df[
        filtered_df["_metric_pct"].apply(status_from_value).isin(status_filter)
    ]

    # ---------------------------
    # Reset
    # ---------------------------
    def reset_filters():
        st.session_state.metric_select = "Answer Correctness"
        st.session_state.threshold_slider = (0, 100)
        st.session_state.status_filter = ["🔴 Critical", "🟠 Warning", "🟢 Good"]
        st.rerun()

    st.sidebar.divider()
    st.sidebar.button("🔄 Reset to Default", on_click=reset_filters)

    return filtered_df, selected_metric
