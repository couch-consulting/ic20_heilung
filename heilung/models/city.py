from heilung.models.events.outbreak import Outbreak
from heilung.models.events.sub_event.pathogen import Pathogen

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
        # Get all events

        self.events, self.outbreak = self.event_builder(events)

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

    def event_builder(self, events):
        """
        [TMP Solution]

        Should model all events correct at some point
        :param events:
        :return:
        """
        # TODO add correct event Builder here after we know all event types for all possible events
        # TODO maybe move into constructor of evnets class
        tmp_events = []
        # Some shortcut vars which can be checked during building
        outbreak = None
        for event in events:
            if event['type'] == "outbreak":
                # Build Outbreak event
                pathogen = event['pathogen']
                # Build Subevent Pathogen
                pathogen = Pathogen(pathogen['name'], pathogen['infectivity'], pathogen['mobility'],
                                    pathogen['duration'], pathogen['lethality'])
                outbreak = Outbreak(pathogen, event['sinceRound'], event['prevalence'])
                # tmp_events.append(outbreak)
            else:
                # Default for unknown events
                tmp_events.append(event)

        return tmp_events, outbreak



# TODO model all possible events and make the city class create the associated event classes? For example outbreak
