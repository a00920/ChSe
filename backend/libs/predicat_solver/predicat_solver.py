from deap import creator, base, tools, algorithms
import random

class Predicate:
    POSITIVE_TYPE = 0
    NEGATIVE_TYPE = 1

    def __init__(self, type, indices):
        self.type = type
        self.indices = indices
        self.max_index = max(self.indices)

    def is_solution(self, solution):
        if self.type == self.POSITIVE_TYPE:
            return any([solution[index] for index in self.indices])
        else:
            return any([not solution[index] for index in self.indices])


def recursive_solve_system(predicates, current_index, max_index, current_solution, solutions):
    if current_index > max_index:
        solutions.append(list(current_solution))
        return

    for current_value in [True, False]:
        current_solution[current_index] = current_value
        if check_part_solve(current_solution, predicates, current_index):
            recursive_solve_system(predicates, current_index + 1, max_index, current_solution,
                                   solutions)


def check_part_solve(current_solution, predicates, current_index):
    return all([predicate.is_solution(current_solution) for predicate in predicates
                if predicate.max_index == current_index])


def solve_system(predicates):
    solutions = []
    max_index = max([predicate.max_index for predicate in predicates])
    null_solve = [False] * (max_index + 1)
    recursive_solve_system(predicates, 0, max_index, null_solve, solutions)
    return solutions


def solve_system_with_GA(predicates):
    max_index = max([predicate.max_index for predicate in predicates])

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    toolbox.register("attr_bool", random.randint, 0, 1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool,
                     max_index + 1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evalOneMax(individual):
        return sum([predicate.is_solution(individual) * (1 + 0.1 * len(predicate.indices)) for predicate in predicates]),

    toolbox.register("evaluate", evalOneMax)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=1000)
    NGEN=100
    for gen in range(NGEN):
        offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
        fits = toolbox.map(toolbox.evaluate, offspring)
        for fit, ind in zip(fits, offspring):
            ind.fitness.values = fit
        population = toolbox.select(offspring, k=len(population))
    top = tools.selBest(population, k=1)[0]
    undefined = []
    best_res = evalOneMax(top)
    for i in range(len(top)):
        top_clone = list(top)
        top_clone[i] = not bool(top_clone[i])
        if round(evalOneMax(top_clone)[0], 5) == round(best_res[0], 5):
            undefined.append(i)
        elif round(evalOneMax(top_clone)[0], 5) > round(best_res[0], 5):
            print("GA is trash")
    for i in undefined:
        top[i] = 2
    return top
