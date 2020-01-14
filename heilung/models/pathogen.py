from heilung.utilities import grade_to_scalar


class Pathogen:
    """A Pathogen
    """

    def __init__(self, name, infectivity, mobility, duration, lethality, transformation=True):
        """Pathogen object modelling the given input

        Arguments:
            name {str} -- Fictive name of the pathogen
            infectivity {str} -- Textual representation for ranking - possibility to infect citizens of other cities or of the city with the outbreak
            mobility {str} -- Textual representation for ranking - possibility of spread to not connected cities
            duration {str} -- Textual representation for ranking - of rounds a citizen is infected who might infect others
            lethality {str} -- Textual representation for ranking - of infected citizen dying

        Keyword Arguments:
            transformation {bool} -- Convert text to scalar values (default: {True})
        """

        self.name = name
        if transformation:
            self.infectivity = grade_to_scalar(infectivity)
            self.mobility = grade_to_scalar(mobility)
            self.duration = grade_to_scalar(duration)
            self.lethality = grade_to_scalar(lethality)
        else:
            self.infectivity = infectivity
            self.mobility = mobility
            self.duration = duration
            self.lethality = lethality

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
        # self.__dict__ == other.__dict__ changed to name due to possible changes in other property values
        return self.name == other.name

    @property
    def max_prop(self) -> int:
        return max(self.infectivity, self.mobility, self.duration, self.lethality)
