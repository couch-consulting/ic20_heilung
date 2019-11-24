class Pathogen:
    """A Pathogen
    """

    def __init__(self, name, infectivity, mobility, duration, lethality):
        """
        :param name: Fictive name of the pathogen
        :param infectivity: % as categorical value, % possibility to infect citizens of other cities or of the city with the outbreak
        :param mobility:  % as categorical value, % possibility of spread to not connected cities
        :param duration: # as categorical value, # of rounds a citizen is infected who might infect others
        :param lethality: % as categorical value, % of infected citizen dying
        """
        self.name = name
        self.infectivity = infectivity
        self.mobility = mobility
        self.duration = duration
        self.lethality = lethality
