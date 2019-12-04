from heilung.models.action import Action


class CloseAirport(Action):
    """Hinders pathogens to spread to cities connected via a flightpath for a specified number of rounds
    """

    def __init__(self, city, num_rounds):
        """
        :param city: City object
        :param num_rounds: number of rounds to quarantine the city as a positive integer greater than 0
        """
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
