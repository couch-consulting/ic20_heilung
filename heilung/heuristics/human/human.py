# Human heuristic
from heilung.models import actions
from . import h_utils
from .stateheuristic import Stateheuristic
from .gameplan import Gameplan
import copy


def get_decision(game: 'Game'):
    """
    Get decision for the human heuristic - main entry point
    :param game: Game Object
    :return: List[Action]
    """

    # Init
    game = copy.deepcopy(game)
    stateheuristic = Stateheuristic(game)

    # Simple shortcut to avoid recomputing everything in this case
    # because action list would consist only of this element in the end
    if game.points == 0:
        return [(actions.EndRound(), 1)]  # if decide to add value: (actions.EndRound(), 1.0)

    # Rank of each global action (Scaled to 0-1 whereby most important is 1)
    ranked_global_actions = stateheuristic.rank_global_actions()

    # Rank of each city (Scaled to 0-1 whereby most important is 1)
    city_ranks = stateheuristic.rank_cities()

    # Rank of each action per city (Scaled to 0-1 for each city whereby most important = 1)
    ranked_city_actions_per_city = stateheuristic.rank_actions_for_cities()

    # Combine ranks of city and actions for cities to have one flat list
    combined_ranks = h_utils.compute_combined_importance(city_ranks, ranked_city_actions_per_city)

    # Init Gameplan
    gameplan = Gameplan(game, combined_ranks, ranked_global_actions, stateheuristic.weighted_pathogens)

    # Build a list of actions whereby the first one is most important
    action_list = gameplan.build_action_list()

    return action_list
