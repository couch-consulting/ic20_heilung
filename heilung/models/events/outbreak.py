from heilung.models.event import Event
from heilung.models.pathogen import Pathogen


class Outbreak(Event):
    """Model of an Outbreak which includes the model for a sub_event
    """

    def __init__(self, pathogen, sinceRound, prevalence):
        """
        :param pathogen: Pathogen Object
        :param sinceRound: Number of Round in which the outbreak started
        :param prevalence: % as float between 0 and 1, % of infected citizens in the city
        """
        self.pathogen = Pathogen.from_dict(pathogen)
        self.prevalence = prevalence
        super().__init__("outbreak", sinceRound)
