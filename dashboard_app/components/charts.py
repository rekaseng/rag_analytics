# components/charts_altair.py

import altair as alt
import streamlit as st
import pandas as pd


def render_keyword_coverage_chart(context_df, filtered_df):
    coverage_df = (
        context_df
        .groupby("ticket_id", as_index=False)
        .agg({
            "question_keyword_coverage_pct": "mean",
            "ground_truth_keyword_coverage_pct": "mean",
            "rag_answer_keyword_coverage_pct": "mean"
        })
    )

    coverage_cols = [
        "question_keyword_coverage_pct",
        "ground_truth_keyword_coverage_pct",
        "rag_answer_keyword_coverage_pct"
    ]

    coverage_df[coverage_cols] = (coverage_df[coverage_cols] * 100).round(2)

    coverage_df = coverage_df[
        coverage_df["ticket_id"].isin(filtered_df["ticket_id"])
    ]

    bar_df = coverage_df[coverage_cols].mean().reset_index()
    bar_df.columns = ["Metric", "Average Coverage (%)"]

    color_scale = alt.Scale(
        domain=coverage_cols,
        range=["#A7C7E7", "#B7E4C7", "#FFD6A5"]
    )

    st.subheader("📊 Contexts Keyword Coverage Analysis")

    chart_type = st.radio(
        "Chart Type",
        ["Bar Chart (Average)", "Line Chart (Trend)"],
        horizontal=True
    )

    if chart_type == "Bar Chart (Average)":
        chart = (
            alt.Chart(bar_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Metric:N", title=None),
                y=alt.Y("Average Coverage (%):Q", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Metric:N", scale=color_scale, legend=None),
                tooltip=["Metric:N", alt.Tooltip("Average Coverage (%):Q", format=".2f")]
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

    else:
        line_df = coverage_df.sort_values("ticket_id")
        st.line_chart(
            line_df.set_index("ticket_id")[coverage_cols]
        )

    st.caption("""
    **How to read this chart**
    - Question Coverage → Did retrieved context cover the user's intent?
    - Ground Truth Coverage → Did context support the correct answer?
    - Answer Coverage → Did the final answer use what was retrieved?
    """)

def render_context_answer_scatter(context_df):
    scatter_df = context_df.copy()
    scatter_df["rag_answer_keyword_coverage_pct"] *= 100
    scatter_df["is_context_useful"] = scatter_df["is_context_useful"].astype(str)

    st.subheader("🔬 Context Quality vs Answer Coverage")

    chart = (
        alt.Chart(scatter_df)
        .mark_circle(size=120, opacity=0.7)
        .encode(
            x=alt.X("context_token_count:Q", title="Context Token Count"),
            y=alt.Y(
                "rag_answer_keyword_coverage_pct:Q",
                title="Answer Keyword Coverage (%)",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color(
                "is_context_useful:N",
                scale=alt.Scale(domain=["True", "False"],
                                range=["#74C69D", "#F28482"])
            ),
            tooltip=[
                "ticket_id:N",
                "context_id:N",
                "context_token_count:Q",
                alt.Tooltip("rag_answer_keyword_coverage_pct:Q", format=".2f"),
                "is_context_useful:N"
            ]
        )
        .properties(height=380)
    )

    st.altair_chart(chart, use_container_width=True)

    st.caption("""
    - X-axis → Context length (tokens)
    - Y-axis → How much the answer used this context
    - Color → Whether the context was marked useful
    """)


def render_ground_truth_quality(context_df):
    gt_df = context_df.copy()
    gt_df["is_context_useful"] = gt_df["is_context_useful"].astype(str)

    if gt_df["ground_truth_keyword_coverage_pct"].max() <= 1:
        gt_df["ground_truth_keyword_coverage_pct"] *= 100

    # Box plot
    box = (
        alt.Chart(gt_df)
        .mark_boxplot(extent="min-max", size=60, opacity=0.6)
        .encode(
            x="is_context_useful:N",
            y=alt.Y(
                "ground_truth_keyword_coverage_pct:Q",
                scale=alt.Scale(domain=[0, 100]),
                title="Ground Truth Coverage (%)"
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

    # Jittered points
    points = (
        alt.Chart(gt_df)
        .mark_circle(size=120, opacity=0.7)
        .encode(
            x="is_context_useful:N",
            y="ground_truth_keyword_coverage_pct:Q",
            tooltip=[
                "ticket_id:N",
                "context_id:N",
                alt.Tooltip(
                    "ground_truth_keyword_coverage_pct:Q",
                    format=".2f",
                    title="GT Coverage (%)"
                )
            ],
            color="is_context_useful:N"
        )
    )

    # Threshold lines
    thresholds = (
        alt.Chart(pd.DataFrame({"y": [40, 70]}))
        .mark_rule(strokeDash=[4, 4], color="#999")
        .encode(y="y:Q")
    )

    final_chart = (box + points + thresholds).properties(height=360)

    st.subheader("🔬 Context Quality vs Ground Truth Coverage")
    st.altair_chart(final_chart, use_container_width=True)

    # Interpretation
    median_gt = gt_df["ground_truth_keyword_coverage_pct"].median()

    if median_gt < 40:
        st.caption(
            "🔴 **Ground-truth coverage is low across contexts.** "
            "Retrieved contexts do not sufficiently support the correct answer."
        )
    elif median_gt < 70:
        st.caption(
            "🟠 **Ground-truth coverage is moderate but inconsistent.** "
            "Retrieval partially works; consider improving source quality or ranking."
        )
    else:
        st.caption(
            "🟢 **Contexts strongly support ground truth.** "
            "Retrieval quality is solid; focus optimization on generation."
        )


def render_question_coverage(context_df):
    qc_df = context_df.copy()
    qc_df["is_context_useful"] = qc_df["is_context_useful"].astype(str)

    if qc_df["question_keyword_coverage_pct"].max() <= 1:
        qc_df["question_keyword_coverage_pct"] *= 100

    hist = (
        alt.Chart(qc_df)
        .mark_bar(opacity=0.65)
        .encode(
            x=alt.X(
                "question_keyword_coverage_pct:Q",
                bin=alt.Bin(step=10),
                scale=alt.Scale(domain=[0, 100]),
                title="Question Keyword Coverage (%)"
            ),
            y=alt.Y("count():Q", title="Number of Contexts"),
            color=alt.Color(
                "is_context_useful:N",
                scale=alt.Scale(
                    domain=["True", "False"],
                    range=["#74C69D", "#F28482"]
                ),
                title="Context Useful"
            ),
            tooltip=["count():Q", "is_context_useful:N"]
        )
        .properties(height=320)
    )

    st.subheader("🔍 Context Quality vs Question Coverage")
    st.altair_chart(hist, use_container_width=True)

    useful = qc_df[qc_df["is_context_useful"] == "True"]
    not_useful = qc_df[qc_df["is_context_useful"] == "False"]

    useful_median = useful["question_keyword_coverage_pct"].median() if not useful.empty else 0
    not_useful_median = not_useful["question_keyword_coverage_pct"].median() if not not_useful.empty else 0

    if useful_median < 40:
        st.caption(
            "🔴 **Question keyword coverage is weak across contexts.** "
            "Retrieval is not sufficiently covering the user’s intent."
        )
    elif useful_median > not_useful_median + 10:
        st.caption(
            "🟢 **Useful contexts clearly cover the question better.** "
            "Recall quality is strong; focus optimization downstream."
        )
    elif abs(useful_median - not_useful_median) < 5:
        st.caption(
            "🟠 **Question coverage does not strongly differentiate useful vs non-useful contexts.** "
            "Retrieval may be noisy or overly broad."
        )
    else:
        st.caption(
            "🟡 **Question coverage is moderate but inconsistent.** "
            "Consider improving query expansion or keyword weighting."
        )

