from heilung.models.event import Event


class Outbreak(Event):
    """Model of an Outbreak which includes the model for a sub_event
    """

    def __init__(self, pathogen, since_round, prevalence):
        """
        :param pathogen: Pathogen Object
        :param since_round: Number of Round in which the outbreak started
        :param prevalence: % as float between 0 and 1, % of infected citizens in the city
        """
        self.pathogen = pathogen
        self.prevalence = prevalence
        super().__init__("outbreak", since_round)
