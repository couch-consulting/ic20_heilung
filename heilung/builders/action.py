# Action Builder Class - Responsible for creating an output/answer
from heilung.models.actions import EndRound, ApplyHygienicMeasures, ExertInfluence, LaunchCampaign, CallElections, \
    PutUnderQuarantine, CloseAirport, CloseConnection, DevelopVaccine, DeployVaccine, DevelopMedication, \
    DeployMedication
from heilung.models.city import City
import random


class ActionBuilder:
    """ Builder for Actions
    """

    def __init__(self, game):
        self.game = game

    def get_actions(self):
        """
        Builds a list of possible actions that can be performed according to the current game state
        :return: List[Action] - list of actions
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

        # Get Possible DeployVaccine Actions which are still relevant
        if ava_points >= DeployVaccine.get_costs():
            # Can be deployed as long as a city has an outbreak and uninfected citizens are not immune
            # vaccines could be deployed multiple times but this does not affect anything thus is filtered
            potential_pathogen = self.game.get_relevant_pathogens(self.game.pathogens_with_vaccine)
            for pathogen in potential_pathogen:
                # Cities that have the outbreak pathogen but do not have the vaccine deployed already
                possible_cities = [city for city in self.game.get_cities_with_pathogen(pathogen) if
                                   pathogen not in city.deployed_vaccines]
                # if no cities are possible then this is also not a possible action
                if possible_cities:
                    action_list.append(DeployVaccine(default_city, pathogen, possible_cities))

        # Get Possible DeployMedication Actions which are still relevant
        if ava_points >= DeployMedication.get_costs():
            # Can be deployed as long as a city has infected citizens (medication can be deployed multiple times)
            potential_pathogen = self.game.get_relevant_pathogens(self.game.pathogens_with_medication)
            for pathogen in potential_pathogen:
                # if the outbreak/pathogen is gone the prevalence is 0 <==> if the prevalence is 0 the outbreak is gone.
                # Thus only need to check for cities with an outbreak of the given pathogen
                possible_cities = [city for city in self.game.get_cities_with_pathogen(pathogen)]
                if possible_cities:
                    action_list.append(DeployMedication(default_city, pathogen, possible_cities=possible_cities))

        # Written like this in case costs of any of these would change, alternative they could all use the "same" if
        # Here no indication that these happened in the past exists, and so far these do not actually change values of a city
        # Every city is possible
        all_cities = self.game.cities_list
        if ava_points >= ApplyHygienicMeasures.get_costs():
            action_list.append(ApplyHygienicMeasures(default_city, possible_cities=all_cities))
        if ava_points >= CallElections.get_costs():
            action_list.append(CallElections(default_city, possible_cities=all_cities))
        if ava_points >= ExertInfluence.get_costs():
            action_list.append(ExertInfluence(default_city, possible_cities=all_cities))
        if ava_points >= LaunchCampaign.get_costs():
            action_list.append(LaunchCampaign(default_city, possible_cities=all_cities))

        # WARNING
        # The following city specific action can not be filtered further
        # since the game state does not incorporated whether it did took place in previous rounds or is still active
        # Must be solved by the heuristic/action executed by backtracking
        # WARNING

        # All cities with an outbreak
        possible_cities = self.game.cities_infected
        # All cities with an outbreak that have an airport
        alt_pos_cities = [city for city in possible_cities if city not in self.game.cities_without_airport]
        # num_rounds will default to maximum of rounds for available points
        if ava_points >= PutUnderQuarantine.get_costs(1) and possible_cities:
            # possible city for each only cities with an outbreak because any other city would be irrelevant
            action_list.append(PutUnderQuarantine(default_city, PutUnderQuarantine.get_max_rounds(ava_points),
                                                  possible_cities=possible_cities))
        if alt_pos_cities:
            if ava_points >= CloseAirport.get_costs(1):
                action_list.append(CloseAirport(default_city, CloseAirport.get_max_rounds(ava_points),
                                                possible_cities=alt_pos_cities))
            if ava_points >= CloseConnection.get_costs(1):
                action_list.append(
                    CloseConnection(default_city, default_city, CloseConnection.get_max_rounds(ava_points),
                                    possible_from_cities=alt_pos_cities))

        # End Round is always possible
        action_list.append(EndRound())

        return action_list

    @staticmethod
    def random_action(action_list):
        """
        Generate a random action and "fill" values randomly to have a correct action object
        :param action_list: action list created by the function "get_actions"
        :return: JSON of action ready for return to requester
        """

        action = random.choice(action_list)

        if isinstance(action, (DeployVaccine, DeployMedication)):
            action.parameters['city'] = random.choice(action.possible_cities).name
        if isinstance(action, (ApplyHygienicMeasures, CallElections, ExertInfluence, LaunchCampaign)):
            action.parameters['city'] = random.choice(action.possible_cities).name

        # No backtracking, due to the idea that it is possible by randomness to take another action
        # Further, go with random number of rounds between min and max
        if isinstance(action, (PutUnderQuarantine, CloseAirport)):
            action.parameters['city'] = random.choice(action.possible_cities).name
            action.parameters['rounds'] = random.randint(1, action.parameters['rounds'])
        if isinstance(action, CloseConnection):
            from_city = random.choice(action.possible_cities)
            action.parameters['fromCity'] = from_city.name
            # select random to connection
            action.parameters['toCity'] = random.choice(from_city.connections)
            action.parameters['rounds'] = random.randint(1, action.parameters['rounds'])

        return action
