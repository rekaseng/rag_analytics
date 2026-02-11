import uuid
from ingest.ragas_loader import load_ragas
from normalize.ragas_normalizer import normalize
from evaluate.resolution_classifier import classify_resolution
from analyze.keyword_analyzer import extract_keywords
from analyze.context_analyzer import analyze_contexts
from flatten.ragas_bi_flattener import build_ragas_bi
from flatten.context_bi_flattener import build_context_bi
from export.exporter import export_outputs
from analyze.llm_ranker import rank_ragas_bi, rank_context_bi


def run_pipeline(job_id: str, raw_bytes: bytes) -> dict:
    #Load raw RAGAS JSON
    raw = load_ragas(raw_bytes)

    # Generate tracking ID for this upload
    ticket_id = str(uuid.uuid4())

    #Normalize RAGAS results
    normalized = normalize(raw, ticket_id=ticket_id)
    print("✓ Completed normalization")

    #Resolution classification (PER QUESTION)
    resolution_map = classify_resolution(normalized)
    print("✓ Completed resolution classification")

    #Keyword extraction
    keyword_info = extract_keywords(normalized)
    print("✓ Completed keyword extraction")

    #Context analysis (usefulness, token waste)
    contexts = analyze_contexts(normalized, keyword_info)
    print("✓ Completed context analysis")

    #Build RAGAS BI table
    ragas_bi = build_ragas_bi(
        normalized=normalized,
        resolution=resolution_map,
        contexts=contexts,
        keyword_info=keyword_info
    )

    #LLM ranking for RAGAS BI
    ragas_bi = rank_ragas_bi(ragas_bi)
    print("✓ Completed RAGAS BI ranking")

    #Build Context BI table
    context_bi = build_context_bi(
        contexts=contexts,
        keyword_info=keyword_info
    )

    #LLM ranking for Context BI
    context_bi = rank_context_bi(context_bi)
    print("✓ Completed Context BI ranking")

    #Export outputs
    return export_outputs(job_id, ragas_bi, context_bi)
