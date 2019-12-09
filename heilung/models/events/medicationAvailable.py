from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class MedicationAvailable(Event):
    """Model of an medicationAvailable event
    """

    def __init__(self, pathogen: dict, sinceRound: int):
        """Creates a new object

        Arguments:
            pathogen {dict} -- Pathogen medicated against
            sinceRound {int} -- [description]
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        super().__init__("medicationAvailable", sinceRound)
