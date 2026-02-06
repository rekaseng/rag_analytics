import uuid
import math
from typing import Dict, List, Any
from models.ragas_models import (
    NormalizedRagasResult,
    RagasRecord,
    RagasMetrics,
    NormalizedContext
)

def _safe_float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    return value


def normalize(
    raw: List[Dict[str, Any]],
    ticket_id: str
) -> NormalizedRagasResult:
    """
    Normalize raw RAGAS JSON input into a deterministic internal structure.
    ticket_id is provided by the application layer.
    """

    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError("Invalid RAGAS input: root must be a non-empty list")

    root = raw[0]

    aggregated_scores = {
        k: _safe_float(v)
        for k, v in root.get("aggregated_scores", {}).items()
    }

    records: List[RagasRecord] = []

    for idx, item in enumerate(root.get("detailed_results", []), start=1):
        ticket_id = f"question_{idx}"

        question = item.get("question", "").strip()
        ground_truth = item.get("ground_truth", "").strip()

        rag_answer = (
                item.get("rag_answer")
                or item.get("rag answer")
                or ""
        ).strip()

        metrics = RagasMetrics(
            answer_relevancy=_safe_float(item.get("answer_relevancy")),
            faithfulness=_safe_float(item.get("faithfulness")),
            context_recall=_safe_float(item.get("context_recall")),
            context_precision=_safe_float(item.get("context_precision")),
            answer_correctness=_safe_float(item.get("answer_correctness")),
            answer_similarity=_safe_float(item.get("answer_similarity")),
            context_entity_recall=_safe_float(item.get("context_entity_recall")),
        )

        contexts: List[NormalizedContext] = []
        raw_contexts = item.get("contexts", [])

        if isinstance(raw_contexts, list):
            for cidx, ctx in enumerate(raw_contexts, start=1):
                if not ctx or not isinstance(ctx, str):
                    continue

                contexts.append(
                    NormalizedContext(
                        context_id=f"context_{cidx}",
                        context_text=ctx.strip(),
                        context_length=len(ctx.split())
                    )
                )

        records.append(
            RagasRecord(
                ticket_id=ticket_id,
                question=question,
                ground_truth=ground_truth,
                rag_answer=rag_answer,
                metrics=metrics,
                contexts=contexts
            )
        )

    return NormalizedRagasResult(
        aggregated_scores=aggregated_scores,
        records=records
    )