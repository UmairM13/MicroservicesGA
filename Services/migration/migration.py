import json
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import NewTopic


class MigrationManager:

    """
    Manages inter-island chromosome migration via Kafka.
    
    Supports ring and fully connected topologies.
    Ring: island i sends to island (i+1) % num_islands.
    Fully connected: island i sends to all other islands."""

    def __init__(
            self,
            bootstrap_servers: str = "127.0.0.1:9092",
            num_islands: int = 4,
            topology: str = "ring",
            ):
        self.bootstrap_servers = bootstrap_servers
        self.num_islands = num_islands
        self.topology = topology
        self.solved = False

        self._ensure_topics()


    def mark_solved(self):
        self.solved = True

    def is_solved(self) -> bool:
        return self.solved

    
    def _ensure_topics(self):

        """ Create per-island inbox topics if they don't exist."""

        admin = AdminClient({"bootstrap.servers": self.bootstrap_servers})
        topics = [
            NewTopic(f"island_{i}_inbox", num_partitions=1, replication_factor=1)
            for i in range(self.num_islands)
        ]

        futures = admin.create_topics(topics)
        for topic, future in futures.items():
            try:
                future.result()
                print(f"Topic {topic} created.")
            except Exception as e:
                if "TOPIC_ALREADY_EXISTS" not in str(e):
                    print(f"Failed to create topic {topic}: {e}")

    def _get_targets(self, source_island: int, num_islands: int, topology: str) -> list[int]:
        """Determine target islands based on topology."""
        if topology == "ring":
            return [(source_island + 1) % num_islands]
        elif topology == "fully_connected":
            return [i for i in range(num_islands) if i != source_island]
        else:
            raise ValueError(f"Unknown topology: {topology}")


    def send_migrants(self, source_island: int, migrants: list[dict], num_islands: int, topology: str):
        producer = Producer({"bootstrap.servers": self.bootstrap_servers})
        targets = self._get_targets(source_island, num_islands, topology)

        for target in targets:
            message = json.dumps({
                "source_island": source_island,
                "target_island": target,
                "migrants": migrants
            })
            producer.produce(
                topic=f"island_{target}_inbox",
                value=message.encode("utf-8")
            )

        producer.flush()
        return targets
        

    def receive_migrants(self, island_id: int, timeout: float = 2.0) -> list[dict]:

        """ Consume any pending migrants from this island's inbox"""

        consumer = Consumer({
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": f"island_{island_id}_group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })

        topic = f"island_{island_id}_inbox"
        consumer.subscribe([topic])

        all_migrants = []

        empty_polls = 0
        while empty_polls < 3:  # Stop after 3 consecutive empty polls
            msg = consumer.poll(timeout)
            if msg is None:
                empty_polls += 1
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                empty_polls += 1
                continue

            empty_polls = 0  # Reset on successful poll
            data = json.loads(msg.value().decode("utf-8"))
            all_migrants.extend(data["migrants"])


        consumer.close()
        return all_migrants
