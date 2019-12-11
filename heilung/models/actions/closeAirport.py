from heilung.models.action import Action


class CloseAirport(Action):
    """Hinders pathogens to spread to cities connected via a flightpath for a specified number of rounds

    WARNINGS - !caution when using this action!:
        - Can not be done multiple times on the same city but no event or indicator exists which states that it already happened or sinceRounds!
        - Can only be considered by backtracking
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
            num_rounds = 1

        # Init
        action_type = "closeAirport"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        return 5 * num_rounds + 15

    @staticmethod
    def get_max_rounds(ava_points):
        return (ava_points - 15) / 5
