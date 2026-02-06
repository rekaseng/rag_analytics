from typing import List, Dict
from models.ragas_models import NormalizedRagasResult
from utils.text_utils import count_tokens


def _safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def analyze_contexts(
    normalized: NormalizedRagasResult,
    keyword_analysis: Dict[str, Dict]
) -> List[Dict]:
    """
    Analyze context usefulness with keyword coverage percentages
    and token cost awareness.
    """

    context_bi_rows = []

    for record in normalized.records:
        ticket_id = record.ticket_id
        metrics = record.metrics

        q_keywords = set(keyword_analysis[ticket_id]["question_keywords"])
        gt_keywords = set(keyword_analysis[ticket_id]["ground_truth_keywords"])
        ans_keywords = set(keyword_analysis[ticket_id]["rag_answer_keywords"])

        for ctx in record.contexts:
            ctx_text = ctx.context_text
            ctx_text_lower = ctx_text.lower()

            # --- Size metrics ---
            context_char_count = len(ctx_text)
            context_token_count = count_tokens(ctx_text)

            # --- Keyword detection ---
            context_keywords = {
                k for k in (q_keywords | gt_keywords | ans_keywords)
                if k in ctx_text_lower
            }

            overlapping_question_keywords = q_keywords & context_keywords
            overlapping_ground_truth_keywords = gt_keywords & context_keywords
            overlapping_answer_keywords = ans_keywords & context_keywords

            missing_question_keywords = q_keywords - context_keywords
            missing_ground_truth_keywords = gt_keywords - context_keywords

            # --- Coverage percentages ---
            question_keyword_coverage_pct = _safe_pct(
                len(overlapping_question_keywords),
                len(q_keywords)
            )

            ground_truth_keyword_coverage_pct = _safe_pct(
                len(overlapping_ground_truth_keywords),
                len(gt_keywords)
            )

            rag_answer_keyword_coverage_pct = _safe_pct(
                len(overlapping_answer_keywords),
                len(ans_keywords)
            )

            # --- RAGAS-aligned usefulness ---
            entity_match = len(overlapping_ground_truth_keywords) > 15

            is_useful = (
                entity_match
                or question_keyword_coverage_pct > 15
                or (rag_answer_keyword_coverage_pct > 0 and metrics.faithfulness >= 0.7)
                or metrics.context_recall < 0.6
            )

            drop_recommendation = (
                not is_useful
                and metrics.context_precision < 0.5
            )

            reason = (
                "Supports question or ground truth keywords"
                if is_useful
                else "Low keyword coverage; high token waste risk"
            )

            context_bi_rows.append({
                "ticket_id": ticket_id,
                "context_id": ctx.context_id,
                "context_text": ctx_text,

                # 🔢 Cost metrics
                "context_char_count": context_char_count,
                "context_token_count": context_token_count,

                # 🔑 Keyword lists
                "context_keywords": sorted(context_keywords),
                "question_keywords": sorted(q_keywords),
                "ground_truth_keywords": sorted(gt_keywords),
                "rag_answer_keywords": sorted(ans_keywords),

                # 🔍 Overlap lists
                "overlapping_question_keywords": sorted(overlapping_question_keywords),
                "overlapping_ground_truth_keywords": sorted(overlapping_ground_truth_keywords),
                "overlapping_answer_keywords": sorted(overlapping_answer_keywords),

                # 📈 Coverage metrics (NEW)
                "question_keyword_coverage_pct": question_keyword_coverage_pct,
                "ground_truth_keyword_coverage_pct": ground_truth_keyword_coverage_pct,
                "rag_answer_keyword_coverage_pct": rag_answer_keyword_coverage_pct,

                # ❌ Missing keywords
                "missing_question_keywords": sorted(missing_question_keywords),
                "missing_ground_truth_keywords": sorted(missing_ground_truth_keywords),

                # 📊 Flags
                "entity_match": entity_match,
                "is_context_useful": is_useful,
                "usefulness_reason": reason,
                "drop_recommendation": drop_recommendation
            })

    return context_bi_rows
