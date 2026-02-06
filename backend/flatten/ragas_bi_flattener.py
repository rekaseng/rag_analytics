from typing import List, Dict
from models.ragas_models import NormalizedRagasResult


def build_ragas_bi(
    normalized: NormalizedRagasResult,
    resolution: Dict[str, Dict],
    contexts: List[Dict],
    keyword_info: Dict[str, Dict]
) -> List[Dict]:
    """
    Build question-level RAGAS BI output with keyword explainability.
    """

    bi_rows = []

    for record in normalized.records:
        ticket_id = record.ticket_id
        keywords = keyword_info.get(ticket_id, {})

        gt_keywords = set(keywords.get("ground_truth_keywords", []))
        ans_keywords = set(keywords.get("rag_answer_keywords", []))
        ctx_keywords = set(keywords.get("context_keywords", []))

        row = {
            "ticket_id": ticket_id,
            "question": record.question,
            "rag_answer": record.rag_answer,
            "ground_truth": record.ground_truth,

            # RAGAS metrics (per-question)
            "context_entity_recall": record.metrics.context_entity_recall,
            "context_precision": record.metrics.context_precision,
            "context_recall": record.metrics.context_recall,
            "answer_correctness": record.metrics.answer_correctness,
            "answer_similarity": record.metrics.answer_similarity,
            "answer_relevancy": record.metrics.answer_relevancy,
            "faithfulness": record.metrics.faithfulness,

            # Resolution
            **resolution.get(ticket_id, {}),

            # Context stats
            "context_count": len(record.contexts),
            "useful_context_count": sum(
                1 for c in contexts
                if c["ticket_id"] == ticket_id and c["is_context_useful"]
            ),
            "dropped_context_count": sum(
                1 for c in contexts
                if c["ticket_id"] == ticket_id and c["drop_recommendation"]
            ),

            # 🔑 Keyword explainability columns
            "question_keywords": keywords.get("question_keywords", []),
            "ground_truth_keywords": keywords.get("ground_truth_keywords", []),
            "rag_answer_keywords": keywords.get("rag_answer_keywords", []),

            # 🔍 Gap analysis
            "missing_answer_keywords": list(gt_keywords - ans_keywords),
            "missing_context_keywords": list(gt_keywords - ctx_keywords),
        }

        bi_rows.append(row)

    return bi_rows
