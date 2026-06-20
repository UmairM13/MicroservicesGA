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
    

    def _generate(self, client: httpx.Client) -> list[dict]:
        payload = {"chromosomes": self.population_size, **self.context}
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
        })

        if res.status_code != 200:
            print("SELECTION ERROR:", res.json())   
        res.raise_for_status()
        return res.json()['parents']
    

    def _crossover(self, client: httpx.Client, parents: list[dict]) -> list[dict]:
        res = client.post(f"{self.crossover_url}/crossover", json={
            "parents": parents,
            "crossover_rate": self.crossover_rate,
        })

        res.raise_for_status()
        return res.json()['offspring']
    
    def _mutate(self, client: httpx.Client, chromosomes: list[dict]) -> list[dict]:
        payload = {
            "chromosomes": chromosomes,
            "mutation_rate": self.mutation_rate,
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