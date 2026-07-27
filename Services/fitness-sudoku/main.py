""" Sudoku fitness evalutaion microservice. """

from fastapi import FastAPI
from pydantic import BaseModel
from fitness import evaluate_fitness
from typing import Any

app = FastAPI(title = "Sudoku Fitness Evaluation Service", version="0.1.0")

class Chromosome(BaseModel):
    genes: Any
    fitness: float | None = None



class FitnessRequest(BaseModel):
    chromosomes: list[Chromosome]

class FitnessResponse(BaseModel):
    chromosomes: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Sudoku fitness evaluation service is healthy."}

@app.post("/evaluate", response_model=FitnessResponse)
def evaluate(request: FitnessRequest) -> FitnessResponse:
    results = []
    for chromosome in request.chromosomes:
        score = evaluate_fitness(chromosome.genes)
        results.append(Chromosome(genes=chromosome.genes, fitness=score))

    return FitnessResponse(chromosomes=results)