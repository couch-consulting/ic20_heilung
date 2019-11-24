from heilung.models.action import Action


class DeployMedication(Action):
    """Deploy medication for a specified pathogen to a specified city. 30% to 50% of the citizens infected with the
    pathogen will be cured and are immune afterwards. The medication against the specified pathogen must have been
    developed already.
    """

    def __init__(self, pathogen, city):
        """
        :param pathogen: pathogen object of the pathogen for which a medication shall be developed
        :param city: city object of the city to which the medication shall be deployed
        """
        costs = 10
        action_type = "deployMedication"
        parameters = {"pathogen": pathogen.name, "city": city.name}
        super().__init__(action_type, costs, parameters)
