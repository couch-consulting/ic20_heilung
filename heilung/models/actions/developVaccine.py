from heilung.models.action import Action


class DevelopVaccine(Action):
    """Starts the development of a vaccine for a specified sub_event. Takes 6 Rounds. Pathogen must have infected a
    city in the game so far
    """

    def __init__(self, pathogen):
        """
        :param pathogen: pathogen object
        """
        action_type = "developVaccine"
        parameters = {"pathogen": pathogen.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 40
