from heilung.models.action import Action


class CloseConnection(Action):
    """Hinders pathogens to spread between two specified cities via the flightpath for a specified number of rounds
    """

    def __init__(self, from_city, to_city, num_rounds):
        """
        :param from_city: City object
        :param to_city: City object
        :param num_rounds: number of rounds to quarantine the city as a positive integer greater than 0
        """
        # default to 1 round quarantine iff false input for num_rounds
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            num_rounds = 1

        # Init
        costs = 3 * num_rounds + 3
        action_type = "closeConnection"
        parameters = {"fromCity": from_city.name, "toCity": to_city.name, "rounds": num_rounds}
        super().__init__(action_type, costs, parameters)
