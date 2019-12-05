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
        :param name:  [No effect]
        :param latitude: for Location of the city
        :param longitude: for Location of the city
        :param population: [could be relevant for heuristic due to bigger cities are more important]
        :param connections: flight path to another city
        :param economy: [effect unknown how far this helps]
        :param government: [effect unknown how far this helps]
        :param hygiene: [effect unknown how far this helps]
        :param awareness: [effect unknown how far this helps]
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

        self.events, self.outbreak, self.deployed_vaccines = self.event_builder(events)

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
        # TODO model all possible events and make the city class create the associated event classes? For example outbreak
        tmp_events = []
        # Some shortcut vars which can be checked during building
        outbreak = None
        deployed_vaccines = []
        for event in events:
            if event['type'] == 'outbreak':
                # Build Outbreak event
                pathogen = event['pathogen']
                # Build Subevent Pathogen
                pathogen = Pathogen(pathogen['name'], pathogen['infectivity'], pathogen['mobility'],
                                    pathogen['duration'], pathogen['lethality'])
                outbreak = Outbreak(pathogen, event['sinceRound'], event['prevalence'])
                # tmp_events.append(outbreak)
            elif event['type'] == 'vaccineDeployed':
                pathogen = event['pathogen']
                pathogen = Pathogen(pathogen['name'], pathogen['infectivity'], pathogen['mobility'],
                                    pathogen['duration'], pathogen['lethality'])
                if pathogen not in deployed_vaccines:
                    deployed_vaccines.append(pathogen)
            # Build complete event list anyways to have an addition look at stuff TODO check if observer gets problems due to this
            tmp_events.append(event)

        return tmp_events, outbreak, deployed_vaccines

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

# TODO next below (test closeness theory with seed = 1)
# Can an infection spread to a city nearby (location wise by coordinates) without them being connected via flightpath?
# Assumption: yes
# Result: Calculate if close airport/connection or putUnderQuarantie is best idea or if one is for sure cheaper than the others
# Result: See closer cities as potential neighbors/connection for infections and make them more aware/hygienic
# Possibly cities close to another can infect each other - support evidence: game state where 256 of 260 cities were infected but 16 do not even have an airport
