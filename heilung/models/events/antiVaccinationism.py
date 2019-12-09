from heilung.models.event import Event


class AntiVaccinationism(Event):
    """Model of an anti vax event
    """

    def __init__(self, sinceRound: int):
        """Initializes a new anti vax event object

        Arguments:
            round {int} -- Round when this event occured
        """
        super().__init__('antiVaccinationism', sinceRound)
