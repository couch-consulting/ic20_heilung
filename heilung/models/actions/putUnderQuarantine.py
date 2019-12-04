from heilung.models.action import Action


class PutUnderQuarantine(Action):
    """Hinders pathogens to spread to any other cities for a specified number of rounds
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
        action_type = "putUnderQuarantine"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, self.get_costs(num_rounds), parameters)

    @staticmethod
    def get_costs(num_rounds):
        return 10 * num_rounds + 20

    @staticmethod
    def get_max_rounds(ava_points):
        return (ava_points - 20) / 10
