from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class VaccineDeployed(Event):
    """Model of an vaccine deployed event
    """

    def __init__(self, pathogen: dict, round: int):
        """Creates a new object

        Arguments:
            pathogen {dict} -- Pathogen medicated against
            round {int} -- [description]
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        super().__init__("vaccineDeployed", round)
