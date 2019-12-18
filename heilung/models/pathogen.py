from heilung.utilities import grade_to_scalar


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
        self.infectivity = grade_to_scalar(infectivity)
        self.mobility = grade_to_scalar(mobility)
        self.duration = grade_to_scalar(duration)
        self.lethality = grade_to_scalar(lethality)

    def to_dict(self) -> dict:
        """Return all values as dict

        Returns:
            dict -- Represent this object as dictionary
        """
        return {
            'name': self.name,
            'infectivity': self.infectivity,
            'mobility': self.mobility,
            'duration': self.duration,
            'lethality': self.lethality
        }

    @classmethod
    def from_dict(cls, pathogen: dict):
        """Parse dict object to pathogen object

        Arguments:
            pathogen {dict} -- A pathogen dict as received in a request

        Returns:
            [type] -- an instance of this class
        """
        return cls(
            pathogen['name'],
            pathogen['infectivity'],
            pathogen['mobility'],
            pathogen['duration'],
            pathogen['lethality']
        )

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def max_prop(self) -> int:
        return max(self.infectivity, self.mobility, self.duration, self.lethality)
