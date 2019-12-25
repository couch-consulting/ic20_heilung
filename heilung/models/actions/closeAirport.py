from heilung.models.action import Action


class CloseAirport(Action):
    """Hinders pathogens to spread to cities connected via a flightpath for a specified number of rounds
    """

    def __init__(self, city, num_rounds, possible_cities=None):
        """
        :param city: City object
        :param num_rounds: number of rounds to quarantine the city as a positive integer greater than 0
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            # Filter every city in which the airport is already closed
            self.possible_cities = [city for city in possible_cities if not city.airport_closed]

        # default to 1 round quarantine iff false input for num_rounds
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            raise ValueError("num_rounds must be int greater or equal to 1!")

        # Init
        action_type = "closeAirport"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        if num_rounds < 1:
            raise ValueError("num_rounds must be greater or equal to 1!")
        return 5 * num_rounds + 15

    @staticmethod
    def get_max_rounds(ava_points):
        return max(int((ava_points - 15) / 5), 0)

    @staticmethod
    def is_possible(game, num_rounds, city):
        # "Is possible for this city"

        # Has enough points, and has an airport at all and this airport is not closed
        if game.points >= CloseAirport.get_costs(num_rounds) and city.connections and not city.airport_closed:
            return True
        return False
