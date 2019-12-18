# Utils for human heuristic - not moved to the pathogen class to avoid logic specific to heuristics their
import math


def adjust_pathogen_for_city():
    pass


# Made into own functions to make it easily changeable
def increase_on_dependency(pat_to_increase, dependent_pathogen):
    # math.ceil(X/2) makes [0,1,2,3,4,5] -> [0,1,1,2,2,3]
    # The higher dependent_pathogen the better pat_to_increase
    return pat_to_increase + math.ceil(dependent_pathogen / 2)


def decrease_on_dependency(pat_to_decrease, dependent_pathogen):
    # The higher dependent_pathogen the worse pat_to_decrease
    # TODO umkehr funktion von oben finden
    return pat_to_decrease - math.ceil(dependent_pathogen / 2)


def compute_importance(infectivity, lethality, duration, mobility):
    return infectivity + lethality + duration + mobility
