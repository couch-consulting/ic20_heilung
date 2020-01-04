from functools import reduce
from typing import List, Tuple

import networkx as nx

from heilung.models import City
from heilung.models import events
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
        self.points_per_round = 20

        # Feature that shall not be recomputed on every call like properties below
        self.cities_list = [city for _, city in self.cities.items()]
        self.biggest_city = max(self.cities_list, key=lambda x: x.population)

        pathogen_names_in_cities = {outbreak.pathogen.name for _, outbreak in self.outbreaks}
        self.pathogens_in_cities = [pathogen for pathogen in self.pathogens_encountered if
                                    pathogen.name in pathogen_names_in_cities]

        tmp_cities_with_pathogen = {}
        for pathogen in self.pathogens_in_cities:
            tmp_cities_with_pathogen[pathogen.name] = self._get_cities_with_pathogen(pathogen)
        self.cities_with_pathogen = tmp_cities_with_pathogen

        tmp_pathogen_percentage_of_infected = {}
        tmp_pathogen_percentage_of_immune = {}
        for pathogen in self.pathogens_in_cities:
            tmp_pathogen_percentage_of_infected[pathogen.name] = self._get_percentage_of_infected(pathogen)
            tmp_pathogen_percentage_of_immune[pathogen.name] = self._get_percentage_of_immune(pathogen)
        self.pathogen_percentage_of_infected = tmp_pathogen_percentage_of_infected
        self.pathogen_percentage_of_immune = tmp_pathogen_percentage_of_immune

        self.pathogens__with_developing_vaccine = self.pathogens_events_sub_list('vaccineInDevelopment')
        self.pathogens_with_vaccine = self.pathogens_events_sub_list('vaccineAvailable')
        self.pathogens__with_developing_medication = self.pathogens_events_sub_list('medicationInDevelopment')
        self.pathogens_with_medication = self.pathogens_events_sub_list('medicationAvailable')

        # Construct a pat state dict for relevant pathogens
        self.pat_state_dict = {
            pat.name: {
                'mDev': pat in self.pathogens__with_developing_medication,
                'vDev': pat in self.pathogens__with_developing_vaccine,
                'mAva': pat in self.pathogens_with_medication,
                'vAva': pat in self.pathogens_with_vaccine,
                'any_action': pat in (
                        self.pathogens__with_developing_medication + self.pathogens__with_developing_vaccine
                        + self.pathogens_with_medication + self.pathogens_with_vaccine),
                'prevalence': self._get_percentage_of_infected(pat),
                'immunity': self._get_percentage_of_immune(pat),
                'pathogen': pat,
            } for pat in self.pathogens_in_cities
        }

    def get_state_dict(self, short=True) -> dict:
        """
        Help function to get a dataset summarizing the the current state (filtered for only infected cities)
        :return: dict of the state recap
        """
        data = {
            'round': self.round,
            'outcome': self.outcome,
            'points': self.points,
            'infected_city_count': len(self.outbreaks),
            'relevant_pathogens_count': len(self.pathogens_in_cities),
            'total_population': self.total_population,
            'relevant_pathogens': [pat.name for pat in self.pathogens_in_cities],
            'infected_cities': {city.name: city.outbreak.pathogen.name for city in self.cities_infected},
            'error': self.error,
            'game_events': [event.type for event in self.events],
        }

        if not short:
            infected_cities = list()
            for city, outbreak in self.outbreaks:
                infected_city = {
                    'name': city.name,
                    'population': city.population,
                    'connections': city.connections,
                    'economy': city.economy,
                    'government': city.government,
                    'hygiene': city.hygiene,
                    'awareness': city.awareness,
                    'outbreak': {
                        'pathogen': outbreak.pathogen.name,
                        'prevalence': outbreak.prevalence,
                        'since_round': outbreak.sinceRound
                    }
                }
                infected_cities.append(infected_city)
            data['infected_cities'] = infected_cities
        return data

    def state_recap(self, short=False):
        """
        Help function to get a easily human readable output of the current state (filtered for only infected cities)
        :return: String of the state recap
        """
        recap = self.get_state_dict(short)
        overview = (
            f"\n***** {recap['round']} Round Overview *****\n"
            f"Outcome: {recap['outcome']} | "
            f"Points: {recap['points']} | "
            f"Infected Cities: {recap['infected_city_count']} | "
            f"Relevant Pathogens: {recap['relevant_pathogens_count']} | "
            f"Total Population: {recap['total_population']}\n"
            f"Active Pathogens: {recap['relevant_pathogens']}\n"
            # f"Infected Cities: {recap['infected_cities']}\n"
            f"Error MSG: {recap['error']}\n"
            f"Game events: {recap['game_events']}"
        )
        return overview

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
    def has_new_bioTerrorism(self) -> List[City]:
        cities_with_bio_terror = []
        for city in self.cities.values():
            if city.has_event(events.BioTerrorism):
                for event in city.events:
                    if event.type == 'bioTerrorism' and event.sinceRound == self.round \
                            and event.pathogen in self.pathogens_in_cities \
                            and not self.pat_state_dict[event.pathogen.name]['any_action'] \
                            and not (city.under_quarantine or city.airport_closed):
                        cities_with_bio_terror.append(city)
        return cities_with_bio_terror

    @property
    def total_population(self) -> int:
        return reduce(lambda a, b: a + b, [city.population for _, city in self.cities.items()])

    # Following are functions and properties to gather data about the game state TODO decide if refactor

    # Cities state
    def get_cities_with_pathogen(self, pathogen) -> List[City]:
        return self.cities_with_pathogen[pathogen.name]

    def _get_cities_with_pathogen(self, pathogen) -> List[City]:
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
    def pathogens_encountered(self) -> List[Pathogen]:
        """
        Builds a list of already encountered pathogens
        :return: List[Pathogen]
        """
        return self.pathogens_events_sub_list('pathogenEncountered')

    @property
    def pathogens_in_need_of_medication(self) -> List[Pathogen]:
        """
        Get list of pathogens for which the current game still needs to develop medication
        needs to is defined as: It is useful to develop this medication because the pathogen
         is still an active outbreak in at least one city
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
        needs to is defined as: It is useful to develop this medication
        because the pathogen is still an active outbreak in at least one city
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

    def get_percentage_of_infected(self, pathogen):
        return self.pathogen_percentage_of_infected[pathogen.name]

    def _get_percentage_of_infected(self, pathogen) -> int:
        """
        Get the amount of all currently alive citizen infected by this pathogen
        :param pathogen: pathogen object
        :return: % of the infected as value between 0-1
        """
        total_pop = self.total_population + 1
        total_infected = sum([city.population * city.outbreak.prevalence for city in self.cities_infected if
                              city.outbreak.pathogen == pathogen])
        return 1 / total_pop * total_infected

    def get_percentage_of_immune(self, pathogen):
        return self.pathogen_percentage_of_immune[pathogen.name]

    def _get_percentage_of_immune(self, pathogen) -> int:
        """
        (To an extend an heuristic/biased approach to this feature)
        Get the amount of all currently alive citizen which are not infected in a city with a outbreak and vac deployed
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
                                                                                   VaccineDeployed)
                                                                        and event.pathogen == pathogen]]
        cities_with_medication_only = [city for city in non_outbreak_cities if
                                       city not in cities_with_vaccine and [True for event in city.events if
                                                                            isinstance(event,
                                                                                       MedicationDeployed)
                                                                            and event.pathogen == pathogen]]
        # all population of all cities which were infected and are now healed, i.e. pathogen does not exist anymore
        total_immune += sum([city.population for city in cities_with_vaccine])
        # if vac not but only medication assume 50% are immune
        total_immune += sum([city.population * 0.5 for city in cities_with_medication_only])

        return 1 / total_pop * total_immune

    def has_event(self, event_object):
        for event in self.events:
            if isinstance(event, event_object):
                return True
        return False

    def get_connections_sorted_for_highest_population_first(self, city):
        """
        Return connection list sorted for highest population first
        :param city:
        :return: list
        """
        con_with_pop = [[tmp_city_name, self.cities[tmp_city_name].population] for tmp_city_name in
                        city.connections]
        con_sorted = [con_tuple[0] for con_tuple in sorted(con_with_pop, key=lambda x: x[1], reverse=True)]
        return con_sorted

    @property
    def last_development_finished_since(self):
        """
        Returns the number of rounds since the last development has been finished
        :return: int between 0 and current number of round minus smallest development time or none if none yet finished
        """
        exists_flag = False
        finished_since = 0
        for event in self.events:
            if isinstance(event, (events.MedicationAvailable, events.VaccineAvailable)):
                exists_flag = True
                tmp_finished_since = self.round - event.sinceRound
                if tmp_finished_since > finished_since:
                    finished_since = tmp_finished_since
        if exists_flag:
            return finished_since
        return None

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
