from heilung.models.action import Action


class CloseConnection(Action):
    """Hinders pathogens to spread between two specified cities via the flightpath for a specified number of rounds
    """

    def __init__(self, from_city, to_city, num_rounds, possible_from_cities=None):
        """Generates on object of this action

        Arguments:
            from_city {City} -- [description]
            to_city {City} -- [description]
            num_rounds {int} -- number of rounds to quarantine the city as a positive integer greater than 0

        Keyword Arguments:
            possible_cities {List[City]} -- List of possible cities to evaluate this event for (default: {None})

        Raises:
            ValueError: num_rounds must be larger than 0
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
        if not isinstance(num_rounds, int) or num_rounds < 1:
            raise ValueError("num_rounds must be int greater or equal to 1!")

        # Init
        action_type = "closeConnection"
        parameters = {"fromCity": from_city.name, "toCity": to_city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        if num_rounds < 1:
            raise ValueError("num_rounds must be greater or equal to 1!")
        return 3 * num_rounds + 3

    @staticmethod
    def get_max_rounds(ava_points):
        return max(int((ava_points - 3) / 3), 0)

    @staticmethod
    def is_possible(game, from_city, num_rounds, to_city=None):
        # "Is possible for this city" + (optionally) "with this specified connection"

        # Tmp var
        open_con = from_city.open_connections
        # Has enough points, and has at least one connection that is not closed
        if game.points >= CloseConnection.get_costs(num_rounds) and open_con:
            # (Optionally) and the specified connection exists
            if to_city and to_city.name not in open_con:
                # Check if not exists and if so return false, else usual return true is used
                return False
            return True
        return False
