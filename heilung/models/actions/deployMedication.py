from heilung.models.action import Action


class DeployMedication(Action):
    """Deploy medication for a specified pathogen to a specified city. 30% to 50% of the citizens infected with the
    pathogen will be cured and are immune afterwards. The medication against the specified pathogen must have been
    developed already.
    """

    def __init__(self, city, pathogen, possible_cities=None):
        """
        :param pathogen: pathogen object of the pathogen for which a medication shall be developed
        :param city: city object of the city to which the medication shall be deployed
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            self.possible_cities = possible_cities
        action_type = "deployMedication"
        parameters = {"pathogen": pathogen.name, "city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 10

    @staticmethod
    def is_possible(game, pathogen):
        # "Is possible for in this game"
        # (since medication can be deployed multiple times to a given city, the city is irrelevant)

        # Has enough points, medication has been already developed
        if game.points >= DeployMedication.get_costs() and pathogen in game.pathogens_with_medication:
            return True
        return False
