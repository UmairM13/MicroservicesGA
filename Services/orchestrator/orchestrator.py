import httpx 
import time

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
            elitism_rate: float | None = None,
            mutation_rate: float = 0.06,
            crossover_rate: float = 1.0,
            selection_rate: float = 0.85,
            tournament_size: int = 2,
            stale_threshold: int = 15,
            num_islands: int = 1,
            topology: str = "ring",
            migration_rate: float = 0.05
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
        if elitism_rate is not None:
            self.elitism_count = max(1, round(elitism_rate * population_size))
        else:
            self.elitism_count = elitism_count

        self.elitism_count = min(self.elitism_count, population_size - 2)
        self.mutation_rate = mutation_rate
        self.base_mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.selection_rate = selection_rate
        self.tournament_size = tournament_size
        self.stale_threshold = stale_threshold

        self.last_reinit_gen = -1
        self.num_islands = num_islands
        self.population = []
        self.generation = 0
        self.best_fitness = 0.0
        self.history = []
        self.topology = topology
        self.migration_rate = migration_rate

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

                print(f"Generation {gen}: Best Fitness = {self.best_fitness} (mut_rate={self.mutation_rate:.4f})")

                if self.best_fitness == 1.0:
                    if self.migration_url:
                        try:
                            client.post(f"{self.migration_url}/mark_solved?island_id={self.island_id}")
                            print(f"Island {self.island_id} marked solved on coordinator.")
                        except Exception:
                            pass
                    return self._summary("Solution Found" )
                
                ## Migration
                if self.migration_url and gen > 0 and gen % self.migration_interval == 0:
                    # check if another island already solved
                    try:
                        st = client.get(f"{self.migration_url}/is_solved").json()
                        if st.get("solved"):
                            print(f"Island {self.island_id} stopping — another island solved.")
                            return self._summary("Stopped - Another Island Solved")
                    except Exception as e:
                        print(f"STATUS CHECK ERROR: {e}")
                    self._do_migration(client)
            
                
                # preserves elites
                elites = self.population[:self.elitism_count]

                # select parents
                num_parents = self.population_size - self.elitism_count
                t = time.perf_counter()
                parents = self._select(client, num_parents)
                # print(f"  gen {gen} select    {time.perf_counter()-t:.3f}s")

                # crossover
                t = time.perf_counter()
                offspring = self._crossover(client, parents)
                # print(f"  gen {gen} crossover {time.perf_counter()-t:.3f}s")

                # adapt mutation rate based on recent improvement
                self._adapt_mutation_rate(self.base_mutation_rate)

                # mutation
                t = time.perf_counter()
                offspring = self._mutate(client, offspring)
                # print(f"  gen {gen} mutate    {time.perf_counter()-t:.3f}s")

                # create new population
                t = time.perf_counter()
                offspring = self._evaluate(client, offspring)
                # print(f"  gen {gen} evaluate  {time.perf_counter()-t:.3f}s")

                self.population = elites + offspring

                if self._is_stale() and (self.generation - self.last_reinit_gen) >= self.stale_threshold:
                    print("Population stale - reinitializing")
                    self.last_reinit_gen = self.generation
                    self.population.sort(key=lambda c: c['fitness'], reverse=True)
                    survivors = self.population[:self.elitism_count]
                    fresh = self._generate(client, fresh=True)
                    fresh = self._evaluate(client, fresh)

                    self.population = survivors + fresh[:self.population_size - self.elitism_count]

        return self._summary("Max Generations Reached")
    

    def _do_migration(self, client):
        """Send best chromosomes out and receive migrants from other islands."""
        self.population.sort(key=lambda c: c['fitness'], reverse=True)
        num_to_send = max(1, round(self.migration_rate * self.population_size))
        migrants = self.population[:num_to_send]

        try:
            res = client.post(f"{self.migration_url}/send", json={
                "source_island": self.island_id,
                "migrants": migrants,
                "num_islands": self.num_islands,
                "topology": self.topology
            })
            res.raise_for_status()
            print(f"Island {self.island_id} sent {len(migrants)} migrants.")
        except Exception as e:
            print(f"Failed to send migrants from island {self.island_id}: {e}")

        try:
            res = client.post(f"{self.migration_url}/receive?island_id={self.island_id}")
            res.raise_for_status()
            incoming = res.json()["migrants"]

            if incoming:
                # Cap absorbed migrants at the same proportion we send,
                # so FC (many sources) doesn't flood the island. Keep the best.
                incoming.sort(key=lambda c: c.get('fitness', 0) or 0, reverse=True)
                max_absorb = max(1, round(self.migration_rate * self.population_size))
                incoming = incoming[:max_absorb]

                self.population.sort(key=lambda c: c['fitness'], reverse=True)
                for i, migrant in enumerate(incoming):
                    replace_index = len(self.population) - 1 - i
                    if replace_index > self.elitism_count:
                        self.population[replace_index] = migrant
                print(f"Island {self.island_id} absorbed {len(incoming)} migrants.")
        except Exception as e:
            print(f"Failed to receive migrants for island {self.island_id}: {e}")

    def _generate(self, client: httpx.Client, fresh:bool=False) -> list[dict]:
        seed = self._derive_seed("reinit") if fresh else self.island_seed

        payload = {
            "population_size": self.population_size, 
            "seed": seed,
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
    
    def _is_stale(self) -> bool:
        if len(self.history) < self.stale_threshold:
            return False
        
        recent_history = self.history[-self.stale_threshold:]
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

    def _improve_ratio(self, window:int=10) -> float:
        """ Fraction of the last `window` generations that improved the best fitness."""

        if len(self.history) < 2:
            return 1.0 # No history, consider it improving
        recent = self.history[-(window+1):]
        improvements = sum(
            1 for a, b in zip(recent, recent[1:]) if b > a
        )

        comparisons = len(recent) - 1
        return improvements / comparisons if comparisons > 0 else 1.0

    def _adapt_mutation_rate(
            self, 
            base_rate: float,
            max_rate: float = 0.5,
            window: int = 10,
            up: float = 1.5,
            down: float = 0.9,
    ):
        """ Stagnation triggered mutation control. When the search stalls, raise mutation to escape
        local optima."""

        ratio = self._improve_ratio(window)
        if ratio < 0.2:
            self.mutation_rate = min(self.mutation_rate * up, max_rate)
        else:
            self.mutation_rate = max(self.mutation_rate * down, base_rate)


