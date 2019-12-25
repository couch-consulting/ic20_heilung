# Utils for human heuristic - all operation that change the rank outsourced such that it can be replaced more easily
# Rank equals to a percentage which identifies how important a certain object/feature is (the higher the more important)
import math
from heilung.models import events

# Global vars
MAX_VAL = 1


def apply_bias(value_to_decrease, bias_per):
    if bias_per < 0 or bias_per > 1:
        raise ValueError("bias_per must be value between 0 and 1")

    return value_to_decrease * bias_per


def compute_percentage(max_val, current_val, inverted=False):
    """
    Get value between 0-1 which stands for the percentage that current_val is of max_val
    :param max_val: highest value possible
    :param current_val: current value
    :param inverted: used when lower values means better result
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


def compute_pathogen_importance(pathogen_importance, pathogen_original):
    # Combine the importance of the property with its actual value
    # Invert duration of original pathogen since a lower duration is more important
    return 1 * pathogen_importance.infectivity * pathogen_original.infectivity \
           + 1 * pathogen_importance.lethality * pathogen_original.lethality \
           + 1 * pathogen_importance.duration * (1 - pathogen_original.duration) \
           + 1 * pathogen_importance.mobility * pathogen_original.mobility


def compute_combined_importance(city_importance, action_list):
    """
    Compute the importance of each element in the action list when releated back to its city importance
    :param city_importance: importance of city
    :param action_list: list of tuples with action object and current rank
    :return: list of tuples with action object and adjusted rank
    """
    result = []

    for action, rank in action_list:
        adjusted_rank = rank

        result.append((action, adjusted_rank))

    return result

