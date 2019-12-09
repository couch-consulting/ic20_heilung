from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class VaccineAvailable(Event):
    """Model of an vaccineAvailable event
    """

    def __init__(self, pathogen: dict, sinceRound: int):
        """Creates a new object

        Arguments:
            pathogen {dict} -- Pathogen medicated against
            sinceRound {int} -- [description]
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        super().__init__("vaccineAvailable", sinceRound)
