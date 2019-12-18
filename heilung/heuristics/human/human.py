# Human heuristic
from heilung.models import actions, events
from . import h_utils


class Human:
    """
    Human heuristic
    """

    def __init__(self, game):
        self.game = game

    def get_decision(self):

        city_ranks = self.rank_cities()

        print({k: v for k, v in sorted(city_ranks.items(), key=lambda item: item[1], reverse=True)})
        exit()
        return actions.EndRound().build_action()

    def rank_cities(self):
        """
        Create a dict with the name of each city as a key and their rank in this heuristic as a value
        :return:
        """
        rank_dict = {}

        # Get all pathogens which are relevant
        relevant_pathogens = self.game.pathogens_in_cities
        weighted_pathogens = self.reweigh_pathogens(relevant_pathogens)

        # Needed Game data
        biggest_city_pop = self.game.biggest_city.population
        pat_with_med = self.game.pathogens_with_medication
        pat_with_vac = self.game.pathogens_with_vaccine
        pat_with_med_dev = self.game.pathogens__with_developing_medication
        pat_with_vac_dev = self.game.pathogens__with_developing_vaccine

        for city in self.game.cities_list:
            city_rank = 0

            # Get influence of outbreak
            if city.outbreak:
                city_pathogen_name = city.outbreak.pathogen.name
                city_rank += h_utils.compute_pathogen_importance(
                    self.reweigh_pathogen_for_city(city, weighted_pathogens[city_pathogen_name]))
                city_rank += self.compute_since_round_rank(city)
                # prevalence influence
                city_rank += h_utils.percentage_to_num_value(city.outbreak.prevalence)
                # Influence from medication and vaccines
                city_pathogen = city.outbreak.pathogen
                if city_pathogen in pat_with_med:
                    # no need for "and not city.deployed_medication" because multiple deployments may be a good idea
                    city_rank += 1
                elif city_pathogen in pat_with_med_dev:
                    city_rank += -1
                if not city.deployed_vaccines:
                    if city_pathogen in pat_with_vac:
                        city_rank += 1
                    elif city_pathogen in pat_with_vac_dev:
                        city_rank += -1

            # Further influences
            # Influence of population (in contrast to population of the biggest (e.g. highest population) city)
            city_rank += h_utils.percentage_to_num_value(
                h_utils.compute_percentage(biggest_city_pop, city.population), cut=0.05, bias=1)
            # Increase rank if city had no help so far
            if not [True for event_object in h_utils.helpful_events_list() if city.has_event(event_object)]:
                city_rank += 1
            # Store rank in dict
            rank_dict[city.name] = city_rank

        return rank_dict

    def reweigh_pathogen_for_city(self, city, pathogen):
        """
        Reweighs properties of a given pathogen according to the city state
        :param city: city object
        :param pathogen: pathogen object
        :return: reweighed pathogen object
        """
        lethality = pathogen.lethality
        infectivity = pathogen.infectivity
        duration = pathogen.duration
        mobility = pathogen.mobility

        # Tmp vars
        vacc_dep = False

        # Collect city features
        # Anti_vac influence by default small
        if city.has_event(events.AntiVaccinationism):
            anti_vac = 1
        else:
            anti_vac = 0
        # City hygiene got a -2 bias since it is a less important feature
        city_hygiene = max(city.hygiene - 2, 1)
        if city.has_event(events.VaccineDeployed):
            vacc_dep = True
        # Assumption of worst case medication deployment for influence value
        if city.has_event(events.MedicationDeployed):
            med_dep = 1
        else:
            med_dep = 0
        # Take native level of city mobility
        city_mobility = city.mobility

        # Adjust Pathogen dependent on city features
        duration = h_utils.decrease_on_dependency(duration, self.compute_since_round_rank(city))
        mobility = h_utils.increase_on_dependency(mobility, city_mobility)
        if vacc_dep:
            infectivity = 0
        else:
            infectivity = h_utils.increase_on_dependency(infectivity, anti_vac)
            infectivity = h_utils.increase_on_dependency(infectivity, city_hygiene)
            infectivity = h_utils.decrease_on_dependency(infectivity, med_dep)

        # Return pathogen
        pathogen.lethality = lethality
        pathogen.infectivity = infectivity
        pathogen.duration = duration
        pathogen.mobility = mobility

        return pathogen

    def reweigh_pathogens(self, pathogens):
        """
        Reweighs the properties of pathogens according to the game state
        :param pathogens: pathogen object
        :return: dict of pathogen names associated to a reweighed pathogen object
        """

        tmp_dict = {}
        for pathogen in pathogens:
            lethality = pathogen.lethality
            infectivity = pathogen.infectivity
            mobility = pathogen.mobility
            duration = pathogen.duration

            # Scale from the game
            # % of infected citizens for this pathogen - transformed to value in range 1-5
            tmp_num_value = h_utils.percentage_to_num_value(self.game.get_percentage_of_infected(pathogen))
            infectivity = h_utils.increase_on_dependency(infectivity, tmp_num_value)
            lethality = h_utils.increase_on_dependency(lethality, tmp_num_value)
            # % of Immune citizens overall
            tmp_num_value = h_utils.percentage_to_num_value(self.game.get_percentage_of_immune(pathogen))
            infectivity = h_utils.decrease_on_dependency(infectivity, tmp_num_value)

            # Scale in between pathogen properties
            lethality = h_utils.decrease_on_dependency(lethality, duration)
            infectivity = h_utils.increase_on_dependency(infectivity, duration)
            mobility = h_utils.increase_on_dependency(mobility, infectivity)

            # TODO think about further game wide dependencies for pathogen

            # Apply base bias (lethality stays the same)
            infectivity = max(infectivity - 1, 1)
            mobility = max(mobility - 2, 1)
            duration = max(duration - 3, 1)

            pathogen.lethality = lethality
            pathogen.infectivity = infectivity
            pathogen.duration = duration
            pathogen.mobility = mobility
            tmp_dict[pathogen.name] = pathogen

        return tmp_dict

    def compute_since_round_rank(self, city):
        """
        City feature
        :param city: city object
        :return: rank of since round
        """
        # Put sinceRound into contrast of overall rounds and give a value that indicates how long this outbreak exits
        if self.game.round >= 6:  # this feature is only useful when some rounds already passed
            return h_utils.percentage_to_num_value(
                h_utils.compute_percentage(self.game, city.outbreak.sinceRound, inverted=True))
        else:
            return 0
