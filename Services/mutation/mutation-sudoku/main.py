from fastapi import FastAPI
from pydantic import BaseModel, Field
from mutation import mutate
import random


app = FastAPI(title = "Mutation Service", version="0.1.0")

class Chromosome(BaseModel):
    genes: list[list[int]]
    fitness: float | None = None


class MutationRequest(BaseModel):
    chromosomes: list[Chromosome]
    puzzle: list[list[int]]
    mutation_rate: float = Field(default=0.1)
    seed: int | None = Field(default=None)

class MutationResponse(BaseModel):
    mutated: list[Chromosome]

@app.get("/health")
def health():
    return {"status": "ok", "message": "Mutation service is healthy."}


@app.post("/mutate", response_model=MutationResponse)
def do_mutation(request: MutationRequest) -> MutationResponse:
    results = []
    rng = random.Random(request.seed)
    for chromosome in request.chromosomes:
        mutated_genes = mutate(chromosome.genes, request.puzzle, rng, request.mutation_rate)
        results.append(Chromosome(genes=mutated_genes))
    return MutationResponse(mutated=results)

