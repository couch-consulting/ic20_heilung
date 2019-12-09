from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class PathogenEncountered(Event):
    """Model of an pathogenEncountered event
    """

    def __init__(self, pathogen: dict, round: int):
        """Creates a new object

        Arguments:
            pathogen {dict} -- Pathogen medicated against
            round {int} -- Round the pathogen has been encountered in
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        super().__init__("pathogenEncountered", round)
