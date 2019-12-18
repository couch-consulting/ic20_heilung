# Human heuristic
from heilung.models import actions
from . import h_utils
import math


class Human:
    """
    Human heuristic
    """

    def __init__(self, game):
        self.game = game

    def get_decision(self):

        # Get all pathogens which are relevant
        relevant_pathogens = self.game.pathogens_in_cities
        pathogen_importance_dict = self.get_importance_for_game(relevant_pathogens)
        print(pathogen_importance_dict)
        exit()
        return actions.EndRound().build_action()

    # Main function to get importance
    def get_importance_for_game(self, pathogens):
        """
        Get a dict for a pathogen which defines the importance of this pathogen
        :param pathogens: pathogen object
        :return: dict of number values
        """
        importance_dict = {}
        for pathogen in pathogens:
            lethality = pathogen.lethality
            infectivity = pathogen.infectivity
            duration = pathogen.duration
            mobility = pathogen.mobility

            # Scale from the game
            # % of infected citizens for this pathogen - transformed to value in range 1-5
            per_value = self.game.get_percentage_of_infected(pathogen)
            if per_value == 0:
                tmp_num_value = 0
            else:
                tmp_num_value = math.ceil(5 * per_value)
            infectivity = h_utils.increase_on_dependency(infectivity, tmp_num_value)
            lethality = h_utils.increase_on_dependency(lethality, tmp_num_value)
            # % of Immune citizens overall
            per_value = self.game.get_percentage_of_immune(pathogen)
            if per_value == 0:
                tmp_num_value = 0
            else:
                tmp_num_value = math.ceil(5 * per_value)
            infectivity = h_utils.decrease_on_dependency(infectivity, tmp_num_value)

            # Scale in between pathogen properties
            lethality = h_utils.decrease_on_dependency(lethality, duration)
            infectivity = h_utils.increase_on_dependency(infectivity, duration)
            mobility = h_utils.increase_on_dependency(mobility, infectivity)

            # TODO think about further game wide dependencies for pathogen

            # Apply base bias (lethality stays the same)
            infectivity = max(infectivity - 1, 1)
            mobility = max(mobility - 2, 1)
            duration = max(duration - 3, 1)

            importance_dict[pathogen.name] = h_utils.compute_importance(infectivity, lethality, duration, mobility)

        return importance_dict
