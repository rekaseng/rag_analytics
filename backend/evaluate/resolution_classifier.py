from typing import Dict
from models.ragas_models import NormalizedRagasResult


def classify_resolution(
    normalized: NormalizedRagasResult
) -> Dict[str, Dict]:
    """
    Classify resolution root cause per question (ticket_id).
    """

    resolution_map: Dict[str, Dict] = {}

    for record in normalized.records:
        m = record.metrics
        category = "unknown"
        confidence = 0.5
        needs_manual_review = False

        # 🔴 Hallucination
        if m.faithfulness < 0.7 and m.context_precision < 0.5:
            category = "hallucination"
            confidence = 0.9

        # 🔵 Retrieval failure
        elif m.context_recall < 0.6 or m.context_entity_recall < 0.4:
            category = "retrieval_failure"
            confidence = 0.85

        # 🟡 Noise / token waste
        elif m.context_precision < 0.5:
            category = "noise_token_waste"
            confidence = 0.75

        # 🟢 Bad question / prompt
        elif m.context_recall > 0.8 and m.answer_correctness < 0.6:
            category = "bad_question_prompt"
            confidence = 0.7

        # Edge case
        else:
            needs_manual_review = True

        resolution_map[record.ticket_id] = {
            "resolution_category": category,
            "resolution_confidence": confidence,
            "needs_manual_review": needs_manual_review
        }

    return resolution_map
