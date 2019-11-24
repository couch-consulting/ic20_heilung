

class City:
    """Basic City Object Modeling connections
    """

    def __init__(self, name, latitude, longitude, population,
                 connections, economy, government, hygiene,
                 awareness, events):
        """
        TODO add descriptions for properties here maybe
        :param name:
        :param latitude:
        :param longitude:
        :param population:
        :param connections:
        :param economy:
        :param government:
        :param hygiene:
        :param awareness:
        :param events:
        """
        # TODO: Evaluate necessity of preprocessing
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.population = population
        self.connections = connections
        self.economy = economy
        self.government = government
        self.hygiene = hygiene
        self.awareness = awareness
        self.events = events

    @classmethod
    def from_dict(cls, city_name, city):
        return cls(
            city_name,
            city['latitude'],
            city['longitude'],
            city['population'],
            city['connections'],
            city['economy'],
            city['government'],
            city['hygiene'],
            city['awareness'],
            city.setdefault('events', list())
        )

# TODO model all possible events and make the city class create the associated event classes? For example outbreak
