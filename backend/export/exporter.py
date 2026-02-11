import pandas as pd
import os

BASE = "outputs"
os.makedirs(BASE, exist_ok=True)

def export_outputs(job_id, ragas_bi, context_bi):
    ragas_path = f"{BASE}/{job_id}_ragas_bi.csv"
    context_path = f"{BASE}/{job_id}_context_bi.csv"

    pd.DataFrame(ragas_bi).to_csv(ragas_path, index=False)
    pd.DataFrame(context_bi).to_csv(context_path, index=False)


    return {
        "ragas_bi": ragas_path,
        "context_bi": context_path
    }
