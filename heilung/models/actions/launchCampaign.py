from heilung.models.action import Action


class LaunchCampaign(Action):
    """The caution of citizens in a specified city will be randomly increased (to a higher categorical value)
    """

    def __init__(self, city):
        """
        :param city: city object of the city that in which the campaign should be launched
        """
        action_type = "launchCampaign"
        parameters = {"city": city.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 3
