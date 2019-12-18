from functools import reduce
from typing import List, Tuple

import networkx as nx

from heilung.models import City
from heilung.models.event import Event
from heilung.models.events.medicationDeployed import MedicationDeployed
from heilung.models.events.vaccineDeployed import VaccineDeployed

from heilung.models.pathogen import Pathogen
from heilung.models.events.event_utilities import convert_events


class Game:
    """Models the overall game state
    """

    def __init__(self, state):
        self.round = state['round']
        self.outcome = state['outcome']
        self.points = state['points']
        self.cities = {city[0]: City.from_dict(city[0], city[1]) for city in state['cities'].items()}
        self.events = convert_events(state.setdefault('events', list()))
        self.error = state.setdefault('error', '')

        # Create a graph of all connections between cities
        self.connections = nx.Graph()
        self.connections.add_nodes_from(self.cities.keys())
        edges = [(from_city, to_city) for from_city, city in self.cities.items()
                 for to_city in city.connections]
        self.connections.add_edges_from(edges)

        # Feature that shall not be recomputed on every call like properties below
        self.cities_list = [city for _, city in self.cities.items()]
        self.biggest_city = max(self.cities_list, key=lambda x: x.population)




    def state_recap(self, short=False):
        """
        Help function to get a easily human readable output of the current state (filtered for only infected cities)
        :return: String of the state recap
        """
        outbreaks = self.outbreaks
        overview = "\n***** %s Round Overview *****\n" \
                   "Outcome: %s | Points: %s | Infected Cities: %s | Relevant Pathogens: %s | Total Population %s" \
                   % (self.round, self.outcome, self.points, len(outbreaks), len(self.pathogens_in_cities),
                      self.total_population)
        overview += "\n" + str([pat.name for pat in self.pathogens_in_cities])
        overview += "\n" + str([city.name for city in self.cities_infected])
        error = "Error MSG: %s" % self.error
        game_events = "Game events: %s" % str([event.type for event in self.events])
        infected_cities = ""
        if not short:
            infected_cities = "-Infected Cities- \n"
            for city, outbreak in outbreaks:
                # Build overview of infected city
                pathogen = city.outbreak.pathogen
                tmp_string = "City Name: %s \n \t SinceRound: %s, Prevalence: %s \n \t Pathogen Name: %s \n \t " \
                             "Infectivity: %s, Mobility: %s, Duration: %s, Lethality: %s \n" % \
                             (city.name, outbreak.sinceRound, outbreak.prevalence, pathogen.name, pathogen.infectivity,
                              pathogen.mobility, pathogen.duration, pathogen.lethality)
                infected_cities = infected_cities + tmp_string

        return "\n".join([overview, error, game_events, infected_cities])

    @property
    def outbreaks(self) -> List[Tuple[City, dict]]:
        """
        [BASIC IMPLEMENTATION]
        Get a list of all cities which got an outbreak
        :return: list of city and the outbreak objects
        """
        return [(city, city.outbreak) for _, city in self.cities.items() if city.outbreak]

    @property
    def city_events(self) -> List[Tuple[City, dict]]:
        return [(city, city.events) for city in self.cities.values() if len(city.events) > 0]

    @property
    def total_population(self) -> int:
        return reduce(lambda a, b: a + b, [city.population for _, city in self.cities.items()])

    # Following are functions and properties to gather data about the game state TODO decide if refactor

    # Cities state
    def get_cities_with_pathogen(self, pathogen) -> List[City]:
        """
        Build list of cities in which the given pathogen in present
        :param pathogen: pathogen object
        :return: List[City]
        """

        return [city for _, city in self.cities.items() if city.outbreak if
                city.outbreak.pathogen.name == pathogen.name]

    @property
    def cities_infected(self) -> List[City]:
        """
        Builds a list of all infected cities
        :return: List[City]
        """
        return [city for _, city in self.cities.items() if city.outbreak]

    @property
    def cities_without_airport(self) -> List[City]:
        """
        Builds a list of all cities without an airport
        :return: List[City]
        """
        return [city for _, city in self.cities.items() if not city.connections]


    # Pathogens state

    @property
    def pathogens_in_cities(self) -> List[Pathogen]:
        """
        Build a list of pathogens which are infecting cities currently
        :return: List[Pathogen]
        """
        pathogen_names_in_cities = {outbreak.pathogen.name for _, outbreak in self.outbreaks}
        return [pathogen for pathogen in self.pathogens_encountered if pathogen.name in pathogen_names_in_cities]

    @property
    def pathogens_encountered(self) -> List[Pathogen]:
        """
        Builds a list of already encountered pathogens
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('pathogenEncountered')

    @property
    def pathogens__with_developing_vaccine(self) -> List[Pathogen]:
        """
        Builds a list of pathogens for which a vaccine is in development
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('vaccineInDevelopment')

    @property
    def pathogens_with_vaccine(self) -> List[Pathogen]:
        """
        Builds a list of pathogens for which a vaccine was developed
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('vaccineAvailable')

    @property
    def pathogens__with_developing_medication(self) -> List[Pathogen]:
        """
        Builds a list of pathogens for which a medication is in development
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('medicationInDevelopment')

    @property
    def pathogens_with_medication(self) -> List[Pathogen]:
        """
        Builds a list of pathogens for which a medication was developed
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('medicationAvailable')

    @property
    def pathogens_in_need_of_medication(self) -> List[Pathogen]:
        """
        Get list of pathogens for which the current game still needs to develop medication
            "needs to" is defined as: It is useful to develop this medication because the pathogen is still an active outbreak in at least one city
        :return: List[Pathogen]
        """
        path_list1 = self.pathogens_in_cities
        path_list2 = self.pathogens__with_developing_medication
        path_list3 = self.pathogens_with_medication

        return [pathogen for pathogen in path_list1 if pathogen not in path_list2 + path_list3]

    @property
    def pathogens_in_need_of_vaccine(self) -> List[Pathogen]:
        """
        Get list of pathogens for which the current game still needs to develop vaccines
            "needs to" is defined as: It is useful to develop this medication because the pathogen is still an active outbreak in at least one city
        :return: List[Pathogen]
        """
        path_list1 = self.pathogens_in_cities
        path_list2 = self.pathogens__with_developing_vaccine
        path_list3 = self.pathogens_with_vaccine

        return [pathogen for pathogen in path_list1 if pathogen not in path_list2 + path_list3]

    def pathogens_events_sub_list(self, event_type) -> List[Pathogen]:
        """
        Get a list of pathogen objects for the specified event type
        :param event_type: str
        :return: List[Pathogen]
        """
        return [event.pathogen for event in self.events if
                event.type == event_type]

    def get_relevant_pathogens(self, pathogens) -> List[Pathogen]:
        """
        Filters out irrelevant pathogens for a given list of pathogens
        :param pathogens: List[Pathogen]
        :return: List[Pathogen]
        """
        relevant_pathogens = self.pathogens_in_cities

        return [pathogen for pathogen in pathogens if pathogen in relevant_pathogens]

    def get_percentage_of_infected(self, pathogen) -> int:
        """
        Get the amount of all currently alive citizen infected by this pathogen
        :param pathogen: pathogen object
        :return: % of the infected as value between 0-1
        """
        total_pop = self.total_population + 1
        total_infected = sum([city.population * city.outbreak.prevalence for city in self.cities_infected if
                              city.outbreak.pathogen == pathogen])
        return 1 / total_pop * total_infected

    def get_percentage_of_immune(self, pathogen) -> int:
        """
        (To an extend an heuristic/biased approach to this feature)
        Get the amount of all currently alive citizen which are not infected in a city with a outbreak and vaccine deployed
        Whereby the people made immune by medication is assumed to be the worst case estimate
        :param pathogen: pathogen object
        :return: % of the immune as value between 0-1
        """
        total_pop = self.total_population + 1

        # Immune in currently infected cities
        infected_cities = self.get_cities_with_pathogen(pathogen)
        total_immune = sum([city.population * (1 - city.outbreak.prevalence) for city in infected_cities if
                            pathogen in city.deployed_vaccines])
        # Worst case estimate for medication, only 30% became immune
        total_immune += sum([city.population * (city.outbreak.prevalence / 0.7 * 0.3) for city in infected_cities if
                             pathogen in city.deployed_medication])

        # Immune in already "healed" cities
        non_outbreak_cities = [city for city in self.cities_list if city.outbreak is None]
        cities_with_vaccine = [city for city in non_outbreak_cities if [True for event in city.events if
                                                                        isinstance(event,
                                                                                   VaccineDeployed) and event.pathogen == pathogen]]
        cities_with_medication_only = [city for city in non_outbreak_cities if
                                       city not in cities_with_vaccine and [True for event in city.events if
                                                                            isinstance(event,
                                                                                       MedicationDeployed) and event.pathogen == pathogen]]
        # additionally all population of all cities which were infected and are now healed, i.e. pathogen does not exist anymore
        total_immune += sum([city.population for city in cities_with_vaccine])
        # if vac not but only medication assume 50% are immune
        total_immune += sum([city.population * 0.5 for city in cities_with_medication_only])

        return 1 / total_pop * total_immune

    # currently not used but could be useful later
    @property
    def pathogens_without_vaccine(self) -> List[Pathogen]:
        """
        Get list of pathogens for which no vaccine is or was developed so far
        :return: List[Pathogen]
        """
        path_list1 = self.pathogens_encountered
        path_list2 = self.pathogens__with_developing_vaccine
        path_list3 = self.pathogens_with_vaccine

        return [pathogen for pathogen in path_list1 if pathogen not in path_list2 + path_list3]

    @property
    def pathogens_without_medication(self) -> List[Pathogen]:
        """
        Get list of pathogens for which no medication is or was developed so far
        :return: List[Pathogen]
        """
        path_list1 = self.pathogens_encountered
        path_list2 = self.pathogens__with_developing_medication
        path_list3 = self.pathogens_with_medication

        return [pathogen for pathogen in path_list1 if pathogen not in path_list2 + path_list3]
