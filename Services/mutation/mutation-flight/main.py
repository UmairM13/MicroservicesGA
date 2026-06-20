from fastapi import FastAPI
from pydantic import BaseModel, Field
from mutation import mutate


app = FastAPI(title = "Mutation-flight Service", version="0.1.0")


class Chromosome(BaseModel):
    genes: list[int]
    fitness: float | None = None


class MutationRequest(BaseModel):
    chromosomes: list[Chromosome]
    num_gates: int = Field(default=5)
    mutation_rate: float = Field(default=0.06)


class MutationResponse(BaseModel):
    mutated: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Mutation-flight service is healthy."}


@app.post("/mutate", response_model=MutationResponse)
def do_mutate(request: MutationRequest) -> MutationResponse:
    results = []
    for chromosome in request.chromosomes:
        mutated_genes = mutate(chromosome.genes, request.num_gates, request.mutation_rate)
        results.append(Chromosome(genes=mutated_genes))
    return MutationResponse(mutated=results)

