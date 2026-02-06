import os

# ==============================
# AWS / Bedrock Settings
# ==============================

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-sonnet-20240229-v1:0"
)

BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "1024"))
BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.2"))

# ==============================
# File / Job Settings
# ==============================

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "86400"))
