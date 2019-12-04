# Action Builder Class - Responsible for creating an output/answer
from heilung.models.actions import EndRound, ApplyHygienicMeasures, ExertInfluence, LaunchCampaign, CallElections, \
    PutUnderQuarantine, CloseAirport, CloseConnection, DevelopVaccine, DeployVaccine, DevelopMedication, \
    DeployMedication
from heilung.models.city import City


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
        # Default empty city
        default_city = City("", "", "", "", "", "", "", "", "", [])

        # Get Possible DevelopVaccine Actions which are still relevant (pathogen still exists in at least one city)
        if ava_points >= DevelopVaccine.get_costs():
            for pathogen in self.game.pathogens_in_need_of_vaccine:
                action_list.append(DevelopVaccine(pathogen))

        # Get Possible DevelopMedication Actions which are still relevant
        if ava_points >= DevelopMedication.get_costs():
            for pathogen in self.game.pathogens_in_need_of_medication:
                action_list.append(DevelopMedication(pathogen))

        # TODO add list of possible cities to object and generate in here as well





        # Get Possible DeployVaccine Actions which are still relevant
        if ava_points >= DeployVaccine.get_costs():
            # Can be deployed as long as a city has an outbreak and uninfected citizens are not immune
            potential_pathogen = self.game.get_relevant_pathogens(self.game.pathogens_with_vaccine)
            for pathogen in potential_pathogen:
                # Cities that have the outbreak pathogen but do not have the vaccine deployed
                possible_cities = [city for city in self.game.get_cities_with_pathogen(pathogen) if
                                   pathogen not in city.deployed_vaccines]
                action_list.append(DeployVaccine(default_city, pathogen, possible_cities))

        # Get Possible DeployMedication Actions which are still relevant
        if ava_points >= DeployMedication.get_costs():
            # Can be deployed as long as a city has infected citizens (e.g. has an outbreak)
            potential_pathogen = self.game.get_relevant_pathogens(self.game.pathogens_with_medication)
            for pathogen in potential_pathogen:
                action_list.append(DeployMedication(default_city, pathogen))

        # Written like this in case costs of any of these would change, alternative they could all use the "same" if
        # TODO check if any of these have an event in a city
        if ava_points >= ApplyHygienicMeasures.get_costs():
            action_list.append(ApplyHygienicMeasures(default_city))
        if ava_points >= CallElections.get_costs():
            action_list.append(CallElections(default_city))
        if ava_points >= ExertInfluence.get_costs():
            action_list.append(ExertInfluence(default_city))
        if ava_points >= LaunchCampaign.get_costs():
            action_list.append(LaunchCampaign(default_city))

        # num_rounds will default to maximum of rounds for available points
        # TODO check if any of these generate an even in a city and in how far reusage/usage is possible
        if ava_points >= CloseConnection.get_costs(1):
            action_list.append(CloseConnection(default_city, default_city, CloseConnection.get_max_rounds(ava_points)))
        if ava_points >= CloseAirport.get_costs(1):
            action_list.append(CloseAirport(default_city, CloseAirport.get_max_rounds(ava_points)))
        if ava_points >= PutUnderQuarantine.get_costs(1):
            action_list.append(PutUnderQuarantine(default_city, PutUnderQuarantine.get_max_rounds(ava_points)))

        # End Round is always possible
        action_list.append(EndRound())

        return action_list

        # TODO rethink how far this list can be used or rather the methods in here could be useful for heuristics
