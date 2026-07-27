from fastapi import FastAPI
from pydantic import BaseModel, Field
from generator import generate_population

app = FastAPI(title = "Generate Service", version="0.1.0")

class GenerateRequest(BaseModel):
    puzzle: list[list[int]]
    population_size: int = Field(default=100)
    seed:int | None  = Field(default=None)


class Chromosome(BaseModel):
    genes: list[list[int]]
    fitness: float | None = None

class GenerateResponse(BaseModel):
    chromosomes: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Generator service is healthy."}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse: 
    grids = generate_population(request.puzzle, request.population_size, seed=request.seed)
    chromosomes = [Chromosome(genes=grid) for grid in grids]
    return GenerateResponse(chromosomes=chromosomes)



