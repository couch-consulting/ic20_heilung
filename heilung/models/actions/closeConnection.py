from heilung.models.action import Action


class CloseConnection(Action):
    """Hinders pathogens to spread between two specified cities via the flightpath for a specified number of rounds

    WARNINGS - !caution when using this action!:
        - Can not be done multiple times on the same city but no event or indicator exists which states that it already happened or sinceRounds!
        - Can only be considered by backtracking
    """

    def __init__(self, from_city, to_city, num_rounds, possible_from_cities=None):
        """
        :param from_city: City object
        :param to_city: City object
        :param num_rounds: number of rounds to quarantine the city as a positive integer greater than 0
        """
        if possible_from_cities is None:
            self.possible_from_cities = []
        else:
            self.possible_from_cities = possible_from_cities
            # Get a dict with city name as key and possible connections that are not closed as value
            connections_from_city = {city.name: [connection for connection in city.connections if connection
                                                 not in city.closed_connections] for city in possible_from_cities}
            self.connections_from_city = connections_from_city

        # default to 1 round quarantine iff false input for num_rounds
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            num_rounds = 1

        # Init
        action_type = "closeConnection"
        parameters = {"fromCity": from_city.name, "toCity": to_city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        return 3 * num_rounds + 3

    @staticmethod
    def get_max_rounds(ava_points):
        return (ava_points - 3) / 3
