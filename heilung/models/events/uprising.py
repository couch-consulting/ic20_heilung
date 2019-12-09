from heilung.models.event import Event


class Uprising(Event):
    """Model of an uprising event
    """

    def __init__(self, participants: int, sinceRound: int):
        """Create an Uprising event object

        Arguments:
            participants {int} -- umber of participants
            sinceRound {int} -- Round the event first occurred in
        """
        self.participants = participants
        super().__init__("uprising", sinceRound)
