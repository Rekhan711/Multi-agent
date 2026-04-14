import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .agents.orchestrator import Orchestrator
from .core.metrics import (
    gather_dashboard_metrics,
    gather_finance_metrics,
    gather_hr_metrics,
    gather_inventory_metrics,
    gather_sales_metrics,
)
from .db.init_db import init_db
from .db.session import SessionLocal


class ChatRequest(BaseModel):
    question: str
    page: Optional[str] = None
    messages: Optional[list[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    agents: list[str]


app = FastAPI(title="Multi-Agent BI System")

cors_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
allow_all_origins = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else cors_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    init_db()


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    orchestrator = Orchestrator(db)
    result = orchestrator.handle(request.question, messages=request.messages)
    return ChatResponse(answer=result["answer"], agents=result.get("agents", []))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics_endpoint(page: Optional[str] = "dashboard", db: Session = Depends(get_db)):
    page = page.lower()
    if page == "dashboard":
        return gather_dashboard_metrics(db)
    if page == "sales":
        return gather_sales_metrics(db)
    if page == "inventory":
        return gather_inventory_metrics(db)
    if page == "finance":
        return gather_finance_metrics(db)
    if page == "hr":
        return gather_hr_metrics(db)
    raise HTTPException(status_code=400, detail="Unknown metrics page")
