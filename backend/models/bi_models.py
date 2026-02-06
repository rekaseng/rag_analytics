from pydantic import BaseModel
from typing import List, Optional


# -------- RAGAS BI Output --------
class RagasBIResult(BaseModel):
    ticket_id: str
    question: str
    rag_answer: str
    ground_truth: str

    context_entity_recall: float
    context_precision: float
    context_recall: float
    answer_correctness: float
    answer_similarity: float
    answer_relevancy: float
    faithfulness: float

    eval_context_entity_recall: str
    eval_context_precision: str
    eval_context_recall: str
    eval_answer_correctness: str
    eval_answer_similarity: str
    eval_answer_relevancy: str
    eval_faithfulness: str

    context_count: int
    useful_context_count: int
    dropped_context_count: int

    resolution_category: str
    resolution_confidence: float
    needs_manual_review: bool


# -------- Context BI Output --------
class ContextBIResult(BaseModel):
    ticket_id: str
    context_id: str
    context_text: str
    context_length: int

    keyword_overlap_gt: int
    keyword_overlap_answer: int
    keyword_overlap_question: int

    entity_match: bool
    is_context_useful: bool
    usefulness_reason: str
    drop_recommendation: bool
