from heilung.models.action import Action


class DevelopVaccine(Action):
    """Starts the development of a vaccine for a specified sub_event. Takes 6 Rounds. Pathogen must have infected a
    city in the game so far
    """

    def __init__(self, pathogen, input_is_str=False):
        """
        :param pathogen: pathogen object
        """
        action_type = "developVaccine"
        if input_is_str:
            parameters = {"pathogen": pathogen}
        else:
            parameters = {"pathogen": pathogen.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 40

    @staticmethod
    def is_possible(game, pathogen):
        # "Is possible for this game"

        # Game has enough points, the vaccine is not already developed and is not getting developed right now
        if game.points >= DevelopVaccine.get_costs() and \
                pathogen not in game.pathogens_with_vaccine \
                and pathogen not in game.pathogens__with_developing_vaccine:
            return True
        return False
