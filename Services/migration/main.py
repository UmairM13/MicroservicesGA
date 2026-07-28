import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from migration import MigrationManager


app = FastAPI(title="Migration Service", version="0.1.0")

manager = MigrationManager(
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    num_islands = int(os.getenv("NUM_ISLANDS", 4)),
    topology = os.getenv("TOPOLOGY", "ring")
)


class Chromosome(BaseModel):
    genes: Any
    fitness: float | None = None


class SendRequest(BaseModel):
    source_island: int
    migrants: list[Chromosome]
    num_islands: int = 4
    topology: str = "ring"


class ReceiveResponse(BaseModel):
    migrants: list[Chromosome]


@app.get("/health")
def health():
    return {"status": "ok", 
            "message": "Migration service is healthy.",
            "topology": manager.topology,
            "num_islands": manager.num_islands,
            "topology": manager.topology,
            }


@app.post("/send")
def send_migrants(request: SendRequest):
    migrant_dicts = [m.model_dump() for m in request.migrants]
    targets = manager.send_migrants(request.source_island, migrant_dicts,
                                    request.num_islands, request.topology)
    print(f"[MIGRATION] island {request.source_island} (of {request.num_islands}, {request.topology}) -> targets {targets}")
    return {"status": "ok", "source_island": request.source_island,
            "targets": targets, "num_migrants_sent": len(migrant_dicts)}


@app.post("/receive", response_model=ReceiveResponse)
def receive_migrants(island_id: int):
    migrants = manager.receive_migrants(island_id)
    return ReceiveResponse(
        migrants=[Chromosome(**m) for m in migrants]
    )


@app.post("/mark_solved")
def mark_solved(island_id: int):
    manager.mark_solved()
    return {"status": "ok", "message": f"solved by {island_id} "}


@app.get("/is_solved")
def is_solved():
    return {"solved": manager.is_solved()}

@app.post("/reset")
def reset():
    manager.solved = False
    return {"status": "reset"}