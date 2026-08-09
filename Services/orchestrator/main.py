import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from orchestrator import GAOrchestrator


app = FastAPI(title="Island Orchestrator", version="0.1.0")

class RunRequest(BaseModel):
    context: dict
    island_id: int = Field(default=0)
    base_seed: int | None = Field(default=None)
    migration_url: str | None = Field(default=None)
    population_size: int = Field(default=100)
    max_generations: int = Field(default=1000)
    elitism_count: int = Field(default=5)
    mutation_rate: float = Field(default=0.06)
    crossover_rate: float = Field(default=1.0)
    selection_rate: float = Field(default=0.85)
    tournament_size: int = Field(default=2)
    stale_threshold: int = Field(default=15)
    num_islands: int = Field(default=1)
    migration_interval: int = Field(default=10)
    num_migrants: int = Field(default=3)
    topology: str = Field(default="ring")
    migration_rate: float = Field(default=0.05)
  


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}


@app.post("/run")
def run(request: RunRequest):

    orchestrator = GAOrchestrator(
        fitness_url=os.getenv("FITNESS_URL", "http://127.0.0.1:8001"),
        generator_url=os.getenv("GENERATOR_URL", "http://127.0.0.1:8002"),
        crossover_url=os.getenv("CROSSOVER_URL", "http://127.0.0.1:8003"),
        mutation_url=os.getenv("MUTATION_URL", "http://127.0.0.1:8004"),
        # fitness_url=os.getenv("FITNESS_URL", "http://127.0.0.1:8011"),
        # generator_url=os.getenv("GENERATOR_URL", "http://127.0.0.1:8012"),
        # crossover_url=os.getenv("CROSSOVER_URL", "http://127.0.0.1:8013"),
        # mutation_url=os.getenv("MUTATION_URL", "http://127.0.0.1:8014"),

        selector_url=os.getenv("SELECTOR_URL", "http://127.0.0.1:8201"),
        migration_url=request.migration_url or os.getenv("MIGRATION_URL", None),

        context=request.context,
        island_id=request.island_id,
        base_seed=request.base_seed,
        population_size=request.population_size,
        max_generations=request.max_generations,
        elitism_count=request.elitism_count,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        selection_rate=request.selection_rate,
        tournament_size=request.tournament_size,
        stale_threshold=request.stale_threshold,
        num_islands=request.num_islands,
        migration_interval=request.migration_interval,
        num_migrants=request.num_migrants,
        topology=request.topology,
        migration_rate=request.migration_rate
    )

    result = orchestrator.run()
    return result