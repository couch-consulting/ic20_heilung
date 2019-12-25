from heilung.models.action import Action


class PutUnderQuarantine(Action):
    """Hinders pathogens to spread to any other cities for a specified number of rounds
    """

    def __init__(self, city, num_rounds, possible_cities=None):
        """
        :param city: City object
        :param num_rounds: number of rounds to quarantine the city as a positive integer greater than 0
        """
        if possible_cities is None:
            self.possible_cities = []
        else:
            # filter cities which are already under quarantine
            self.possible_cities = [city for city in possible_cities if not city.under_quarantine]

        # default to 1 round quarantine iff false input for num_rounds
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            raise ValueError("num_rounds must be int greater or equal to 1!")

        # Init
        action_type = "putUnderQuarantine"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        if num_rounds < 1:
            raise ValueError("num_rounds must be greater or equal to 1!")
        return 10 * num_rounds + 20

    @staticmethod
    def get_max_rounds(ava_points):
        return max(int((ava_points - 20) / 10), 0)

    @staticmethod
    def is_possible(game, num_rounds, city):
        # "Is possible for this city"

        # Has enough points, and has an airport at all and this airport is not closed
        if game.points >= PutUnderQuarantine.get_costs(num_rounds) and not city.under_quarantine:
            return True
        return False
