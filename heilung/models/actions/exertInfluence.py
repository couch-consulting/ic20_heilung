from heilung.models.action import Action


class ExertInfluence(Action):
    """The economic power of a specified city will be randomly reassigned to a new categorical value.
    Could get worse...
    """

    def __init__(self, city, possible_cities=None):
        """
        :param city: city object of the city in which influence shall be exerted
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            self.possible_cities = possible_cities
        action_type = "exertInfluence"
        parameters = {"city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 3

    @staticmethod
    def is_possible(game):
        if game.points >= ExertInfluence.get_costs():
            return True
        return False
