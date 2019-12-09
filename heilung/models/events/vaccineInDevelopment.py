from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class VaccineInDevelopment(Event):
    """Model of an vaccineInDevelopment event
    """

    def __init__(self, pathogen: dict, sinceRound: int, untilRound):
        """Create a new object

        Arguments:
            pathogen {dict} -- Pathogen to vax against
            sinceRound {int} -- Started development
            untilRound {[type]} -- When it will be finished
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        self.untilRound = untilRound
        super().__init__("vaccineInDevelopment", sinceRound)
