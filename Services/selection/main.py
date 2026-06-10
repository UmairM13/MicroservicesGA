from fastapi import FastAPI
from pydantic import BaseModel, Field
from selection import tournament_select
from typing import Any

app = FastAPI(title = "Selection Service", version="0.1.0")

class Chromosome(BaseModel):
    genes: Any
    fitness: float | None = None

class SelectionRequest(BaseModel):
    chromosomes: list[Chromosome]
    num_parents: int
    tournament_size: int = Field(default=2)
    selection_rate: float = Field(default=0.85)


class SelectionResponse(BaseModel):
    parents: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Selection service is healthy."}


@app.post("/select", response_model=SelectionResponse)
def select(request: SelectionRequest) -> SelectionResponse:
    chromosome_dicts = [c.model_dump() for c in request.chromosomes]
    selected = tournament_select(
        chromosome_dicts,
        num_parents=request.num_parents,
        tournament_size=request.tournament_size,
        selection_rate=request.selection_rate
    )
    parents = [Chromosome(**chromo) for chromo in selected]
    return SelectionResponse(parents=parents)