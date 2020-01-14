from heilung.models.action import Action


class DeployVaccine(Action):
    """Deploy the vaccine of a specified pathogen to all non-infected citizen of a specified city. They are going to
    be instantly immune to the specified pathogen. The vaccine for the specified pathogen must be researched already.
    """

    def __init__(self, city, pathogen, possible_cities=None):
        """Generates on object of this action

        Arguments:
            city {City} -- city object of the city to which the vaccine shall be deployed
            pathogen {Pathogen} -- Pathogen object of the pathogen for which a vaccine shall be developed

        Keyword Arguments:
            possible_cities {List[City]} -- List of possible cities to evaluate this event for (default: {None})
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            self.possible_cities = possible_cities
        action_type = "deployVaccine"
        parameters = {"pathogen": pathogen.name, "city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 5

    @staticmethod
    def is_possible(game, pathogen, city):
        # "Is possible for this city in this game"

        # Has enough points, vaccine has been already developed and no vaccine has been deployed in this city so far
        if game.points >= DeployVaccine.get_costs() \
                and pathogen in game.pathogens_with_vaccine \
                and pathogen not in city.deployed_vaccines:
            return True
        return False
