import copy
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rnd

from alns import ALNS
from alns.accept import HillClimbing
from alns.select import RouletteWheel
from alns.stop import MaxIterations

BEAM_LENGTH = 0
class CspState:
    """
    Solution state for the CSP problem. It has two data members, assignments
    and unassigned. Assignments is a list of lists, one for each beam in use.
    Each entry is another list, containing the ordered beams cut from this
    beam. Each such sublist must sum to at most BEAM_LENGTH. Unassigned is a
    list of ordered beams that are not currently assigned to one of the
    available beams.
    """

    def __init__(self, assignments, unassigned=None):
        self.assignments = assignments
        self.unassigned = []
        if unassigned is not None:
            self.unassigned = unassigned

    def copy(self):
        """
        Helper method to ensure each solution state is immutable.
        """
        return CspState(copy.deepcopy(self.assignments), self.unassigned.copy())

    def objective(self):
        """
        Computes the total number of beams in use.
        """
        return len(self.assignments)

    def plot(self):
        """
        Helper method to plot a solution.
        """
        _, ax = plt.subplots(figsize=(12, 6))

        ax.barh(np.arange(len(self.assignments)),
                [sum(assignment) for assignment in self.assignments],
                height=1)

        ax.set_xlim(right=BEAM_LENGTH)
        ax.set_yticks(np.arange(len(self.assignments), step=10))

        ax.margins(x=0, y=0)

        ax.set_xlabel('Usage')
        ax.set_ylabel('Beam (#)')

        plt.draw_if_interactive()


def wastage(assignment):
    """
    Helper method that computes the wastage on a given beam assignment.
    """
    return BEAM_LENGTH - sum(assignment)


"""DESTROY OPERATORS"""
degree_of_destruction = 0.25
def beams_to_remove(num_beams):
    return int(num_beams * degree_of_destruction)

def random_removal(state, random_state):
    """
    Iteratively removes randomly chosen beam assignments.
    """
    state = state.copy()

    for _ in range(beams_to_remove(state.objective())):
        idx = random_state.randint(state.objective())
        state.unassigned.extend(state.assignments.pop(idx))

    return state

def worst_removal(state, random_state):
    """
    Removes beams in decreasing order of wastage, such that the
    poorest assignments are removed first.
    """
    state = state.copy()

    # Sort assignments by wastage, worst first
    state.assignments.sort(key=wastage, reverse=True)

    # Removes the worst assignments
    for _ in range(beams_to_remove(state.objective())):
        state.unassigned.extend(state.assignments.pop(0))

    return state

"""REPAIR OPERATORS"""
def greedy_insert(state, random_state):
    """
    Inserts the unassigned beams greedily into the first fitting
    beam. Shuffles the unassigned ordered beams before inserting.
    """
    random_state.shuffle(state.unassigned)

    while len(state.unassigned) != 0:
        beam = state.unassigned.pop(0)

        for assignment in state.assignments:
            if beam <= wastage(assignment):
                assignment.append(beam)
                break
        else:
            state.assignments.append([beam])

    return state

def minimal_wastage(state, random_state):
    """
    For every unassigned ordered beam, the operator determines
    which beam would minimise that beam's waste once the ordered
    beam is inserted.
    """
    def insertion_cost(assignment, beam):  # helper method for min
        if beam <= wastage(assignment):
            return wastage(assignment) - beam

        return float("inf")

    while len(state.unassigned) != 0:
        beam = state.unassigned.pop(0)

        assignment = min(state.assignments, key=partial(insertion_cost, beam=beam))

        if beam <= wastage(assignment):
            assignment.append(beam)
        else:
            state.assignments.append([beam])

    return state

def alnsSolver(stock_length, cutData, iterations=1000, seed=1234):
    BEAM_LENGTH = stock_length
    BEAMS = cutData # must be a flattened list 
    # Define the initial state of the problem
    rnd_state = rnd.RandomState(seed)
    state = CspState([], BEAMS.copy())

    # Run the greedy insert algorithm to get an initial solution
    init_sol = greedy_insert(state, rnd_state)

    # Create the ALNS object
    alns = ALNS(rnd_state)
    alns.add_destroy_operator(random_removal)
    alns.add_destroy_operator(worst_removal)
    alns.add_repair_operator(greedy_insert)
    alns.add_repair_operator(minimal_wastage)
    accept = HillClimbing()
    select = RouletteWheel([3, 2, 1, 0.5], 0.8, 2, 2)
    stop = MaxIterations(iterations)
    result = alns.iterate(init_sol, select, accept, stop)
    solution = result.best_state
    
    # Return the best solution found
    return solution.assignments