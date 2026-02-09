import streamlit as st
from utils.formatting import styled_metric


def render_ragas_kpis(df):
    if df.empty:
        st.warning("No data available for KPI calculation.")
        return

    # ---------------------------
    # KPI calculations
    # ---------------------------
    avg_answer_correctness = df["answer_correctness"].mean() * 100
    avg_answer_relevancy = df["answer_relevancy"].mean() * 100
    avg_answer_similarity = df["answer_similarity"].mean() * 100
    avg_context_precision = df["context_precision"].mean() * 100
    avg_context_recall = df["context_recall"].mean() * 100
    avg_faithfulness = df["faithfulness"].mean() * 100
    avg_entity_recall = df["context_entity_recall"].mean() * 100

    # ---------------------------
    # Layout
    # ---------------------------
    row1 = st.columns(4)
    row2 = st.columns(4)

    with row1[0]:
        st.markdown(styled_metric("Avg Answer Correctness", avg_answer_correctness), unsafe_allow_html=True)
    with row1[1]:
        st.markdown(styled_metric("Avg Answer Relevancy", avg_answer_relevancy), unsafe_allow_html=True)
    with row1[2]:
        st.markdown(styled_metric("Avg Faithfulness", avg_answer_similarity), unsafe_allow_html=True)
    with row1[3]:
        st.markdown(styled_metric("Avg Similarity", avg_context_precision), unsafe_allow_html=True)

    # 👇 ADD SPACE BETWEEN ROWS
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    row2 = st.columns(4)
    with row2[0]:
        st.markdown(styled_metric("Avg Context Precision", avg_context_recall), unsafe_allow_html=True)
    with row2[1]:
        st.markdown(styled_metric("Avg Context Recall", avg_faithfulness), unsafe_allow_html=True)
    with row2[2]:
        st.markdown(styled_metric("Avg Context Entity Recall", avg_entity_recall), unsafe_allow_html=True)

        # row2[3] intentionally left empty
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)


def render_total_context_card(total_contexts): 
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