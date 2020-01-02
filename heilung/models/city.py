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
        # TODO: Evaluate necessity of prepossessing
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

        self.events, self.outbreak, self.deployed_vaccines, self.deployed_medication, \
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
        # TODO maybe move into constructor of events class
        events = convert_events(events)
        tmp_events = []
        # Some shortcut vars which can be checked during building
        outbreak = None
        deployed_vaccines = []
        deployed_medication = []
        airport_closed = False
        quarantine = False
        connections_closed = []
        for event in events:
            if event.type == 'outbreak':
                outbreak = event
            elif event.type == 'vaccineDeployed':
                if event.pathogen not in deployed_vaccines:
                    deployed_vaccines.append(event.pathogen)
            elif event.type == 'medicationDeployed':
                if event.pathogen not in deployed_medication:
                    deployed_medication.append(event.pathogen)
            elif event.type == 'airportClosed':
                airport_closed = True
            elif event.type == 'quarantine':
                quarantine = True
            elif event.type == 'connectionClosed':
                connections_closed.append(event.city)
            tmp_events.append(
                event)  # TODO maybe here event to dict again such that it does not append objects` addresses but readable dict for debugging

        # TODO maybe refactor to something like "shortcuts"-dict which can be accessed
        return tmp_events, outbreak, deployed_vaccines, deployed_medication, airport_closed, quarantine, connections_closed

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def has_event(self, event_object):
        for event in self.events:
            if isinstance(event, event_object):
                return True
        return False

    @property
    def mobility(self):
        """
        Get the state of how mobile this city is (related to pathogen)
        Returns mobility levels:
        0. quarantined (or no nearby neighbors an airport closed [not implemented])
        1/2. only land route to nearby neighbors (i.e. no airport or airport is closed)
        1. airport open
        :return: % as float between 0-1
        """
        mobility_lvl = 0
        # Amount of connections
        if not self.under_quarantine:
            num_of_con = len([city for city in self.connections if city not in self.closed_connections])
            if num_of_con == 0 or self.airport_closed:
                mobility_lvl = 1 / 2
            else:
                mobility_lvl = 1

        # TODO revisit after closeness theory is done

        return mobility_lvl

    @property
    def open_connections(self):
        """
        Get open connection of the city
        :return: List of strings with city names of connections that are still open
        """
        return list(set(self.closed_connections).difference(self.connections))

# TODO next below (test closeness theory with seed = 1)
# Can an infection spread to a city nearby (location wise by coordinates) without them being connected via flightpath?
# Assumption: yes
# Result: Calculate if close airport/connection or putUnderQuarantie is best idea or if one is for sure cheaper than the others
# Result: See closer cities as potential neighbors/connection for infections and make them more aware/hygienic
# Possibly cities close to another can infect each other - support evidence: game state where 256 of 260 cities were infected but 16 do not even have an airport
