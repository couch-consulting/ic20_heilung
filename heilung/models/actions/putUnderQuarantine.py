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
        costs = 10 * num_rounds + 20
        action_type = "putUnderQuarantine"
        parameters = {"city": city.name, "rounds": num_rounds}
        super().__init__(action_type, costs, parameters)
