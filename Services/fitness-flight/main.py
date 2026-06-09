from fastapi import FastAPI
from pydantic import BaseModel, Field
from fitness import evaluate_fitness

app = FastAPI(title = "Fitness Service - Flight Scheduling", version="0.1.0")

class Chromosome(BaseModel):
    genes: list[int]
    fitness: float | None = None


class FlightInfo(BaseModel):
    flight_id: int
    arrival: int
    departure: int
    passengers: int

class FitnessRequest(BaseModel):
    chromosomes: list[Chromosome]
    flights: list[FlightInfo]
    num_gates: int = Field(default=5)


class FitnessResponse(BaseModel):
    chromosomes: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", "message": "Fitness-flight service is healthy."}


@app.post("/evaluate", response_model=FitnessResponse)
def evaluate(request: FitnessRequest) -> FitnessResponse:
    flights = [f.model_dump() for f in request.flights]
    results = []
    for chromosome in request.chromosomes:
        score = evaluate_fitness(chromosome.genes, flights, request.num_gates)
        results.append(Chromosome(genes=chromosome.genes, fitness=score))

    return FitnessResponse(chromosomes=results)


