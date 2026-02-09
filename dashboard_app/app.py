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
import requests
import time
from utils.constants import REQUIRED_RAGAS_COLS, REQUIRED_CONTEXT_COLS, BACKEND_URL, JOB_PENDING, JOB_RUNNING, JOB_COMPLETED, JOB_FAILED
from utils.formatting import styled_metric
from components.filters import ragas_metric_filters
from components.metrics import render_ragas_kpis, render_total_context_card
from components.charts import render_keyword_coverage_chart, render_context_answer_scatter, render_ground_truth_quality, render_question_coverage
from services.json_loader import load_json_safe
from services.job_service import submit_job, get_job_status, download_csv, normalize_job_status


def download_csv(job_id: str, output_type: str) -> pd.DataFrame:
    resp = requests.get(f"{BACKEND_URL}/{job_id}/download/{output_type}")
    resp.raise_for_status()
    return pd.read_csv(BytesIO(resp.content))

st.set_page_config(layout="wide", page_title="Dashboard")

feedback_table = 'vw_user_feedback_summary'
rag_log_table = 'rag_process_result_log'

# If tables are in a specific schema, set it here (e.g., 'public', 'ProjectLog')
DB_SCHEMA = 'public'  # Change this based on test_connection.py output

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    page = st.selectbox("Select Page", ["RAG WisE Dashboard", "RAGAS Dashboard", "Ragas Results Comparison"])
    
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

    # =========================================================
    # Session State Initialization (CRITICAL)
    # =========================================================
    if "job_done" not in st.session_state:
        st.session_state.job_done = False

    if "job_id" not in st.session_state:
        st.session_state.job_id = None

    if "ragas_df" not in st.session_state:
        st.session_state.ragas_df = None

    if "context_df" not in st.session_state:
        st.session_state.context_df = None

    if "evaluation_df" not in st.session_state:
        st.session_state.evaluation_df = None

    st.set_page_config(
        page_title="RAGAS BI Analytics",
        layout="wide"
    )

    # =========================================================
    # Sidebar – JSON Upload
    # =========================================================
    st.sidebar.header("📤 Data Upload")

    json_file = st.sidebar.file_uploader(
        "Upload RAG Evaluation JSON",
        type=["json"],
        help="Upload the input JSON for RAGAS evaluation"
    )

    if "job_id" not in st.session_state and json_file is None:
        st.info("⬅ Upload a JSON file and run evaluation to see results.")

    # =========================================================
    # Submit Job
    # =========================================================
    if st.sidebar.button("🚀 Run RAGAS Evaluation"):
        if json_file is None:
            st.sidebar.error("Please upload a JSON file first.")
            st.stop()

        with st.spinner("Submitting job to backend..."):
            st.session_state.job_id = submit_job(json_file)  # ✅ CALL it
            st.session_state.job_status = JOB_PENDING
            st.session_state.ragas_df = None
            st.session_state.context_df = None

        st.rerun()  # 🔥 trigger polling immediately

    # =========================================================
    # Remove this after testing
    # =========================================================  
    if "job_id" in st.session_state and st.session_state.job_id:
        st.sidebar.markdown("### 🧾 Backend Job ID")
        st.sidebar.code(st.session_state.job_id)

    # =========================================================
    # Poll Job Status
    # =========================================================

    if "job_id" not in st.session_state:
        st.info("⬅ Upload JSON and click **Run RAGAS Evaluation**")

    if st.session_state.job_id is None:
        st.info("⬅ Upload JSON and click **Run RAGAS Evaluation**")
        st.stop()

    job_id = st.session_state.job_id

    if not st.session_state.job_done:
        status_resp = requests.get(f"{BACKEND_URL}/{job_id}")
        status_resp.raise_for_status()
        job = status_resp.json()
        job_status = normalize_job_status(job.get("status"))
    else:
        job_status = JOB_COMPLETED

    st.sidebar.info(f"🕒 Job status: {job_status}")

    # =========================================================
    # Job Failed
    # =========================================================
    if job_status == JOB_FAILED:
        st.error("❌ Backend job failed")
        st.stop()

    # =========================================================
    # Job Running → Auto Refresh
    # =========================================================
    if job_status in (JOB_PENDING, JOB_RUNNING):
        st.info("⏳ RAGAS evaluation running… dashboard will appear automatically")
        time.sleep(2)
        st.rerun()

    # =========================================================
    # Download Results (ONCE)
    # =========================================================
    if (
        job_status == JOB_COMPLETED
        and not st.session_state.job_done
    ):
        st.session_state.ragas_df = download_csv(job_id, "ragas_bi")
        st.session_state.context_df = download_csv(job_id, "context_bi")
        st.session_state.evaluation_df = download_csv(job_id, "evaluation_bi")
        st.session_state.job_done = True
        st.rerun()

    ragas_df = st.session_state.ragas_df
    context_df = st.session_state.context_df
    evaluation_df = st.session_state.evaluation_df

    if ragas_df is None or context_df is None or evaluation_df is None:
        st.info("⏳ Waiting for evaluation results…")
    else:
        # DASHBOARD STARTS HERE
        st.sidebar.success("✅ Evaluation completed")

        st.title("RAGAS BI Analytics")
        st.subheader("1. RAGAS Analysis Dashboard")

        # ---------- Filters ----------
        filtered_df, selected_metric = ragas_metric_filters(ragas_df)

        # ---------- KPI Cards ----------
        render_ragas_kpis(filtered_df)

        # ---------- Total Contexts ----------
        render_total_context_card(len(context_df))

        st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)

        # ---------- Ticket → Context Drilldown ----------
        with st.expander("🔍 View Raw ragas_bi Data (Select a Ticket)"):
            st.caption("Tick **one** ticket to view its related contexts")

            if filtered_df.empty:
                st.info("No tickets match the current filters.")
            else:
                selectable_df = filtered_df.copy()

                if "select" not in selectable_df.columns:
                    selectable_df.insert(0, "select", False)

                edited_df = st.data_editor(
                    selectable_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "select": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select ONE ticket"
                        )
                    },
                    disabled=[c for c in selectable_df.columns if c != "select"],
                    height=300
                )

                selected_rows = edited_df[edited_df["select"]]

                if len(selected_rows) == 1:
                    ticket_id = selected_rows.iloc[0]["ticket_id"]

                    st.subheader(f"📄 Contexts for Ticket: {ticket_id}")

                    related_contexts = context_df[
                        context_df["ticket_id"] == ticket_id
                    ]

                    st.dataframe(
                        related_contexts,
                        use_container_width=True,
                        height=400
                    )

        # =========================================================
        # Ragas Results Table
        # =========================================================
        try:
            evaluate_df = evaluation_df
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
            if col in evaluate_df.columns:
                evaluate_df[col] = (
                    evaluate_df[col]
                    .astype(str)
                    .str.replace("%", "", regex=False)   # remove %
                )
                evaluate_df[col] = pd.to_numeric(evaluate_df[col], errors="coerce")

                # If values look like decimals (≤1), scale them
                if evaluate_df[col].max(skipna=True) <= 1:
                    evaluate_df[col] = evaluate_df[col] * 100

                evaluate_df[col] = evaluate_df[col].round(0)


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

        missing_cols = set(columns_to_show) - set(evaluate_df.columns)
        if missing_cols:
            st.error(f"Missing columns in CSV: {missing_cols}")
            st.stop()

        df_display = evaluate_df[columns_to_show].copy()

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

        # =========================================================
        # Context Analysis
        # =========================================================
        st.subheader("2. Context Analysis Dashboard")

        render_keyword_coverage_chart(context_df, filtered_df)
        render_context_answer_scatter(context_df)

        col1, col2 = st.columns(2)

        with col1:
            render_ground_truth_quality(context_df)

        with col2:
            render_question_coverage(context_df)


elif page == "Ragas Results Comparison":
    st.title("RAGAS Results Comparison Dashboard")
    st.info("RAGAS Results Comparison Dashboard - Coming Soon")
