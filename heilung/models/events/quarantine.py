from heilung.models.event import Event


class Quarantine(Event):
    """Model of an connection closed event
    """

    def __init__(self, sinceRound: int, untilRound: int):
        """Creates a new event object

        Arguments:
            city {str} -- Name (!) of the city
            sinceRound {int} -- Start Round
            untilRound {int} -- End Round
        """
        self.untilRound = untilRound
        super().__init__("quarantine", sinceRound)
