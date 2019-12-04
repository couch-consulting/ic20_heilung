from heilung.models.action import Action


class ExertInfluence(Action):
    """The economic power of a specified city will be randomly reassigned to a new categorical value.
    Could get worse...
    """

    def __init__(self, city):
        """
        :param city: city object of the city in which influence shall be exerted
        """
        action_type = "exertInfluence"
        parameters = {"city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 3
