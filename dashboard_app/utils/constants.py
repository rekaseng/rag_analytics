# utils/constants.py

# ---------------------------
# Metric mapping (UI → column)
# ---------------------------
METRIC_MAP = {
    "Answer Correctness": "answer_correctness",
    "Answer Similarity": "answer_similarity",
    "Answer Relevancy": "answer_relevancy",
    "Faithfulness": "faithfulness",
    "Context Precision": "context_precision",
    "Context Recall": "context_recall",
    "Context Entity Recall": "context_entity_recall",
}

# ---------------------------
# Required columns
# ---------------------------
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