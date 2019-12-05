from heilung.models.action import Action


class ApplyHygienicMeasures(Action):
    """The hygienic-standards of the specified city are randomly increased (TO a higher categorical value).
    """

    def __init__(self, city, possible_cities=None):
        """
        :param city: city object of the city in which hygienic measures should be applied
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            self.possible_cities = possible_cities
        action_type = "applyHygienicMeasures"
        parameters = {"city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 3
