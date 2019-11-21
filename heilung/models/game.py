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

        # Create a graph of all connections between cities
        self.connections = nx.Graph()

        self.connections.add_nodes_from(self.cities.keys())

        edges = [(from_city, to_city) for from_city, city in self.cities.items()
                 for to_city in city.connections]
        self.connections.add_edges_from(edges)
