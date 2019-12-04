# Action Builder Class - Responsible for creating an output/answer
from heilung.models.actions import EndRound, ApplyHygienicMeasures, ExertInfluence, LaunchCampaign, CallElections, \
    PutUnderQuarantine, CloseAirport, CloseConnection, DevelopVaccine, DeployVaccine, DevelopMedication, \
    DeployMedication


class ActionBuilder:
    """ Builder for Actions
    """

    def __init__(self, game):
        self.game = game

    def get_actions(self):  # -> List[]
        """
        Builds a list of possible actions that can be performed according to the current game state
        :return:
        """
        ava_points = self.game.points
        action_list = []

        # Get Possible DevelopVaccine Actions which are still relevant (pathogen still exists in at least one city)
        if ava_points >= DevelopVaccine.get_costs():
            for pathogen in self.game.pathogens_in_need_of_vaccine:
                action_list.append(DevelopVaccine(pathogen))

        # Get Possible DevelopMedication Actions which are still relevant (pathogen still exists in at least one city)
        if ava_points >= DevelopMedication.get_costs():
            for pathogen in self.game.pathogens_in_need_of_medication:
                action_list.append(DevelopMedication(pathogen))

        # End Round is always possible
        action_list.append(EndRound())

        return action_list

        # Do for ApplyHygienicMeasures, ExertInfluence, LaunchCampaign, CallElections, PutUnderQuarantine,
        # CloseAirport, CloseConnection, DeployVaccine, DevelopMedication, DeployMedication

    def check_costs(self, costs):
        """
        Check costs of action against available points
        :param costs: integer of costs
        :return: False/True
        """
        if self.available_points < costs:
            return False
        else:
            return True

    def adapt_points(self, costs):
        """
        Adapt available points for internal round data and check if action even possible
        :param costs: integer of costs
        """
        if not self.check_costs(costs):
            raise ValueError(
                "Insufficient funds")  # TODO Raise or Return own error object for self-healing/defaulting?

        self.available_points = self.available_points - costs
