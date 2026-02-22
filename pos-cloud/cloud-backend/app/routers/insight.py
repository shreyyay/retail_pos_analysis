from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.llm_service import ask_insight, get_insight_cards

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    store_id: str


@router.post("/query")
def query_insight(payload: QueryRequest):
    return ask_insight(payload.question, payload.store_id)


@router.get("/cards")
def insight_cards(store_id: str = Query(...), period: str = Query(default="weekly")):
    cards = get_insight_cards(store_id, period)
    return {"cards": cards}
