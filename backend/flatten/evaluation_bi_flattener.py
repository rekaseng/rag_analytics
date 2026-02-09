from typing import List, Dict
import math


def build_evaluation_bi(raw_ragas: List[Dict]) -> List[Dict]:
    """
    Builds a flat Evaluation BI table from raw RAGAS JSON.
    One row per question, with expanded context columns.
    """

    # ---------- PASS 1: find max context count ----------
    max_context_count = 0

    for record in raw_ragas:
        for item in record.get("detailed_results", []):
            contexts = item.get("contexts", [])
            if isinstance(contexts, list):
                max_context_count = max(max_context_count, len(contexts))

    rows = []

    # ---------- PASS 2: build rows ----------
    for record in raw_ragas:
        for item in record.get("detailed_results", []):
            contexts = item.get("contexts", [])

            row = {
                "question": item.get("question"),
                "rag_answer": item.get("rag_answer") or item.get("rag answer"),
                "ground_truth": item.get("ground_truth"),

                "answer_relevancy": item.get("answer_relevancy"),
                "faithfulness": item.get("faithfulness"),
                "context_recall": item.get("context_recall"),
                "context_precision": item.get("context_precision"),
                "answer_correctness": item.get("answer_correctness"),
                "answer_similarity": item.get("answer_similarity"),
                "context_entity_recall": item.get("context_entity_recall"),

                "context_count": len(contexts),
            }

            # Expand contexts into columns
            for i in range(max_context_count):
                col_name = f"context_{i+1}"
                row[col_name] = contexts[i] if i < len(contexts) else None

            rows.append(row)

    return rows
