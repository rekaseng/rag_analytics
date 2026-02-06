from pydantic import BaseModel
from typing import List, Dict


# -------- Context --------
class NormalizedContext(BaseModel):
    context_id: str
    context_text: str
    context_length: int


# -------- Question-Level Metrics --------
class RagasMetrics(BaseModel):
    answer_relevancy: float
    faithfulness: float
    context_recall: float
    context_precision: float
    answer_correctness: float
    answer_similarity: float
    context_entity_recall: float


# -------- One Evaluation Record --------
class RagasRecord(BaseModel):
    ticket_id: str
    question: str
    ground_truth: str
    rag_answer: str
    metrics: RagasMetrics
    contexts: List[NormalizedContext]


# -------- Normalized Root --------
class NormalizedRagasResult(BaseModel):
    aggregated_scores: Dict[str, float]
    records: List[RagasRecord]
