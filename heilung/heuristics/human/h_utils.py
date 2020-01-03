# Utils for human heuristic - all operation that change the rank outsourced such that it can be replaced more easily
from heilung.models import events
from heilung.models import actions

# Global vars
MAX_VAL = 1
biasMAP = {
    # Bias based upon idea how much more important one action is than another
    # not based upon the game state but based upon the game plan
    actions.DeployVaccine: 1,
    actions.DeployMedication: 0.75,

    actions.PutUnderQuarantine: 0.7,
    actions.CloseAirport: 0.65,
    actions.CloseConnection: 0.6,

    actions.CallElections: 0.5,
    actions.ApplyHygienicMeasures: 0.5,
    actions.ExertInfluence: 0.5,
    actions.LaunchCampaign: 0.5,

}


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


def compute_combined_importance(city_ranks, ranked_city_actions_per_city):
    """
    Compute the importance of each element in the action list when related back to its city importance
    :param city_ranks: dict with city as key and city rank as value
    :param ranked_city_actions_per_city: dict with city as key and list of tuples with action object and current rank as value
    :return: list of tuples with action object and adjusted rank sorted with highest rank first
    """
    result = []
    for city_name, ranked_actions in ranked_city_actions_per_city.items():
        city_rank = city_ranks[city_name]
        for action, action_rank in ranked_actions:
            # Take average of all importance values
            new_rank = (city_rank + biasMAP[type(action)] + action_rank) / 3
            result.append((action, new_rank))

    # Sort
    if result:
        result.sort(key=lambda x: x[1], reverse=True)
    return result


def since_round_percentage(current_round, city, inverted=True):
    """
    Computes a percentage equal to how old or new a round is
    :param current_round: current round of the game
    :param city: city object
    :param inverted: if true, 100% equals old, if false 100% equal new
    :return: percentage of how old or new a round is
    """
    # Put sinceRound into contrast of overall rounds and give a value that indicates how long this outbreak exits
    if current_round >= 6:  # this feature is only useful when some rounds already passed
        return compute_percentage(current_round, city.outbreak.sinceRound, inverted=inverted)
    else:
        return 0
