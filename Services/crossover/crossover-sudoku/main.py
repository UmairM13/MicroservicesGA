from fastapi import FastAPI
from pydantic import BaseModel, Field
from crossover import crossover
import random
from typing import Any


app = FastAPI(title = "Crossover Service", version="0.1.0")

class Chromosome(BaseModel):
    genes: Any
    fitness: float | None = None

class CrossoverRequest(BaseModel):
    parents: list[Chromosome]
    crossover_rate: float = Field(default=0.8)
    seed: int | None = Field(default=None)

class CrossoverResponse(BaseModel):
    offspring: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Crossover service is healthy."}

@app.post("/crossover", response_model=CrossoverResponse)
def do_crossover(request: CrossoverRequest) -> CrossoverResponse:
    offspring = []
    rng = random.Random(request.seed)
    for i in range(0, len(request.parents) - 1, 2):
        parent1 = request.parents[i].genes
        parent2 = request.parents[i + 1].genes
        child1, child2 = crossover(parent1, parent2, rng,  request.crossover_rate)
        offspring.append(Chromosome(genes=child1))
        offspring.append(Chromosome(genes=child2))
    return CrossoverResponse(offspring=offspring)