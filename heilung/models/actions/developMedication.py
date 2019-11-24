from heilung.models.action import Action


class DevelopMedication(Action):
    """Starts the development of the medication against a specified pathogen. This takes 3 rounds. The pathogen must
    have had an outbreak in the given game so far.
    """

    def __init__(self, pathogen):
        """
        :param pathogen: pathogen object of the pathogen for which a medication shall be developed
        """
        costs = 20
        action_type = "developMedication"
        parameters = {"pathogen": pathogen.name}
        super().__init__(action_type, costs, parameters)
