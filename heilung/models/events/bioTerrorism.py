from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class BioTerrorism(Event):
    """Model of an BT event
    """

    def __init__(self, pathogen: dict, round: int):
        """Initializes a new BT object

        Arguments:
            pathogen {dict} -- Dictionary of the Pathogen Object
            round {int} -- Round when this event occured
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        super().__init__('bioTerrorism', round)

    @classmethod
    def fromDict(cls, dct: dict):
        return cls(dct['pathogen'], dct['round'])
