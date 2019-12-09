from heilung.models.event import Event


class ConnectionClosed(Event):
    """Model of an connection closed event
    """

    def __init__(self, city: str, sinceRound: int, untilRound: int):
        """Creates a new event object

        Arguments:
            city {str} -- Name (!) of the city
            sinceRound {int} -- Start Round
            untilRound {int} -- End Round
        """
        self.city = city
        self.untilRound = untilRound
        super().__init__("connectionClosed", sinceRound)
