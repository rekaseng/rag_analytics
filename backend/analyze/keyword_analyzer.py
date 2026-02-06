import re
from typing import Dict, List, Set
from models.ragas_models import NormalizedRagasResult


STOPWORDS = {
    "the", "is", "are", "a", "an", "and", "or", "to", "of", "in",
    "for", "on", "by", "with", "before", "after", "be", "can",
    "may", "will", "shall", "that", "this"
}


def _tokenize(text: str) -> Set[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def extract_keywords(normalized: NormalizedRagasResult) -> Dict[str, Dict]:
    """
    Extract keywords and compute overlaps per ticket.
    """

    keyword_results = {}

    for record in normalized.records:
        q_kw = _tokenize(record.question)
        gt_kw = _tokenize(record.ground_truth)
        ans_kw = _tokenize(record.rag_answer)

        context_kw = set()
        for ctx in record.contexts:
            context_kw |= _tokenize(ctx.context_text)

        keyword_results[record.ticket_id] = {
            "question_keywords": sorted(q_kw),
            "ground_truth_keywords": sorted(gt_kw),
            "rag_answer_keywords": sorted(ans_kw),
            "context_keywords": sorted(context_kw),

            "missing_context_keywords": sorted(gt_kw - context_kw),
            "missing_answer_keywords": sorted(gt_kw - ans_kw),

            "keyword_overlap_score": (
                len(gt_kw & context_kw) / len(gt_kw)
                if gt_kw else 1.0
            )
        }

    return keyword_results
