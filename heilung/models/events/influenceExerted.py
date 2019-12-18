from heilung.models.event import Event


class InfluenceExerted(Event):
    """Model of an influenceExerted event
    """

    def __init__(self, round: int):
        """Create an influenceExerted event object

        Arguments:
            round {int} -- Round the event first occurred in
        """
        super().__init__("influenceExerted", round)
