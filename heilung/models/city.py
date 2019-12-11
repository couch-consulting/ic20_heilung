from heilung.models.events import Outbreak
from heilung.models.pathogen import Pathogen
from heilung.utilities import grade_to_scalar
from heilung.models.events.event_utilities import convert_events


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
        self.economy = grade_to_scalar(economy)
        self.government = grade_to_scalar(government)
        self.hygiene = grade_to_scalar(hygiene)
        self.awareness = grade_to_scalar(awareness)
        # Get all events

        self.events, self.outbreak, self.deployed_vaccines, \
        self.airport_closed, self.under_quarantine, self.closed_connections = self.event_builder(events)

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
        events = convert_events(events)
        tmp_events = []
        # Some shortcut vars which can be checked during building
        outbreak = None
        deployed_vaccines = []
        airport_closed = False
        quarantine = False
        connections_closed = []
        for event in events:
            if event.type == 'outbreak':
                outbreak = event
                continue

            elif event.type == 'vaccineDeployed':
                if event.pathogen not in deployed_vaccines:
                    deployed_vaccines.append(event.pathogen)
            elif event.type == 'airportClosed':
                airport_closed = True
            elif event.type == 'quarantine':
                quarantine = True
            elif event.type == 'connectionClosed':
                connections_closed.append(event.city)
            tmp_events.append(
                event)  # TODO maybe here event to dict again such that it does not append objects` addresses but readable dict for debugging

        # TODO maybe refactor to something like "shortcuts"-dict which can be accessed
        return tmp_events, outbreak, deployed_vaccines, airport_closed, quarantine, connections_closed

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

# TODO next below (test closeness theory with seed = 1)
# Can an infection spread to a city nearby (location wise by coordinates) without them being connected via flightpath?
# Assumption: yes
# Result: Calculate if close airport/connection or putUnderQuarantie is best idea or if one is for sure cheaper than the others
# Result: See closer cities as potential neighbors/connection for infections and make them more aware/hygienic
# Possibly cities close to another can infect each other - support evidence: game state where 256 of 260 cities were infected but 16 do not even have an airport
