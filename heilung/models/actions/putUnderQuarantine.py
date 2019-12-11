from heilung.models.action import Action


class PutUnderQuarantine(Action):
    """Hinders pathogens to spread to any other cities for a specified number of rounds

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
            # filter cities which are already under quarantine
            self.possible_cities = [city for city in possible_cities if not city.under_quarantine]

        # default to 1 round quarantine iff false input for num_rounds
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            num_rounds = 1

        # Init
        action_type = "putUnderQuarantine"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        return 10 * num_rounds + 20

    @staticmethod
    def get_max_rounds(ava_points):
        return (ava_points - 20) / 10
