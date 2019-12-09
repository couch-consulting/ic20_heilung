from heilung.models.event import Event


class LargeScalePanic(Event):
    """Model of an largeScalePanic event
    """

    def __init__(self, sinceRound: int):
        """Create new object

        Arguments:
            sinceRound {int} -- Round the event occurred on
        """
        super().__init__("largeScalePanic", sinceRound)
