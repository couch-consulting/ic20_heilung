from heilung.models.action import Action


class DeployVaccine(Action):
    """Deploy the vaccine of a specified pathogen to all non-infected citizen of a specified city. They are going to
    be instantly immune to the specified pathogen. The vaccine for the specified pathogen must be researched already.
    """

    def __init__(self, city, pathogen):
        """
        :param city: city object of the city to which the vaccine should be deployed
        :param pathogen: pathogen object
        """
        action_type = "deployVaccine"
        parameters = {"pathogen": pathogen.name, "city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 5
