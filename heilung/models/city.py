from heilung.models.events.event_utilities import convert_events
from heilung.utilities import grade_to_scalar


class City:
    """Basic City Object Modeling connections
    """

    def __init__(self, name, latitude, longitude, population,
                 connections, economy, government, hygiene,
                 awareness, events):
        """Basic city object
        constructor takes that many parameters to allow fluent transformation from input dict

        Arguments:
            name {str} -- Just the name
            latitude {float} -- for Location of the city
            longitude {float} -- for Location of the city
            population {int} -- Number of inhabitants
            connections {List[str]} -- List of city names connected to
            economy {str} -- Textual ranking for this property
            government {str} -- Textual ranking for this property
            hygiene {str} -- Textual ranking for this property
            awareness {str} -- Textual ranking for this property
            events {List[dict]} -- List of events
        """
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.population = population
        self.connections = connections
        self.economy = grade_to_scalar(economy)
        self.government = grade_to_scalar(government)
        self.hygiene = grade_to_scalar(hygiene)
        self.awareness = grade_to_scalar(awareness)

        # Event specific helpers
        self.outbreak = None
        self.deployed_vaccines = []
        self.deployed_medication = []
        self.airport_closed = False
        self.under_quarantine = False
        self.closed_connections = []

        self.events = convert_events(events)
        # Some shortcut vars which can be checked during building

        for event in self.events:
            if event.type == 'outbreak':
                self.outbreak = event
            elif event.type == 'vaccineDeployed':
                if event.pathogen not in self.deployed_vaccines:
                    self.deployed_vaccines.append(event.pathogen)
            elif event.type == 'medicationDeployed':
                if event.pathogen not in self.deployed_medication:
                    self.deployed_medication.append(event.pathogen)
            elif event.type == 'airportClosed':
                self.airport_closed = True
            elif event.type == 'quarantine':
                self.under_quarantine = True
            elif event.type == 'connectionClosed':
                self.closed_connections.append(event.city)

    @classmethod
    def from_dict(cls, city_name: str, city: dict):
        """Converts a dict as sent from the client to a city object

        Arguments:
            city_name {str} -- Name as sent by the client
            city {dict} -- Data Structure of a city as sent by the client
        """
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

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def has_event(self, event_object):
        """Check whether this city has a certain event

        Arguments:
            event_object {Event} -- Event to check

        Returns:
            bool -- True or False
        """
        for event in self.events:
            if isinstance(event, event_object):
                return True
        return False

    @property
    def mobility(self):
        """Get the state of how mobile this city is (related to pathogen)
        Returns mobility levels:
        0. quarantined (or no nearby neighbors an airport closed [not implemented])
        1/2. only land route to nearby neighbors (i.e. no airport or airport is closed)
        1. airport open

        Returns:
            float -- value between 0 and 1 representing the mobility
        """
        mobility_lvl = 0
        # Amount of connections
        if not self.under_quarantine:
            num_of_con = len([city for city in self.connections if city not in self.closed_connections])
            if num_of_con == 0 or self.airport_closed:
                mobility_lvl = 1 / 2
            else:
                mobility_lvl = 1

        return mobility_lvl

    @property
    def open_connections(self):
        """Get open connection of the city

        Returns:
            List[str] -- List of strings with city names of connections that are still open
        """
        return list(set(self.closed_connections).difference(self.connections))

# TODO next below (test closeness theory with seed = 1)
# Can an infection spread to a city nearby (location wise by coordinates) without them being connected via flightpath?
# Assumption: yes
# Result: Calculate if close airport/connection or putUnderQuarantie is best idea or if one is for sure cheaper than the others
# Result: See closer cities as potential neighbors/connection for infections and make them more aware/hygienic
# Possibly cities close to another can infect each other - support evidence: game state where 256 of 260 cities were infected but 16 do not even have an airport
