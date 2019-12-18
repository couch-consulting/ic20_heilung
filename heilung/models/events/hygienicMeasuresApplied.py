from heilung.models.event import Event


class HygienicMeasuresApplied(Event):
    """Model of an hygienicMeasuresApplied event
    """

    def __init__(self, round: int):
        """Create an hygienicMeasuresApplied event object

        Arguments:
            round {int} -- Round the event first occurred in
        """
        super().__init__("hygienicMeasuresApplied", round)
