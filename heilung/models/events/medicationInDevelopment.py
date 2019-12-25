from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class MedicationInDevelopment(Event):
    """Model of an medicationInDevelopment event
    """

    def __init__(self, pathogen: dict, sinceRound: int, untilRound):
        """Creates a new object

        Arguments:
            pathogen {dict} -- Pathogen medicated
            sinceRound {int} -- Round started
            untilRound {[type]} -- Round it will be finished
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        self.untilRound = untilRound
        super().__init__("medicationInDevelopment", sinceRound)
