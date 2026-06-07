import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from orchestrator import GAOrchestrator


app = FastAPI(title="Island Orchestrator", version="1.0")

class RunRequest(BaseModel):
    puzzle: list[list[int]]
    population_size: int = Field(default=100)
    max_generations: int = Field(default=1000)
    elitism_count: int = Field(default=5)
    mutation_rate: float = Field(default=0.06)
    crossover_rate: float = Field(default=1.0)
    selection_rate: float = Field(default=0.85)
    tournament_size: int = Field(default=2)


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}


@app.post("/run")
def run(request: RunRequest):

    orchestrator = GAOrchestrator(
        fitness_url=os.getenv("FITNESS_URL", "http://localhost:8001"),
        generator_url=os.getenv("GENERATOR_URL", "http://localhost:8002"),
        selector_url=os.getenv("SELECTOR_URL", "http://localhost:8003"),
        crossover_url=os.getenv("CROSSOVER_URL", "http://localhost:8004"),
        mutation_url=os.getenv("MUTATION_URL", "http://localhost:8005"),
        population_size=request.population_size,
        max_generations=request.max_generations,
        elitism_count=request.elitism_count,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        selection_rate=request.selection_rate,
        tournament_size=request.tournament_size,
    )

    result = orchestrator.run(request.puzzle)
    return result