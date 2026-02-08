import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # dashboard_app/

@st.cache_data
def load_csv_safe(file_bytes, file_name, default_path, required_cols):
    try:
        if file_bytes is not None:
            df = pd.read_csv(BytesIO(file_bytes))
        else:
            full_path = BASE_DIR / default_path
            df = pd.read_csv(full_path)

        missing = required_cols - set(df.columns)
        if missing:
            return None, f"❌ `{file_name}` missing columns: {missing}"

        return df, None

    except FileNotFoundError:
        return None, f"❌ File not found: {default_path}"
    except Exception as e:
        return None, f"❌ Failed to load `{file_name}`: {e}"
