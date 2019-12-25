from heilung.models.event import Event


class ElectionsCalled(Event):
    """Model of an electionsCalled event
    """

    def __init__(self, round: int):
        """Create an electionCalled event object

        Arguments:
            round {int} -- Round the event first occurred in
        """
        super().__init__("electionsCalled", round)
