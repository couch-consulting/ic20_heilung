import networkx as nx

from .city import City


class Game:
    """Models the overall game state
    """

    def __init__(self, state):
        self.round = state['round']
        self.outcome = state['outcome']
        self.points = state['points']
        self.cities = {city[0]: City.from_dict(
            city[0], city[1]) for city in state['cities'].items()}
        self.events = state.setdefault('events', list())
        self.error = state.setdefault('error', '')

        # Create a graph of all connections between cities
        self.connections = nx.Graph()

        self.connections.add_nodes_from(self.cities.keys())

        edges = [(from_city, to_city) for from_city, city in self.cities.items()
                 for to_city in city.connections]
        self.connections.add_edges_from(edges)

    def state_recap(self):
        """
        Help function to get a easily human readable output of the current state (filtered for only infected cities)
        :return: String of the state recap
        """
        overview = "Outcome: %s | Round: %s | Points: %s" % (self.outcome, self.round, self.points)
        error = "Error MSG: %s" % self.error
        game_events = "Game events: %s" % str(self.events)
        infected_cities = "-Infected Cities- \n"
        for city, city.outbreak in self.get_infected_cities_with_outbreak():
            # Build overview of infected city
            outbreak = city.outbreak
            pathogen = city.outbreak.pathogen
            tmp_string = "City Name: %s \n \t SinceRound: %s, Prevalence: %s \n \t Pathogen Name: %s \n \t " \
                         "Infectivity: %s, Mobility: %s, Duration: %s, Lethality: %s \n" % \
                         (city.name, outbreak.sinceRound, outbreak.prevalence, pathogen.name, pathogen.infectivity,
                          pathogen.mobility, pathogen.duration, pathogen.lethality)
            infected_cities = infected_cities + tmp_string

        return "\n".join([overview, error, game_events, infected_cities])

    def get_infected_cities_with_outbreak(self):
        """
        [BASIC IMPLEMENTATION]
        Get a list of all cities in which got an outbreak
        :return: list of city and the outbreak objects
        """
        tmp_list = []
        for _, city in self.cities.items():
            if city.outbreak:
                tmp_list.append([city, city.outbreak])

        return tmp_list

# TODO get list of infected cities
