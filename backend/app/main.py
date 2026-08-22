import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import analysis, audit, kpis

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clarity API", description="AI KPI Storytelling Engine", version="1.0.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router)
app.include_router(analysis.router)
app.include_router(audit.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "clarity-api"}
