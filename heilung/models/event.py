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

    @classmethod
    def from_dict(cls, dct: dict):
        """Creates an event object from a dict

        Arguments:
            dct {dict} -- Dictionary of the event
        """
        del dct['type']
        return cls(**dct)

    def to_dict(self) -> dict:
        """Converts the event object back into a dict

        Returns:
            dict -- Event dictionary
        """
        if 'pathogen' in self.__dict__:
            copy = self.__dict__.copy()
            copy['pathogen'] = copy['pathogen'].to_dict()
            return copy
        return self.__dict__
