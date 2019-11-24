class Event:
    """Basic Event Model
    """

    def __init__(self, event_type, since_round):
        """
        :param event_type: type of event
        :param since_round: Number of round in which the event occurred
        """
        self.type = event_type
        self.sinceRound = since_round
