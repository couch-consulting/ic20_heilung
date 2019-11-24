from heilung.models.action import Action


class CallElections(Action):
    """The stability of the government of a specified city will be randomly reassigned.
    Could get worse...
    """

    def __init__(self, city):
        """
        :param city: city object of the city in which an election should be called
        """
        costs = 3
        action_type = "callElections"
        parameters = {"city": city.name}
        super().__init__(action_type, costs, parameters)
