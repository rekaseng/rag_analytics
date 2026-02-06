import json

def load_ragas(raw: bytes) -> dict:
    return json.loads(raw)
