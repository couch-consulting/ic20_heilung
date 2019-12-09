from heilung.models.event import Event


class EconomicCrisis(Event):
    """Model of an economicCrisis event
    """

    def __init__(self, sinceRound: int):
        """Create new object

        Arguments:
            sinceRound {int} -- Round the event occurred on
        """
        super().__init__("economicCrisis", sinceRound)
