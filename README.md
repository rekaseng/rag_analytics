# Dashboard App

Streamlit dashboard for RAG WisE monitoring and analytics.

## Quick Start

### Local Development (Windows)
```bash
cd dashboard_app
uv pip install -r requirements.txt
uv run streamlit run app.py --server.port=3005 --server.address=0.0.0.0
```

Access at: http://localhost:3005

### Production Deployment (Ubuntu/Linux)
```bash
# Run in background with nohup
nohup uv run streamlit run app.py --server.port=3005 --server.address=0.0.0.0 > streamlit.log 2>&1 &

# View logs
tail -f streamlit.log

# Stop the process
ps -ef | grep streamlit
kill -9 <PID>
```

## Features

- **RAG WisE Dashboard**: User feedback analytics, message tracking, RAG process logs
- **RAGAS Dashboard**: Provides analytics and insights based on RAGAS evaluation scores.

## Dependencies

Managed via `uv` package manager. Key dependencies:
- streamlit
- pandas
- plotly
- psycopg2-binary
- matplotlib

## Database Tables

- `vw_user_feedback_summary`: User feedback and message data
- `rag_process_result_log`: RAG process execution logs
