from fastapi import FastAPI
from pydantic import BaseModel, Field
from generator import generate_population 


app = FastAPI(title = "Generator Service - Flight Scheduling", version="0.1.0")

class Chromosome(BaseModel):
    genes: list[int]
    fitness: float | None = None


class GeneratorRequest(BaseModel):
    num_flights: int
    num_gates: int = Field(default=5)
    population_size: int = Field(default=100)
    seed:int | None  = Field(default=None)


class GeneratorResponse(BaseModel):
    chromosomes: list[Chromosome]

@app.get("/health")
def health():
    return {"status": "ok", "message": "Generator-flight service is healthy."}


@app.post("/generate", response_model=GeneratorResponse)
def generate(request: GeneratorRequest) -> GeneratorResponse:
    grids = generate_population(request.num_flights, request.num_gates, request.population_size,
                                seed=request.seed)
    chromosomes = [Chromosome(genes=grid) for grid in grids]
    return GeneratorResponse(chromosomes=chromosomes)

