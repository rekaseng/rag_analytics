import json
from io import BytesIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # dashboard_app/


def load_json_safe(file_bytes, file_name, default_path, required_keys=None):
    """
    Safely load JSON from:
    1) uploaded file bytes (Streamlit)
    2) fallback JSON file on disk

    Returns:
        (data, error_message)
    """

    try:
        # -------------------------
        # Load JSON
        # -------------------------
        if file_bytes is not None:
            data = json.loads(file_bytes.decode("utf-8"))
        else:
            full_path = BASE_DIR / default_path
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # -------------------------
        # Validate required keys
        # -------------------------
        if required_keys:
            missing = set(required_keys) - set(data.keys())
            if missing:
                return None, f"❌ `{file_name}` missing keys: {missing}"

        return data, None

    except FileNotFoundError:
        return None, f"❌ File not found: {default_path}"
    except json.JSONDecodeError as e:
        return None, f"❌ Invalid JSON format in `{file_name}`: {e}"
    except UnicodeDecodeError:
        return None, f"❌ `{file_name}` must be UTF-8 encoded"
    except Exception as e:
        return None, f"❌ Failed to load `{file_name}`: {e}"
