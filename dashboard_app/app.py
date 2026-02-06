import streamlit as st
import pandas as pd
import json
import importlib
import db_utils
importlib.reload(db_utils)  # Force reload to get latest changes
import config
from datetime import datetime, timedelta
import pytz
import ast
import plotly.express as px
from matplotlib import colors
import altair as alt
from io import BytesIO

st.set_page_config(layout="wide", page_title="Dashboard")

feedback_table = 'vw_user_feedback_summary'
rag_log_table = 'rag_process_result_log'

# If tables are in a specific schema, set it here (e.g., 'public', 'ProjectLog')
DB_SCHEMA = 'public'  # Change this based on test_connection.py output

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    page = st.selectbox("Select Page", ["RAG WisE Dashboard", "RAGAS Dashboard", "Ragas Evaluation Report"])
    
    st.divider()

    if page == "RAG WisE Dashboard":
        st.subheader("Quick Links")
        st.markdown("[Filters](#filters)")
        st.markdown("[Feedback Distribution](#feedback-distribution)")
        st.markdown("[Messages Over Time](#messages-over-time)")
        st.markdown("[User Feedback Summary](#user-feedback-summary)")
    elif page == "Ragas Evaluation Report":
        st.subheader("Quick Links")
        st.markdown("[RAGAS Detailed Results](#ragas-detailed-results)")
        st.markdown("[1. RAG 评估报告分析汇总 / RAG評価レポート分析サマリー](#ragas-analysis-results)")
        st.markdown("[2. 問題の根本原因分析](#ragas-root-cause-analysis)")

if page == "RAG WisE Dashboard":
    with st.spinner("Loading data..."):
        feedback_df = db_utils.fetch_logs(feedback_table, schema=DB_SCHEMA)
    
    if feedback_df is None:
        st.error(f"❌ Cannot load table: {DB_SCHEMA}.{feedback_table}")
        st.warning("Check terminal output for detailed error message")
        
        # Show connection info
        import os
        db_url = os.getenv('POSTGRES_URL_RAG')
        if db_url:
            st.info(f"Connection string found: {db_url[:30]}...")
        else:
            st.error("❌ POSTGRES_URL_RAG not found in environment!")
        st.stop()
    
    if feedback_df.empty:
        st.warning(f"⚠️ Table {DB_SCHEMA}.{feedback_table} is empty")
        st.stop()

    # Transform user_feedback column
    feedback_df["user_feedback"] = feedback_df["user_feedback"].map({1: "Like", 0: "Dislike"}).fillna(" ")

    st.title("RAG WisE Dashboard")

    # Main layout: content on left, filters on right
    main_col, filter_col = st.columns([3, 1])

    with filter_col:
        st.subheader("Filters")
        
        if st.button("Reset Filters"):
            st.rerun()
        
        # Date range setup
        user_time_clean = feedback_df["user_time"].dropna()
        min_date = user_time_clean.dt.date.min()
        max_date = user_time_clean.dt.date.max()
        default_start = max_date - timedelta(days=6)  # Last 7 days including today
        
        date_range_filter = st.date_input(
            "Date Range",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Apply date filter
        filtered_df = feedback_df[
            (feedback_df["user_time"].dt.date >= date_range_filter[0]) & 
            (feedback_df["user_time"].dt.date <= date_range_filter[1])
        ]
        
        system_code_filter = st.multiselect("System Code", filtered_df["system_code"].unique(), default=filtered_df["system_code"].unique())
        filtered_df = filtered_df[filtered_df["system_code"].isin(system_code_filter)]
        
        user_feedback_filter = st.multiselect("User Feedback", filtered_df["user_feedback"].unique(), default=filtered_df["user_feedback"].unique())
        filtered_df = filtered_df[filtered_df["user_feedback"].isin(user_feedback_filter)]
        
        user_filter = st.multiselect("User", filtered_df["user_name"].unique(), default=filtered_df["user_name"].unique())
        filtered_df = filtered_df[filtered_df["user_name"].isin(user_filter)]
        
        issue_key_filter = st.multiselect("Issue Key", filtered_df["issue_key"].unique(), default=filtered_df["issue_key"].unique())
        filtered_df = filtered_df[filtered_df["issue_key"].isin(issue_key_filter)]
        

    with main_col:
        # Metrics
        total_users = filtered_df["user_name"].nunique()
        total_threads = filtered_df["thread_id"].nunique()
        total_messages = filtered_df["message_id"].nunique()
        total_feedback = filtered_df[filtered_df["user_feedback"] != " "]["user_feedback"].count()
        feedback_rate = f"{(total_feedback / total_messages * 100):.1f}%" if total_messages > 0 else "0%"
        
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("👥 Total Users", total_users)
            col2.metric("🧵 Total Threads", total_threads)
            col3.metric("💬 Total Messages", total_messages)
            col4.metric("👍 Total Feedback", total_feedback)
            col5.metric("📊 Feedback Rate", feedback_rate)
        
        # Charts
        chart_col1, chart_col2 = st.columns([1, 1])
        
        with chart_col1:
            with st.container(border=True):
                st.subheader("Feedback Distribution")
                feedback_counts = filtered_df["user_feedback"].value_counts().reset_index()
                feedback_counts.columns = ["Feedback", "Count"]
                feedback_counts["Feedback"] = feedback_counts["Feedback"].replace({" ": "No Feedback"})
                
                fig = px.pie(feedback_counts, values="Count", names="Feedback", 
                             color="Feedback",
                             color_discrete_map={"Like": "#00cc66", "Dislike": "#ff4444", "No Feedback": "#cccccc"},
                             hole=0.4)
                fig.update_layout(height=400, margin=dict(t=30, b=30, l=30, r=30))
                st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            with st.container(border=True):
                st.subheader("Messages Over Time")
                time_series = filtered_df.groupby(filtered_df["user_time"].dt.date).size().reset_index()
                time_series.columns = ["Date", "Messages"]
                
                fig2 = px.line(time_series, x="Date", y="Messages", markers=True)
                fig2.update_layout(height=400, margin=dict(t=30, b=30, l=30, r=30))
                st.plotly_chart(fig2, use_container_width=True)
        
        # User Feedback Summary Table
        st.subheader("User Feedback Summary")
        table_cols = ["thread_id", "message_id", "system_code", "user_name", "user_time", 
                      "issue_key", "query", "ai_message", "user_feedback", "user_comment", "rag_trace_id"]
        display_df = filtered_df[table_cols].copy().sort_values("message_id", ascending=False)
        display_df["message_id"] = display_df["message_id"].astype('Int64')
        
        # Remove rag_trace_id from display but keep in dataframe
        display_cols = [col for col in table_cols if col != "rag_trace_id"]
        display_only_df = display_df[display_cols].copy()
        
        def highlight_dislike(row):
            return ['background-color: #ffcccc' if row['user_feedback'] == 'Dislike' else '' for _ in row]
        
        styled_df = display_only_df.style.apply(highlight_dislike, axis=1)
        
        event = st.dataframe(
            styled_df, 
            use_container_width=True, 
            height=400,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun"
        )
        
        # Show RAG process log for selected message
        if len(event.selection['rows']) > 0:
            selected_idx = event.selection['rows'][0]
            selected_rag_trace_id = display_df.iloc[selected_idx]['rag_trace_id']
            selected_row = display_df.iloc[selected_idx]
            
            detail_col, log_col = st.columns([1, 1])
            
            with detail_col:
                with st.container(height=600, border=True):
                    st.subheader("Selected Message Details")
                    st.markdown("**🧑 User Query:**")
                    st.info(selected_row['query'])
                    
                    st.markdown("**🤖 AI Answer:**")
                    st.success(selected_row['ai_message'])
                    
                    feedback_emoji = "👍" if selected_row['user_feedback'] == "Like" else "👎" if selected_row['user_feedback'] == "Dislike" else "➖"
                    st.markdown(f"**{feedback_emoji} User Feedback: {selected_row['user_feedback']}**")
                    if selected_row['user_feedback'] == "Dislike":
                        st.error(selected_row['user_comment'] if pd.notna(selected_row['user_comment']) else "No comment")
                    elif selected_row['user_feedback'] == "Like":
                        st.success(selected_row['user_comment'] if pd.notna(selected_row['user_comment']) else "No comment")
                    else:
                        st.write(selected_row['user_comment'] if pd.notna(selected_row['user_comment']) else "No comment")
            
            with log_col:
                with st.container(height=600, border=True):
                    st.subheader("RAG Process Log")
                    st.caption(f"Trace ID: {selected_rag_trace_id}")
                    
                    with st.spinner("Fetching RAG process logs..."):
                        rag_log_df = db_utils.fetch_logs(rag_log_table, schema=DB_SCHEMA)
                        
                        if rag_log_df is None:
                            st.error(f"Cannot load {rag_log_table}")
                            trace_log = pd.DataFrame()
                        else:
                            trace_log = rag_log_df[rag_log_df['trace_id'] == selected_rag_trace_id]
                    
                    if not trace_log.empty:
                        trace_log = trace_log.sort_values('timestamp', ascending=True)
                        
                        for _, row in trace_log.iterrows():
                            with st.expander(f"{row['Features']} | Duration: {row['Duration_s']}s"):
                                try:
                                    if isinstance(row['Method_Results'], str):
                                        result = json.loads(row['Method_Results'])
                                    else:
                                        result = row['Method_Results']
                                    st.json(result, expanded=True)
                                except json.JSONDecodeError:
                                    try:
                                        result = ast.literal_eval(row['Method_Results'])
                                        st.json(result, expanded=True)
                                    except:
                                        st.code(row['Method_Results'], language="text")
                    else:
                        st.info("No RAG process log found for this message.")

elif page == "RAGAS Dashboard":
    st.set_page_config(
        page_title="RAGAS BI Analytics OB2C 20260128 Overview",
        layout="wide"
    )

# --------------------------- # Load data # --------------------------- 
    st.sidebar.header("📤 Data Upload")

    ragas_file = st.sidebar.file_uploader(
        "Upload ragas_bi CSV",
        type=["csv"],
        help="Upload a ragas_bi CSV file"
    )

    context_file = st.sidebar.file_uploader(
        "Upload context_bi CSV",
        type=["csv"],
        help="Upload a context_bi CSV file"
    )

    @st.cache_data
    def load_csv_safe(file_bytes, file_name, default_path, required_cols):
        try:
            if file_bytes is not None:
                df = pd.read_csv(BytesIO(file_bytes))
            else:
                df = pd.read_csv(default_path)

            missing = required_cols - set(df.columns)
            if missing:
                return None, f"❌ `{file_name}` is missing columns: {', '.join(missing)}"

            return df, None

        except Exception as e:
            return None, f"❌ Failed to load `{file_name}`: {str(e)}"
    
    REQUIRED_RAGAS_COLS = {
        # Identifiers
        "ticket_id",

        # Core text fields (used in drill-down & analysis)
        "question",
        "rag_answer",
        "ground_truth",

        # RAGAS retrieval metrics
        "context_entity_recall",
        "context_precision",
        "context_recall",

        # RAGAS answer quality metrics
        "answer_correctness",
        "answer_similarity",
        "answer_relevancy",
        "faithfulness",

        # Resolution & QA signals
        "resolution_category",
        "resolution_confidence",
        "needs_manual_review",

        # Context statistics
        "context_count",
        "useful_context_count",
        "dropped_context_count",

        # Keyword analysis (used in context dashboard)
        "question_keywords",
        "ground_truth_keywords",
        "rag_answer_keywords",
        "missing_answer_keywords",
        "missing_context_keywords",

        # Ranking / prioritization
        "rank",
        "rank_reason",
    }
    REQUIRED_CONTEXT_COLS = {
        # Identifiers
        "ticket_id",
        "context_id",

        # Raw context content
        "context_text",

        # Context size metrics
        "context_char_count",
        "context_token_count",

        # Keyword extraction
        "context_keywords",
        "question_keywords",
        "ground_truth_keywords",
        "rag_answer_keywords",

        # Keyword overlap analysis
        "overlapping_question_keywords",
        "overlapping_ground_truth_keywords",
        "overlapping_answer_keywords",

        # Coverage metrics (core analytics)
        "question_keyword_coverage_pct",
        "ground_truth_keyword_coverage_pct",
        "rag_answer_keyword_coverage_pct",

        # Missing keyword analysis
        "missing_question_keywords",
        "missing_ground_truth_keywords",

        # Entity & usefulness signals
        "entity_match",
        "is_context_useful",
        "usefulness_reason",
        "drop_recommendation",

        # Ranking / prioritization
        "rank",
        "rank_reason",
    }

    df, ragas_error = load_csv_safe(
        ragas_file.getvalue() if ragas_file else None,
        ragas_file.name if ragas_file else "default_ragas",
        "ob2c_20260128_ragas_bi.csv",
        REQUIRED_RAGAS_COLS
    )

    context_df, context_error = load_csv_safe(
        context_file.getvalue() if context_file else None,
        context_file.name if context_file else "default context_bi",
        "ob2c_20260128_context_bi.csv",
        REQUIRED_CONTEXT_COLS
    )

    if ragas_error:
        st.error(ragas_error)
        st.info("Please upload a valid **ragas_bi CSV** with the correct format.")
        st.stop()

    if context_error:
        st.error(context_error)
        st.info("Please upload a valid **context_bi CSV** with the correct format.")
        st.stop()

    st.sidebar.success(
        f"🧠 ragas_bi loaded: {ragas_file.name if ragas_file else 'Default dataset'}"
    )
    st.sidebar.success(
        f"🧩 context_bi loaded: {context_file.name if context_file else 'Default dataset'}"
    )

    # ---------------------------
    # Session State Initialization (CRITICAL)
    # ---------------------------
    if "metric_select" not in st.session_state:
        st.session_state.metric_select = "Answer Correctness"

    if "threshold_slider" not in st.session_state:
        st.session_state.threshold_slider = (0, 100)

    if "status_filter" not in st.session_state:
        st.session_state.status_filter = ["🔴 Critical", "🟠 Warning", "🟢 Good"]

    # ---------------------------
    # Helper functions
    # ---------------------------
    def score_badge(value):
        if value < 40:
            return "🔴 Critical"
        elif value < 70:
            return "🟠 Warning"
        else:
            return "🟢 Good"
        
    st.title("RAGAS BI Analytics")
    st.subheader("1. Ragas Analysis Dashboard OB2C 20260128")

    def styled_metric(label, value, is_percent=True):
        display_value = f"{value:.2f}%" if is_percent else f"{value:.2f}"
        badge = score_badge(value)

        st.markdown(
            f"""
            <div style="
                padding:10px;
                margin:12px;
                border-radius:14px;
                background-color:#f9f9f9;
                box-shadow:0 4px 10px rgba(0,0,0,0.08);
                text-align:center;
            ">
                <div style="font-size:14px;color:#777;">{label}</div>
                <div style="font-size:30px;font-weight:700;">{display_value}</div>
                <div style="font-size:14px;margin-top:6px;">{badge}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------------------
    # Filters
    # ---------------------------
    st.sidebar.header("🎯 Metric Filters")

    metric_map = {
        "Answer Correctness": "answer_correctness",
        "Answer Similarity": "answer_similarity",
        "Answer Relevancy": "answer_relevancy",
        "Faithfulness": "faithfulness",
        "Context Precision": "context_precision",
        "Context Recall": "context_recall",
        "Context Entity Recall": "context_entity_recall",
    }

    selected_metric_label = st.sidebar.selectbox(
        "Select Metric",
        list(metric_map.keys()),
        key="metric_select"
    )

    selected_metric = metric_map[selected_metric_label]

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
    # Reset callback (SAFE)
    # ---------------------------
    def reset_filters():
        st.session_state.metric_select = "Answer Correctness"
        st.session_state.threshold_slider = (0, 100)
        st.session_state.status_filter = ["🔴 Critical", "🟠 Warning", "🟢 Good"]

    st.sidebar.divider()
    st.sidebar.button("🔄 Reset to Default", on_click=reset_filters)

    # ---------------------------
    # Filtering logic
    # ---------------------------
    df["_metric_pct"] = df[selected_metric] * 100

    filtered_df = df[
        (df["_metric_pct"] >= threshold_range[0]) &
        (df["_metric_pct"] <= threshold_range[1])
    ]

    def status_from_value(v):
        if v < 40:
            return "🔴 Critical"
        elif v < 70:
            return "🟠 Warning"
        else:
            return "🟢 Good"

    filtered_df = filtered_df[
        filtered_df["_metric_pct"].apply(status_from_value).isin(status_filter)
    ]

    # ---------------------------
    # KPI calculations
    # ---------------------------
    avg_answer_correctness = filtered_df["answer_correctness"].mean() * 100
    avg_answer_relevancy = filtered_df["answer_relevancy"].mean() * 100
    avg_answer_similarity = filtered_df["answer_similarity"].mean() * 100
    avg_context_precision = filtered_df["context_precision"].mean() * 100
    avg_context_recall = filtered_df["context_recall"].mean() * 100
    avg_faithfulness = filtered_df["faithfulness"].mean() * 100
    avg_entity_recall = filtered_df["context_entity_recall"].mean() * 100

    # ---------------------------
    # Ragas Metrics Average Score
    # ---------------------------

    row1 = st.columns(4)
    row2 = st.columns(4)

    with row1[0]:
        styled_metric("Avg Answer Correctness", avg_answer_correctness)
    with row1[1]:
        styled_metric("Avg Answer Relevancy", avg_answer_relevancy)
    with row1[2]:
        styled_metric("Avg Faithfulness", avg_faithfulness)
    with row1[3]:
        styled_metric("Avg Similarity", avg_answer_similarity)

    with row2[0]:
        styled_metric("Avg Context Precision", avg_context_precision)
    with row2[1]:
        styled_metric("Avg Context Recall", avg_context_recall)
    with row2[2]:
        styled_metric("Avg Context Entity Recall", avg_entity_recall)
    # row2[3] intentionally left empty

    total_contexts = len(context_df)
    st.markdown(
    f"""
    <div style="
        width:240px;
        padding:16px;
        border-radius:14px;
        background-color:#ffffff;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
        text-align:center;
        margin-bottom:24px;
    ">
        <div style="font-size:14px;color:#888;margin-bottom:8px;">
            🧩 Total Contexts
        </div>
        <div style="font-size:32px;font-weight:700;color:#2f2f2f;">
            {total_contexts}
        </div>
    </div>
    """,
    unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)


    # ---------------------------
    # Raw data
    # ---------------------------
    with st.expander("🔍 View Raw ragas_bi Data (Select a Ticket)"):
        st.caption("Tick **one** ticket to view its related contexts")

        if filtered_df.empty:
            st.info("No tickets match the current filters.")
        else:
            selectable_df = filtered_df.copy()

            # Add checkbox column
            if "select" not in selectable_df.columns:
                selectable_df.insert(0, "select", False)

            edited_df = st.data_editor(
                selectable_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select ONE ticket to view related contexts"
                    )
                },
                disabled=[
                    col for col in selectable_df.columns if col != "select"
                ],
                height=300
            )

            selected_rows = edited_df[edited_df["select"]]

            if len(selected_rows) == 0:
                st.info("Select a ticket above to view its contexts.")
            elif len(selected_rows) > 1:
                st.warning("Please select **only ONE** ticket.")
            else:
                selected_ticket_id = selected_rows.iloc[0]["ticket_id"]

                st.divider()
                st.subheader(f"📄 Contexts for Ticket: {selected_ticket_id}")

                related_contexts = context_df[
                    context_df["ticket_id"] == selected_ticket_id
                ]

                st.dataframe(
                    related_contexts,
                    use_container_width=True,
                    height=400
                )

    st.subheader("2. Context Analysis Dashboard")

    coverage_df = (
    context_df
    .groupby("ticket_id", as_index=False)
    .agg({
        "question_keyword_coverage_pct": "mean",
        "ground_truth_keyword_coverage_pct": "mean",
        "rag_answer_keyword_coverage_pct": "mean"
    })
    )

    # Convert to percentage (0–100)
    coverage_cols = [
        "question_keyword_coverage_pct",
        "ground_truth_keyword_coverage_pct",
        "rag_answer_keyword_coverage_pct"
    ]

    coverage_df[coverage_cols] = (coverage_df[coverage_cols] * 100).round(2)
    bar_df = coverage_df[coverage_cols].mean().reset_index()
    bar_df.columns = ["Metric", "Average Coverage (%)"]

    color_scale = alt.Scale(
        domain=[
            "question_keyword_coverage_pct",
            "ground_truth_keyword_coverage_pct",
            "rag_answer_keyword_coverage_pct"
        ],
        range=[
            "#A7C7E7",  # soft blue
            "#B7E4C7",  # soft green
            "#FFD6A5"   # soft orange
        ]
    )


    coverage_df = coverage_df[
    coverage_df["ticket_id"].isin(filtered_df["ticket_id"])
    ]

    st.subheader("📊 Contexts Keyword Coverage Analysis")

    chart_type = st.radio(
        "Chart Type",
        ["Bar Chart (Average)", "Line Chart (Trend)"],
        horizontal=True
    )

    if chart_type == "Bar Chart (Average)":
        bar_chart = (
            alt.Chart(bar_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Metric:N", title=None),
                y=alt.Y(
                    "Average Coverage (%):Q",
                    scale=alt.Scale(domain=[0, 100]),
                    title="Coverage (%)"
                ),
                color=alt.Color("Metric:N", scale=color_scale, legend=None),
                tooltip=[
                    alt.Tooltip("Metric:N", title="Metric"),
                    alt.Tooltip("Average Coverage (%):Q", format=".2f")
            ]
        )
        .properties(height=320)
    )

        st.altair_chart(bar_chart, use_container_width=True)

    if chart_type == "Line Chart (Trend)":
        line_df = coverage_df.sort_values("ticket_id")

        st.line_chart(
            line_df.set_index("ticket_id")[[
                "question_keyword_coverage_pct",
                "ground_truth_keyword_coverage_pct",
                "rag_answer_keyword_coverage_pct"
            ]]
        )

    st.caption("""
    **How to read this chart**
    - Question Coverage → Did retrieved context cover the user's intent?
    - Ground Truth Coverage → Did context support the correct answer?
    - Answer Coverage → Did the final answer use what was retrieved?
    """)

    scatter_df = context_df.copy()
    scatter_df["rag_answer_keyword_coverage_pct"] = (
        scatter_df["rag_answer_keyword_coverage_pct"] * 100
    )
    # Ensure correct dtypes
    scatter_df["is_context_useful"] = scatter_df["is_context_useful"].astype(str)

    st.subheader("🔬 Context Quality vs Answer Coverage")

    scatter_chart = (
        alt.Chart(scatter_df)
        .mark_circle(size=120, opacity=0.7)
        .encode(
            x=alt.X(
                "context_token_count:Q",
                title="Context Token Count",
                scale=alt.Scale(zero=False)
            ),
            y=alt.Y(
                "rag_answer_keyword_coverage_pct:Q",
                title="Answer Keyword Coverage (%)",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color(
                "is_context_useful:N",
                title="Context Useful",
                scale=alt.Scale(
                    domain=["True", "False"],
                    range=["#74C69D", "#F28482"]  # soft green / soft red
                )
            ),
            tooltip=[
                alt.Tooltip("context_id:N", title="Context ID"),
                alt.Tooltip("ticket_id:N", title="Ticket ID"),
                alt.Tooltip("context_token_count:Q", title="Token Count"),
                alt.Tooltip("rag_answer_keyword_coverage_pct:Q", title="Coverage (%)", format=".2f"),
                alt.Tooltip("is_context_useful:N", title="Useful")
            ]
        )
        .properties(height=380)
    )

    st.altair_chart(scatter_chart, use_container_width=True)

    st.caption("""
    **How to read this scatter plot**
    - X-axis → Context length (tokens)
    - Y-axis → How much the answer used this context
    - Color → Whether the context was marked useful

    Ideal contexts appear as **large green circles in the upper-right**.
    """)

    # Use ONLY the selected ticket's contexts
    gt_df = context_df.copy()

    # Ensure correct types
    gt_df["is_context_useful"] = gt_df["is_context_useful"].astype(str)

    # Scale to percentage if still 0–1
    if gt_df["ground_truth_keyword_coverage_pct"].max() <= 1:
        gt_df["ground_truth_keyword_coverage_pct"] *= 100

    # -----------------------
    # Box plot
    # -----------------------
    box = (
        alt.Chart(gt_df)
        .mark_boxplot(
            extent="min-max",
            size=60,
            opacity=0.6
        )
        .encode(
            x=alt.X(
                "is_context_useful:N",
                title="Context Useful",
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "ground_truth_keyword_coverage_pct:Q",
                title="Ground Truth Coverage (%)",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color(
                "is_context_useful:N",
                scale=alt.Scale(
                    domain=["True", "False"],
                    range=["#74C69D", "#F28482"]
                ),
                legend=None
            )
        )
    )

    # -----------------------
    # Jittered points
    # -----------------------
    points = (
        alt.Chart(gt_df)
        .mark_circle(
            size=120,
            opacity=0.7,
            stroke="white",
            strokeWidth=0.8
        )
        .encode(
            x=alt.X("is_context_useful:N", title=None),
            y=alt.Y("ground_truth_keyword_coverage_pct:Q"),
            color=alt.Color(
                "is_context_useful:N",
                scale=alt.Scale(
                    domain=["True", "False"],
                    range=["#74C69D", "#F28482"]
                ),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("ticket_id:N", title="Ticket"),
                alt.Tooltip("context_id:N", title="Context"),
                alt.Tooltip(
                    "ground_truth_keyword_coverage_pct:Q",
                    title="GT Coverage (%)",
                    format=".2f"
                )
            ]
        )
    )

    # -----------------------
    # Threshold lines
    # -----------------------
    thresholds = (
        alt.Chart(pd.DataFrame({"y": [40, 70]}))
        .mark_rule(strokeDash=[4, 4], color="#999")
        .encode(y="y:Q")
    )

    qc_df = context_df.copy()

    # Ensure correct types
    qc_df["is_context_useful"] = qc_df["is_context_useful"].astype(str)

    # Scale to percentage if still 0–1
    if qc_df["question_keyword_coverage_pct"].max() <= 1:
        qc_df["question_keyword_coverage_pct"] *= 100

    hist = (
        alt.Chart(qc_df)
        .mark_bar(opacity=0.65)
        .encode(
            x=alt.X(
                "question_keyword_coverage_pct:Q",
                bin=alt.Bin(step=10),
                title="Question Keyword Coverage (%)",
                scale=alt.Scale(domain=[0, 100])
            ),
            y=alt.Y(
                "count():Q",
                title="Number of Contexts"
            ),
            color=alt.Color(
                "is_context_useful:N",
                title="Context Useful",
                scale=alt.Scale(
                    domain=["True", "False"],
                    range=["#74C69D", "#F28482"]  # soft green / soft red
                )
            ),
            tooltip=[
                alt.Tooltip("count():Q", title="Context Count"),
                alt.Tooltip("is_context_useful:N", title="Useful")
            ]
        )
        .properties(height=320)
    )

    col_gt, col_qc = st.columns(2)

    with col_gt:
        st.markdown(
            "<h4 style='margin-bottom:3px;'>🔬 Context Quality vs Ground Truth Coverage</h4>",
            unsafe_allow_html=True
        )

        final_chart = (box + points + thresholds).properties(height=360)
        st.altair_chart(final_chart, use_container_width=True)

        median_gt = gt_df["ground_truth_keyword_coverage_pct"].median()

        if median_gt < 40:
            interpretation = (
                "🔴 **Ground-truth coverage is low across contexts.** "
                "Retrieved contexts do not sufficiently support the correct answer."
            )
        elif median_gt < 70:
            interpretation = (
                "🟠 **Ground-truth coverage is moderate but inconsistent.** "
                "Retrieval partially works; consider improving source quality or ranking."
            )
        else:
            interpretation = (
                "🟢 **Contexts strongly support ground truth.** "
                "Retrieval quality is solid; focus optimization on generation."
            )

        st.caption(interpretation)

    with col_qc:
        st.markdown(
            "<h4 style='margin-bottom:40px;'>🔍 Context Quality vs Question Coverage</h4>",
            unsafe_allow_html=True
        )

        st.altair_chart(hist, use_container_width=True)

        useful = qc_df[qc_df["is_context_useful"] == "True"]
        not_useful = qc_df[qc_df["is_context_useful"] == "False"]

        useful_median = useful["question_keyword_coverage_pct"].median() if not useful.empty else 0
        not_useful_median = not_useful["question_keyword_coverage_pct"].median() if not not_useful.empty else 0

        if useful_median < 40:
            interpretation = (
                "🔴 **Question keyword coverage is weak across contexts.** "
                "Retrieval is not sufficiently covering the user’s intent."
            )
        elif useful_median > not_useful_median + 10:
            interpretation = (
                "🟢 **Useful contexts clearly cover the question better.** "
                "Recall quality is strong; focus optimization downstream."
            )
        elif abs(useful_median - not_useful_median) < 5:
            interpretation = (
                "🟠 **Question coverage does not strongly differentiate useful vs non-useful contexts.** "
                "Retrieval may be noisy or overly broad."
            )
        else:
            interpretation = (
                "🟡 **Question coverage is moderate but inconsistent.** "
                "Consider improving query expansion or keyword weighting."
            )

        st.caption(interpretation)

elif page == "Ragas Evaluation Report":
    st.title("Ragas Evaluation Report")

    # -----------------------------
    # CSV Loader
    # -----------------------------
    @st.cache_data
    def load_ragas_csv(path: str):
        return pd.read_csv(path)

    csv_path = "ragas_results.csv"  # <-- change to your actual CSV filename


    try:
        df = load_ragas_csv(csv_path)
    except Exception as e:
        st.error(f"Failed to load CSV: {e}")
        st.stop()

    st.subheader("RAGAS Detailed Results")

    # -----------------------------
    # Normalize percentage columns (handle "81%", 0.81, 81)
    # -----------------------------
    percentage_columns = [
        "answer_relevancy",
        "faithfulness",
        "context_recall",
        "context_precision",
        "answer_correctness",
        "answer_similarity",
        "context_entity_recall",
    ]

    for col in percentage_columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)   # remove %
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

            # If values look like decimals (≤1), scale them
            if df[col].max(skipna=True) <= 1:
                df[col] = df[col] * 100

            df[col] = df[col].round(0)


    # -----------------------------
    # Columns to display
    # -----------------------------
    columns_to_show = [
        "question",
        "rag_answer",
        "answer_relevancy",
        "faithfulness",
        "context_recall",
        "context_precision",
        "answer_correctness",
        "answer_similarity",
        "context_entity_recall",
    ]

    missing_cols = set(columns_to_show) - set(df.columns)
    if missing_cols:
        st.error(f"Missing columns in CSV: {missing_cols}")
        st.stop()

    df_display = df[columns_to_show].copy()

    # -----------------------------
    # Conditional formatting
    # -----------------------------
    gradient_cmap = colors.LinearSegmentedColormap.from_list(
    "rag_gradient",
    [
        (0.00, "#F8696B"),  # red
        (0.40, "#FCFCFF"),  # neutral
        (0.70, "#FCFCFF"),  # neutral
        (1.00, "#63BE7B"),  # green
    ]
    )

    metric_cols = columns_to_show[2:]  # all score columns

    styled_df = (
    df_display
    .style
    .format({col: "{:.0f}%" for col in metric_cols})
    .background_gradient(
        cmap=gradient_cmap,
        subset=metric_cols,
        vmin=0,
        vmax=100
    )
    )

    # -----------------------------
    # Render table
    # -----------------------------
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=650
    )

    st.subheader("1. RAG 评估报告分析汇总 / RAG評価レポート分析サマリー")

    summary_df = pd.DataFrame({
        "Metric": [
            "Context Entity Recall",
            "Context Precision",
            "Answer Correctness",
            "Context Recall",
            "Answer Relevancy",
            "Faithfulness",
        ],
        "Score": [12.84, 45.09, 36.58, 47.16, 67.54, 85.27],
        "Status": ["🔴 Critical", "🟠 Warning", "🟠 Warning", "🟠 Warning", "🟡 Average", "🟢 Good"],
        "詳細分析": ["依然として非常に低く、重要なエンティティ（システム名、ID、重要項目など）がコンテキスト内で十分にカバーされていない点が、最大の課題となっています。",
                    "各指標は小幅に改善しており、コンテキスト取得の量と一致度は向上していますが、精度面には依然として課題があります。", 
                    "前回より改善しているものの、全体としてはまだ低水準であり、コンテキスト品質の影響を強く受けていることが分かります。", 
                    "各指標は小幅に改善しており、コンテキスト取得の量と一致度は向上していますが、精度面には依然として課題があります。", 
                    "前回と比べて明確な改善（＋9.44％）が見られ、回答内容は全体として質問の意図に対応できていることを示していますが、さらなる精度向上の余地は残されています。", 
                    "高いスコアを示しており、回答は提供されたコンテキストに基づいて生成されており、幻覚のリスクは低いと判断できます。"],
        "详细分析（中国语）": ["该指标依然处于较低水平，说明上下文中对关键实体（如系统名、编号、关键字段等）的覆盖不足，是当前最主要的瓶颈之一。",
                    "指标均有小幅提升，说明检索到的上下文数量和匹配度有所改善，但当前仍存在“检索到但不够精准”的问题。", 
                    "虽然比上一期有所提高，但整体仍偏低，反映出上下文质量不足会直接影响最终答案的准确性。", 
                    "指标均有小幅提升，说明检索到的上下文数量和匹配度有所改善，但当前仍存在“检索到但不够精准”的问题。", 
                    "相比上一期有明显提升（+9.44%），表明回答内容整体上能够回应问题意图，但仍有进一步精准化的空间。", 
                    "得分较高，且相较上一期略有提升，说明模型在引用检索到的上下文时保持较好的事实一致性，幻觉风险较低。"],
        "Previous": [11.78, 43.78, 34.55, 46.29, 58.10, 84.90],
    })

    st.dataframe(summary_df, use_container_width=True)

    st.subheader("2. 問題の根本原因分析")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
    **实体召回率问题（Context Entity Recall）**  
    当前实体召回率仅 **12.84% (Critical)**，关键实体（系统名、ID、规则编号）未被充分覆盖。
    """)

    with col2:
        st.markdown("""
    **问题根源（中文）**  
    当前检索策略偏向语义相似度，缺乏实体级约束与验证机制。
    """)
