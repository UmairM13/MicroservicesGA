import httpx 


Nd = 9

class GAOrchestrator:

    def __init__(
            self, 
            fitness_url: str,
            generator_url: str,
            selector_url: str,
            crossover_url: str,
            mutation_url: str,
            context: dict,
            island_id: int = 0,
            base_seed: int | None = None,
            migration_url: str | None = None,
            migration_interval: int = 10,
            num_migrants: int = 3,
            population_size: int = 100,
            max_generations: int = 1000,
            elitism_count: int = 5,
            mutation_rate: float = 0.06,
            crossover_rate: float = 1.0,
            selection_rate: float = 0.85,
            tournament_size: int = 2,
    ):
        
        self.fitness_url = fitness_url
        self.generator_url = generator_url
        self.selector_url = selector_url
        self.crossover_url = crossover_url
        self.mutation_url = mutation_url
        self.context = context

        self.island_id = island_id
        self.base_seed = base_seed
        self.island_seed = None if base_seed is None else base_seed + island_id
        self.migration_url = migration_url
        self.migration_interval = migration_interval
        self.num_migrants = num_migrants

        self.population_size = population_size
        self.max_generations = max_generations
        self.elitism_count = elitism_count
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.selection_rate = selection_rate
        self.tournament_size = tournament_size

        self.population = []
        self.generation = 0
        self.best_fitness = 0.0
        self.history = []

    def run( self) -> dict:

        with httpx.Client(timeout=60.0) as client:

            # Generate initial population
            self.population = self._generate(client)
            self.population = self._evaluate(client, self.population)


            for gen in range (self.max_generations):

                self.generation = gen
                
                # sort by fitness descending 
                self.population.sort(key=lambda c: c['fitness'], reverse=True)
                self.best_fitness = self.population[0]['fitness']
                self.history.append(self.best_fitness)

                print(f"Generation {gen}: Best Fitness = {self.best_fitness}")

                if self.best_fitness == 1.0:
                    return self._summary("Solution Found" )
                
                ## Migration
                if self.migration_url and gen > 0 and gen % self.migration_interval == 0:
                    self._do_migration(client)
            
                
                # preserves elites
                elites = self.population[:self.elitism_count]

                # select parents
                num_parents = self.population_size - self.elitism_count
                parents = self._select(client, num_parents)

                # crossover
                offspring = self._crossover(client, parents)

                # mutation
                offspring = self._mutate(client, offspring)

                # create new population
                offspring = self._evaluate(client, offspring)

                self.population = elites + offspring

                if self._is_stale():
                    print("Population stale - reinitializing")
                    self.population = self._generate(client)
                    self.population = self._evaluate(client, self.population)

        return self._summary("Max Generations Reached")
    

    def _do_migration(self, client):
        """Send best chromosomes out and recieve migrants from other islands."""
        self.population.sort(key=lambda c: c['fitness'], reverse=True)
        migrants = self.population[:self.num_migrants]

        try: 
            res = client.post(f"{self.migration_url}/send", json={
                "source_island": self.island_id,
                "migrants": migrants
            })

            res.raise_for_status()
            print(f"Island {self.island_id} sent {len(migrants)} migrants to other islands.")

        except Exception as e:
            print(f"Failed to send migrants from island {self.island_id}: {e}")

        try:
            res = client.post(f"{self.migration_url}/receive?island_id={self.island_id}")
            res.raise_for_status()
            incoming = res.json()["migrants"]

            if incoming:
                self.population.sort(key=lambda c: c['fitness'], reverse=True)

                for i, migrant in enumerate(incoming):
                    replace_index = len(self.population) - 1 - i
                    if replace_index > self.elitism_count: 
                        self.population[replace_index] = migrant
                print(f"Island {self.island_id} received {len(incoming)} migrants from other islands.")

        except Exception as e:
            print(f"Failed to receive migrants for island {self.island_id}: {e}")

    def _generate(self, client: httpx.Client) -> list[dict]:
        payload = {
            "population_size": self.population_size, 
            "seed": self.island_seed,
            **self.context}
        res = client.post(f"{self.generator_url}/generate", json=payload)
        res.raise_for_status()
        return res.json()['chromosomes']


    def _evaluate(self, client: httpx.Client, chromosomes: list[dict]) -> list[dict]:
        payload = {"chromosomes": chromosomes, **self.context}
        res = client.post(f"{self.fitness_url}/evaluate", json=payload)
        res.raise_for_status()
        return res.json()["chromosomes"]
    
    
    def _select(self, client: httpx.Client, num_parents: int) -> list[dict]:
        res = client.post(f"{self.selector_url}/select", json={
            "chromosomes": self.population,
            "num_parents": num_parents,
            "tournament_size": self.tournament_size,
            "selection_rate": self.selection_rate,
            "seed": self._derive_seed("selection"),
        })

        if res.status_code != 200:
            print("SELECTION ERROR:", res.json())   
        res.raise_for_status()
        return res.json()['parents']
    

    def _crossover(self, client: httpx.Client, parents: list[dict]) -> list[dict]:
        res = client.post(f"{self.crossover_url}/crossover", json={
            "parents": parents,
            "crossover_rate": self.crossover_rate,
            "seed": self._derive_seed("crossover"),
        })

        res.raise_for_status()
        return res.json()['offspring']
    
    def _mutate(self, client: httpx.Client, chromosomes: list[dict]) -> list[dict]:
        payload = {
            "chromosomes": chromosomes,
            "mutation_rate": self.mutation_rate,
            "seed": self._derive_seed("mutation"),
            **self.context,
        }
        res = client.post(f"{self.mutation_url}/mutate", json=payload)
        res.raise_for_status()
        return res.json()["mutated"]
    
    def _is_stale(self, threshold: int = 100) -> bool:
        if len(self.history) < threshold:
            return False
        
        recent_history = self.history[-threshold:]
        return len(set(recent_history)) == 1
    
    def _summary(self, status: str) -> dict:
        return {
            "status": status,
            "best_fitness": self.best_fitness,
            "generations": self.generation,
            "history": self.history,
            "best_solution": self.population[0] if self.population else None,
        }


    def _derive_seed(self, tag: str) -> int | None:
        """Derive a deterministic per-call seed from the island seed,
        the current generation, and an operator tag. Returns None if
        seeding is disabled (no base_seed provided)."""
        if self.island_seed is None:
            return None

        tag_num = {"selection": 1, "crossover": 2, "mutation": 3, "reinit":4}[tag]
        return (self.island_seed * 1_000_003 + self.generation * 1009 + tag_num) & 0x7FFFFFFF