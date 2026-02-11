import boto3
import json
from typing import List, Dict
from settings import AWS_REGION, BEDROCK_MODEL_ID
from utils.logger import get_logger

logger = get_logger(__name__)

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION
)

def build_ticket_rank_prompt(ticket_payload: list) -> str:
    return f"""
You are a RAG quality auditor.

You will receive multiple RAG evaluation tickets.
Your task is to rank the tickets by urgency to investigate.

Ranking signals:
- context_entity_recall
- context_precision
- context_recall
- answer_correctness
- answer_similarity
- answer_relevancy
- faithfulness
- resolution_category
- needs_manual_review
- dropped_context_count

Rules:
- Rank 1 = highest urgency
- Rank tickets RELATIVELY
- Do not assign the same rank unless unavoidable

🚨 Return STRICT JSON ONLY in this schema:

{{
  "ranked_tickets": [
    {{
      "ticket_id": "<string>",
      "rank": <integer>,
      "reason": "<short explanation>"
    }}
  ]
}}

Ticket data:
{json.dumps(ticket_payload, indent=2)}
"""

def build_context_rank_prompt(context_payload: list) -> str:
    return f"""
You are a RAG context quality auditor.

Your task:
- Rank ALL contexts by urgency to review or drop
- Higher rank = higher priority
- Compare contexts RELATIVELY (do not assign the same rank unless unavoidable)

Ranking signals:
- context_char_count
- context_token_count
- question_keyword_coverage_pct
- ground_truth_keyword_coverage_pct
- rag_answer_keyword_coverage_pct
- entity_match
- is_context_useful
- drop_recommendation

🚨 Return STRICT JSON ONLY in this exact schema:

{{
  "ranked_contexts": [
    {{
      "ticket_id": "<string>",
      "context_id": "<string>",
      "rank": <integer>,
      "reason": "<short explanation>"
    }}
  ]
}}

Context data:
{json.dumps(context_payload, indent=2)}
"""


def rank_single_context(context_payload: dict) -> dict:
    prompt = build_context_rank_prompt(context_payload)

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "system": "Respond ONLY with valid JSON.",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.0
        })
    )

    return json.loads(response["body"].read())


def invoke_claude(prompt: str) -> dict:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": (
            "You are a strict ranking engine. "
            "Respond ONLY with valid JSON."
        ),
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 3000,
        "temperature": 0.0
    }

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body).encode("utf-8")
    )

    raw = json.loads(response["body"].read().decode("utf-8"))

    try:
        # 🔑 Extract Claude text output
        text_blocks = raw.get("content", [])
        if not text_blocks:
            raise ValueError("No content returned by Claude")

        text_output = text_blocks[0].get("text", "").strip()

        # ⚠️ Detect truncation
        if raw.get("stop_reason") == "max_tokens":
            logger.warning("Claude response truncated due to max_tokens")

        return json.loads(text_output)

    except Exception as e:
        logger.error("Failed to parse Claude response: %s", raw)
        return {
            "ranked_contexts": [],
            "error": str(e)
        }


def rank_ragas_bi(ragas_bi_rows: List[Dict]) -> List[Dict]:
    # Build payload for ALL tickets
    payload = [
        {
            "ticket_id": r["ticket_id"],
            "context_entity_recall": r["context_entity_recall"],
            "context_precision": r["context_precision"],
            "context_recall": r["context_recall"],
            "answer_correctness": r["answer_correctness"],
            "answer_similarity": r["answer_similarity"],
            "answer_relevancy": r["answer_relevancy"],
            "faithfulness": r["faithfulness"],
            "resolution_category": r["resolution_category"],
            "needs_manual_review": r["needs_manual_review"],
            "context_count": r["context_count"],
            "useful_context_count": r["useful_context_count"],
            "dropped_context_count": r["dropped_context_count"],
        }
        for r in ragas_bi_rows
    ]

    prompt = build_ticket_rank_prompt(payload)
    response = invoke_claude(prompt)

    ranked = {
        r["ticket_id"]: r
        for r in response.get("ranked_tickets", [])
    }

    for row in ragas_bi_rows:
        info = ranked.get(row["ticket_id"])
        row["rank"] = info["rank"] if info else 999
        row["rank_reason"] = info["reason"] if info else "Not ranked by LLM"

    return ragas_bi_rows


def rank_context_bi(context_bi: list) -> list:
    """
    Rank contexts in batches to avoid token limit truncation.
    Processes contexts in chunks of 50 to stay within token limits.
    """
    BATCH_SIZE = 50
    ranking_map = {}

    # Process in batches
    for i in range(0, len(context_bi), BATCH_SIZE):
        batch = context_bi[i:i + BATCH_SIZE]
        
        payload = [
            {
                "ticket_id": r["ticket_id"],
                "context_id": r["context_id"],
                "context_char_count": r["context_char_count"],
                "context_token_count": r["context_token_count"],
                "question_keyword_coverage_pct": r["question_keyword_coverage_pct"],
                "ground_truth_keyword_coverage_pct": r["ground_truth_keyword_coverage_pct"],
                "rag_answer_keyword_coverage_pct": r["rag_answer_keyword_coverage_pct"],
                "entity_match": r["entity_match"],
                "is_context_useful": r["is_context_useful"],
                "usefulness_reason": r["usefulness_reason"],
                "drop_recommendation": r["drop_recommendation"],
            }
            for r in batch
        ]

        prompt = build_context_rank_prompt(payload)
        response = invoke_claude(prompt)

        # 🔒 Defensive parsing
        ranked_contexts = response.get("ranked_contexts", [])

        for r in ranked_contexts:
            if "ticket_id" in r and "context_id" in r:
                ranking_map[(r["ticket_id"], r["context_id"])] = r

    # Apply rankings to all contexts
    for row in context_bi:
        key = (row["ticket_id"], row["context_id"])
        rank_info = ranking_map.get(key)

        row["rank"] = rank_info["rank"] if rank_info else 999
        row["rank_reason"] = rank_info["reason"] if rank_info else "Not ranked by LLM"

    return context_bi



