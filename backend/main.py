from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="RAGAS BI Analytics")

app.include_router(router, prefix="/api")
