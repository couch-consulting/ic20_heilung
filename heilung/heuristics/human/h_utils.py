# Utils for human heuristic - not moved to the pathogen class to avoid logic specific to heuristics their
import math
from heilung.models import events

# Default 5 == 100% (before dependencies)
DEFAULT_SCALE = 5


# Made into own functions to make it easily changeable
def increase_on_dependency(pat_to_increase, dependent_pathogen):
    # math.ceil(X/2) makes [0,1,2,3,4,5,...] -> [0,1,1,2,2,3,...]
    # The higher dependent_pathogen the better pat_to_increase
    new_value = pat_to_increase + math.ceil(dependent_pathogen / 2)
    # no max value
    return new_value


def decrease_on_dependency(pat_to_decrease, dependent_pathogen):
    # The higher dependent_pathogen the worse pat_to_decrease
    new_value = pat_to_decrease - math.ceil(dependent_pathogen / 2)
    if new_value < 1:
        # min value is 1
        new_value = 1
    return new_value


def percentage_to_num_value(percentage, cut=0.1, bias=0):
    """
    Return num_value for percentage whereby default_scale equals to 100%
    :param percentage: number between 0-1
    :param cut: percentage that dictates values below it will make the result 0, should be between 0-1
    :param bias: bias value to add to the final result
    :return: integer between 0-5
    """
    if percentage == 0 or percentage < cut:
        # make 0% = 0 and support min percentage before influence
        return 0
    else:
        return math.ceil(DEFAULT_SCALE * percentage) + bias


def compute_pathogen_importance(pathogen):
    return pathogen.infectivity + pathogen.lethality + pathogen.duration + pathogen.mobility


def compute_percentage(max_val, current_val, inverted=False):
    """
    Get value between 0-1 which stands for the percentage that current_val is of max_val
    :param max_val: highest value possible
    :param current_val: current value
    :return: float 0-1
    """
    if inverted:
        return 1 - (1 / max_val * current_val)
    else:
        return 1 / max_val * current_val


def helpful_events_list():
    # List of any event that could have happened after a city specif action was called that helped this city in someway
    return [events.MedicationDeployed, events.VaccineDeployed, events.Quarantine, events.InfluenceExerted,
            events.HygienicMeasuresApplied, events.ElectionsCalled, events.ConnectionClosed, events.CampaignLaunched,
            events.AirportClosed]
