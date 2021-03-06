from heilung.models.action import Action


class CallElections(Action):
    """The stability of the government of a specified city will be randomly reassigned.
    Could get worse...
    """

    def __init__(self, city, possible_cities=None):
        """Generate on object of this action

        Arguments:
            city {City} -- city object of the city in which an election should be called

        Keyword Arguments:
            possible_cities {List[City]} -- List of possible cities to evaluate this event for (default: {None})
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            self.possible_cities = possible_cities
        action_type = "callElections"
        parameters = {"city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 3

    @staticmethod
    def is_possible(game):
        if game.points >= CallElections.get_costs():
            return True
        return False
