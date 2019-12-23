# Human heuristic
from heilung.models import actions, events
from heilung.models.pathogen import Pathogen
from . import h_utils
from .h_utils import Scalegroup
import copy
import math


class Human:
    """
    Human heuristic
    """

    def __init__(self, game):
        self.original_game = game
        self.game = copy.deepcopy(game)
        self.pat_with_med = self.game.pathogens_with_medication
        self.pat_with_vac = self.game.pathogens_with_vaccine
        self.pat_with_med_dev = self.game.pathogens__with_developing_medication
        self.pat_with_vac_dev = self.game.pathogens__with_developing_vaccine
        self.city_weighted_pathogens = {}
        self.population_of_biggest_city = self.game.biggest_city.population

    def get_decision(self):

        city_ranks = self.rank_cities()
        # print({k: v for k, v in sorted(city_ranks.items(), key=lambda item: item[1], reverse=True)})

        ranked_actions = self.rank_actions_for_cities(city_ranks)
        # print(sorted(ranked_actions, key=lambda x: x[1], reverse=True))

        exit()
        # add heuristic for waiting (e.g. in case something is currently developed and we want to deploy it immediately after)
        # wait heuristic - deicdes to wait

        # logic for if multiple have same prio

        # add logic that might decide on doing 2 things etc - get first fit mäßig (von oben) die meisten punkte, also nehme 1 und 2 wofür du genug punkte hast und gucke ob es eine kombi gibt die mehr punkte hat

        # Default idea - check if top 3 are possible, if not wait
        ava_points = self.game.points
        top_3 = sorted(ranked_actions, key=lambda x: x[1], reverse=True)[:3]
        print(sorted(ranked_actions, key=lambda x: x[1], reverse=True)[:10])
        for action_tuple in top_3:
            action = action_tuple[0]
            if isinstance(action, (actions.PutUnderQuarantine, actions.CloseAirport, actions.CloseConnection)):
                costs = action.get_costs(action.get_max_rounds(ava_points))
            else:
                costs = action.get_costs()

            if ava_points >= costs:
                return action

        return actions.EndRound()

    def rank_actions_for_cities(self, city_ranks):
        """
        Builds a ranked list of all possible actions
        :param city_ranks: dict of city name as key and rank percentage as value
        :return: a list of tuples containing the action ready to build and the rank percentage
        """
        action_ranks = []

        # TODO implement separate ranking for develop meidcation/vaccine

        for city_name, importance_per in city_ranks.items():
            city = self.game.cities[city_name]
            # if city.outbreak:
            #     continue
            tmp_action_ranks = self.rank_actions_of_city(city)
            tmp_var = self.finalize_actions_of_city(city, tmp_action_ranks)

            # Kombiniere mit city rank
            # compute importance of actions? - keep in mind that cities without pathogen have much higher values hence we need to scale most likely

        # # Add global actions to result list
        # for pat_name, action_ranks in development_actions.items():
        #     print(pat_name)
        #     print(action_ranks)
        #     if action_ranks['develop_vaccine'] > 0:
        #         result.append([actions.DevelopVaccine(pat_name, input_is_str=True), action_ranks['develop_vaccine']])
        #     if action_ranks['develop_medication'] > 0:
        #         result.append(
        #             [actions.DevelopMedication(pat_name, input_is_str=True), action_ranks['develop_medication']])
        #
        #

        return action_ranks

    def rank_actions_of_city(self, city):
        """
        Returns each possible (without regard to available points) action with a rank
        :param city: city object
        :return: dict with name of action as key and importance percetnage as value
        """

        # Action scale group
        tmp_dict = {'reduce_city_mob': 1, 'exert_influence': 1, 'apply_hyg_msr': 1, 'call_elections': 1,
                    'launch_campaign': 1, 'deploy_vaccine': 1, 'deploy_medication': 1}
        action_scale = Scalegroup(tmp_dict)

        # Apply base bias - to an extend this represent a predefined gameplan for this city (could be merged with above)
        action_scale.apply_bias('deploy_vaccine', 0.8)
        action_scale.apply_bias('deploy_medication', 0.7)

        action_scale.apply_bias('reduce_city_mob', 0.65)

        action_scale.apply_bias('launch_campaign', 0.5)
        action_scale.apply_bias('exert_influence', 0.5)
        action_scale.apply_bias('apply_hyg_msr', 0.5)
        action_scale.apply_bias('call_elections', 0.5)

        # Pathogen/outbreak rank influence
        if city.outbreak:
            # Collect pathogen values
            pathogen = city.outbreak.pathogen

            # Collect features
            outbreak_lifetime = self.since_round_percentage(city)  # The higher the older
            compared_pop = h_utils.compute_percentage(self.population_of_biggest_city, city.population)
            anti_vac = city.has_event(events.AntiVaccinationism)
            dep_meds = bool(city.deployed_medication)
            med_state = pathogen in self.pat_with_med
            vac_state = (pathogen in self.pat_with_vac) and not city.deployed_vaccines

            # Weigh city mobility - is only relevant when outbreak exists
            # The more mobile the pathogen the more important to reduce its mobility
            action_scale.increase_on_dependency('reduce_city_mob', pathogen.mobility * action_scale.influence_lvl2)
            # The shorter the duration of the pathogen the more important
            action_scale.increase_on_dependency('reduce_city_mob',
                                                (1 - pathogen.duration) * action_scale.influence_lvl3)
            # The lower the population the more important to reduce city mobility
            action_scale.increase_on_dependency('reduce_city_mob', (1 - compared_pop) * action_scale.influence_lvl3)
            # The older the pathogen the less important to reduce its mobility
            action_scale.decrease_on_dependency('reduce_city_mob', outbreak_lifetime * action_scale.influence_lvl3)
            # TODO implement neighbor check with infected and immune % (the higher immune and already infected neighbors the less important reduce city mobility/the less infected or immune the more important)

            # Weigh Vaccine
            if vac_state:
                # The more mobile the pathogen, the more important to deploy the vaccine
                action_scale.increase_on_dependency('deploy_vaccine', pathogen.mobility * action_scale.influence_lvl2)
                # The longer the duration the more important
                action_scale.increase_on_dependency('deploy_vaccine', pathogen.duration * action_scale.influence_lvl2)
                # The less lethal the more important
                action_scale.increase_on_dependency('deploy_vaccine',
                                                    (1 - pathogen.lethality) * action_scale.influence_lvl2)
                # The more infective the more important
                action_scale.increase_on_dependency('deploy_vaccine',
                                                    pathogen.infectivity * action_scale.influence_lvl2)

                # If no anti vacs in city, more important
                action_scale.increase_on_dependency('deploy_vaccine', int(not anti_vac) * action_scale.influence_lvl1)
                # If med already deployed in city, more important
                action_scale.increase_on_dependency('deploy_vaccine', int(dep_meds) * action_scale.influence_lvl2)
            else:
                # In case the vaccine is not yet developed
                action_scale.sg['deploy_vaccine'] = 0

            # Medication Ranking
            if med_state:
                # The less mobile the pathogen, the more important
                action_scale.increase_on_dependency('deploy_medication',
                                                    (1 - pathogen.mobility) * action_scale.influence_lvl2)
                # The shorter the duration of the pathogen the more important
                action_scale.increase_on_dependency('deploy_medication',
                                                    (1 - pathogen.duration) * action_scale.influence_lvl2)
                # The more lethal the more important
                action_scale.increase_on_dependency('deploy_medication',
                                                    pathogen.lethality * action_scale.influence_lvl2)
                # The less infective the more important
                action_scale.increase_on_dependency('deploy_medication',
                                                    (1 - pathogen.infectivity) * action_scale.influence_lvl2)

                # If anti vacs in city, more important
                action_scale.increase_on_dependency('deploy_vaccine', int(anti_vac) * action_scale.influence_lvl1)
                # For each time medication was already deployed, reduce importance
                action_scale.decrease_on_dependency('deploy_medication',
                                                    len(city.deployed_medication) * action_scale.influence_lvl3)
            else:
                # In case the medication is not yet developed
                action_scale.sg['deploy_medication'] = 0
        else:
            action_scale.sg['deploy_vaccine'] = 0
            action_scale.sg['deploy_medication'] = 0

        # 3-er Actions rank influences
        action_scale.increase_on_dependency('exert_influence',
                                            int(city.has_event(events.EconomicCrisis)) * action_scale.influence_lvl1)
        action_scale.decrease_on_dependency('exert_influence',
                                            int(city.has_event(events.InfluenceExerted)) * action_scale.influence_lvl2)
        action_scale.increase_on_dependency('exert_influence', (1 - city.economy) * action_scale.influence_lvl2)

        action_scale.increase_on_dependency('call_elections',
                                            int(city.has_event(events.LargeScalePanic)) * action_scale.influence_lvl1)
        action_scale.increase_on_dependency('call_elections',
                                            int(city.has_event(events.Uprising)) * action_scale.influence_lvl1)
        action_scale.decrease_on_dependency('call_elections',
                                            int(city.has_event(events.ElectionsCalled)) * action_scale.influence_lvl2)
        action_scale.increase_on_dependency('call_elections', (1 - city.government) * action_scale.influence_lvl2)

        action_scale.increase_on_dependency('launch_campaign', (1 - city.awareness) * action_scale.influence_lvl2)
        # higher decrease because event makes it to higher categorical value by default
        action_scale.decrease_on_dependency('launch_campaign',
                                            int(city.has_event(events.CampaignLaunched)) * action_scale.influence_lvl3)

        action_scale.increase_on_dependency('apply_hyg_msr', int(
            city.has_event(events.AntiVaccinationism)) * action_scale.influence_lvl1)
        # higher decrease because event makes it to higher categorical value by default
        action_scale.decrease_on_dependency('apply_hyg_msr', int(
            city.has_event(events.HygienicMeasuresApplied)) * action_scale.influence_lvl3)
        action_scale.increase_on_dependency('apply_hyg_msr', (1 - city.hygiene) * action_scale.influence_lvl2)
        if city.outbreak:
            action_scale.increase_on_dependency('apply_hyg_msr',
                                                (1 - city.outbreak.prevalence) * action_scale.influence_lvl2)
            action_scale.increase_on_dependency('apply_hyg_msr',
                                                city.outbreak.pathogen.infectivity * action_scale.influence_lvl2)

        # Rank actual mobility actions and readjust (e.g. check if possible) based on game state
        # Further, 3er action need no adjustment - all are possible - and medication/vaccine already done above
        self.readjust_mobility_actions(action_scale, city)  # adjusts action_scale object in palce

        return action_scale.sg

    def finalize_actions_of_city(self, city, action_ranks):
        """
        Finalize a list of action which are ready to be build
        :param city: city object
        :param action_ranks: rank of each action for the given city object
        :return: List of actions ready to be build
        """
        # Build actions - own function later
        # List of ready-to-build actions
        result = []
        # city unspecific book keeping of actions - e.g. for development of vaccine or medication
        development_actions = {}

        development_actions[pathogen.name] = {'develop_vaccine': 0, 'develop_medication': 0}

        # Füge an glboal action ranks hinzu (e.g. wegen develop zeug)

        # Add to result list with city offset
        if deploy_medication > 0:
            result.append([actions.DeployMedication(city, pathogen), deploy_medication + rank])
        if deploy_vaccine > 0:
            result.append([actions.DeployVaccine(city, pathogen), deploy_vaccine + rank])

        # Only save the highest rank for global action
        if develop_medication > 0 and development_actions[pathogen.name]['develop_medication'] < (
                develop_medication + rank):
            development_actions[pathogen.name]['develop_medication'] = develop_medication + rank
        if develop_vaccine > 0 and development_actions[pathogen.name]['develop_vaccine'] < (
                develop_vaccine + rank):
            development_actions[pathogen.name]['develop_vaccine'] = develop_vaccine + rank

        result.append([actions.ExertInfluence(city), exert_influence + reduced_rank])
        result.append([actions.ApplyHygienicMeasures(city), apply_hyg_msr + reduced_rank])
        result.append([actions.CallElections(city), call_elections + reduced_rank])
        result.append([actions.LaunchCampaign(city), launch_campaign + reduced_rank])

        if close_connection > 0:
            num_rounds = actions.CloseConnection.get_max_rounds(self.game.points)

        if close_airport > 0:
            num_rounds = actions.CloseAirport.get_max_rounds(self.game.points)
            result.append([actions.CloseAirport(city, num_rounds), close_airport + rank])
        if put_under_quarantine > 0:
            num_rounds = actions.PutUnderQuarantine.get_max_rounds(self.game.points)
            result.append([actions.PutUnderQuarantine(city, num_rounds), put_under_quarantine + rank])


    def rank_cities(self):
        """
        Create a dict with the name of each city as a key and their importance in this heuristic as a value
        :return: dict of importance
        """
        importance_dict = {}

        # Get all pathogens which are relevant
        relevant_pathogens = self.game.pathogens_in_cities
        weighted_pathogens = self.reweigh_pathogens(relevant_pathogens)

        # Dict to store city specfic pathogen weight

        # Needed Game data
        biggest_city_pop = self.game.biggest_city.population
        cities_list = self.game.cities_list

        # Build scale group
        tmp_scale_group, self.city_weighted_pathogens = self.get_city_sg_and_pathogens(cities_list, weighted_pathogens)
        city_scale = Scalegroup(tmp_scale_group)

        for city in cities_list:
            name = city.name

            # Get influence of outbreak
            if city.outbreak:
                # The older the outbreak the more important the city to cure since deaths are closer
                city_scale.increase_on_dependency(name, self.since_round_percentage(city) * city_scale.influence_lvl2)

                # The higher the actually infected people in the city the more important the city
                compared_pop_infected_per = h_utils.compute_percentage(biggest_city_pop,
                                                                       city.outbreak.prevalence * city.population)
                city_scale.increase_on_dependency(name, compared_pop_infected_per * city_scale.influence_lvl3)

                if city.outbreak.pathogen in self.pat_with_med or city.outbreak.pathogen in self.pat_with_vac:
                    # If medication or vaccine is available for this city, is shall become more important
                    city_scale.increase_on_dependency(name, city_scale.influence_lvl1)
                if not city.deployed_vaccines:
                    # When the city was yet not made immune it gets more important
                    city_scale.increase_on_dependency(name, city_scale.influence_lvl2)

            # Influence of population (in contrast to population of the biggest (e.g. highest population) city)
            compared_pop_per = h_utils.compute_percentage(biggest_city_pop, city.population)
            city_scale.increase_on_dependency(name, compared_pop_per * city_scale.influence_lvl2)

            # Increase importance if city had no help so far
            if not [True for event_object in h_utils.helpful_events_list() if city.has_event(event_object)]:
                city_scale.increase_on_dependency(name, city_scale.influence_lvl1)

        # Build dict
        for city_name, importance_per in city_scale.sg.items():
            importance_dict[city_name] = importance_per

        return importance_dict

    def get_city_sg_and_pathogens(self, cities_list, weighted_pathogens):
        """
        Initializes the scale group and collects the city specif pathogen weight
        :param cities_list: list of city objects
        :param weighted_pathogens: dict of overall weighted pathogens
        :return: initialized scale group as dict, city specific pathogen weights as dict
        """
        # Higher value for percentage for numerical robustness
        default_value = 100000000000000
        # TODO rethink this approach to define the base importance and make it numerically robuster

        # Build scale group
        tmp_scale_group = {}
        city_weighted_pathogens = {}
        for city in cities_list:
            # Default initialize all cities with rank equal to 100% or 100% + % of pathogen
            if city.outbreak:
                pathogen = self.reweigh_pathogen_for_city(city, weighted_pathogens[city.outbreak.pathogen.name])
                city_weighted_pathogens[city.name] = pathogen
                tmp_scale_group[city.name] = default_value + (
                        default_value * h_utils.compute_pathogen_importance(pathogen, city.outbreak.pathogen))
            else:
                tmp_scale_group[city.name] = default_value

        return tmp_scale_group, city_weighted_pathogens

    def reweigh_pathogen_for_city(self, city, pathogen):
        """
        Reweighs properties of a given pathogen according to the city state
        :param city: city object
        :param pathogen: pathogen object
        :return: reweighed pathogen object
        """
        pat_scale = Scalegroup({'lethality': pathogen.lethality, 'infectivity': pathogen.infectivity,
                                'mobility': pathogen.mobility, 'duration': pathogen.duration})
        # Collect city features
        anti_vac = city.has_event(events.AntiVaccinationism)
        vacc_dep = bool(city.deployed_vaccines)
        med_dep = bool(city.deployed_medication)
        city_hyg = city.hygiene

        # The higher the more mobile
        city_mob = city.mobility
        # The higher the longer the outbreak is alive
        outbreak_lifetime = self.since_round_percentage(city)

        # If outbreak_lifetime exists longer then the the duration becomes more important because kill-roll is sooner
        pat_scale.increase_on_dependency('duration', outbreak_lifetime * pat_scale.influence_lvl2)
        # Increase mobility of the city, increases mobility of the pathogen
        pat_scale.increase_on_dependency('mobility', city_mob * pat_scale.influence_lvl2)

        if vacc_dep:
            pat_scale.sg['infectivity'] = 0
        else:
            pat_scale.increase_on_dependency('infectivity', int(anti_vac) * pat_scale.influence_lvl1)
            pat_scale.decrease_on_dependency('infectivity', city_hyg * pat_scale.influence_lvl2)
            pat_scale.decrease_on_dependency('infectivity', int(med_dep) * pat_scale.influence_lvl2)

        # Return pathogen
        return Pathogen(pathogen.name, pat_scale.sg['infectivity'], pat_scale.sg['mobility'],
                        pat_scale.sg['duration'], pat_scale.sg['lethality'], transformation=False)

    def reweigh_pathogens(self, pathogens):
        """
        Reweighs the properties of pathogens according to the game state
        :param pathogens: pathogen object
        :return: dict of pathogen names associated to a reweighed pathogen object
        """

        tmp_dict = {}
        for pathogen in pathogens:
            pat_scale = Scalegroup({'lethality': 1, 'infectivity': 1,
                                    'mobility': 1, 'duration': 1})

            # Apply base bias (lethality stays the same)
            pat_scale.apply_bias('infectivity', 0.9)
            pat_scale.apply_bias('mobility', 0.7)
            pat_scale.apply_bias('duration', 0.6)

            # Collect Game Feature
            infected_citz = self.game.get_percentage_of_infected(pathogen)
            immune_citz = self.game.get_percentage_of_immune(pathogen)

            # Influences
            pat_scale.increase_on_dependency('infectivity', infected_citz * pat_scale.influence_lvl3)
            pat_scale.increase_on_dependency('lethality', infected_citz * pat_scale.influence_lvl3)
            pat_scale.decrease_on_dependency('infectivity', immune_citz * pat_scale.influence_lvl3)
            pat_scale.increase_on_dependency('mobility', pathogen.infectivity * pat_scale.influence_lvl3)
            # Infectivity is more important the longer the duration
            pat_scale.increase_on_dependency('infectivity', pathogen.duration * pat_scale.influence_lvl3)
            # The shorter the duration the more important is lethality, since duration currently has 100% := long, inverted is needed
            pat_scale.increase_on_dependency('lethality', pathogen.duration * pat_scale.influence_lvl3, inverted=True)

            tmp_dict[pathogen.name] = Pathogen(pathogen.name, pat_scale.sg['infectivity'], pat_scale.sg['mobility'],
                                               pat_scale.sg['duration'], pat_scale.sg['lethality'],
                                               transformation=False)

        return tmp_dict

    def since_round_percentage(self, city, inverted=True):
        """
        Computes a percentage equal to how old or new a round is
        :param city: city object
        :param inverted: if true, 100% equals old, if false 100% equal new
        :return: percentage of how old or new a round is
        """
        # Put sinceRound into contrast of overall rounds and give a value that indicates how long this outbreak exits
        if self.game.round >= 6:  # this feature is only useful when some rounds already passed
            return h_utils.compute_percentage(self.game.round, city.outbreak.sinceRound, inverted=inverted)
        else:
            return 0

    def readjust_mobility_actions(self, action_scale, city):
        """
        Computes importance for mobility actions (close_connection, close airport, put underquarantine)
        and modifes action scale group in place
        :param action_scale: action scale object
        :param city: city object
        """
        # TODO revisit after closeness theory is done and adjust how to what to do

        # Get scale of reduce city mob and decide depending on this scale for subactions of city mobility
        # Get and remove reduce city mob
        reduce_mob_rank = action_scale.sg.pop('reduce_city_mob')
        tmp_per = h_utils.compute_percentage(action_scale.max_val, reduce_mob_rank)
        # Depending on the importance of this action group, define the importance of actual actions
        if tmp_per <= 0.25:
            close_connection = reduce_mob_rank
            close_airport = reduce_mob_rank * 0.75
            put_under_quarantine = reduce_mob_rank * 0.5
        elif tmp_per <= 0.6:
            close_connection = reduce_mob_rank * 0.5
            close_airport = reduce_mob_rank
            put_under_quarantine = reduce_mob_rank * 0.75
        else:
            close_connection = reduce_mob_rank * 0.5
            close_airport = reduce_mob_rank * 0.75
            put_under_quarantine = reduce_mob_rank

        # Get rounds for actions - TODO add num of rounds heuristic for actions - for now default to max
        close_connection_rounds = actions.CloseConnection.get_max_rounds(self.game.points)
        close_airport_rounds = actions.CloseAirport.get_max_rounds(self.game.points)
        put_under_quarantine_rounds = actions.PutUnderQuarantine.get_max_rounds(self.game.points)

        # Readjust in case of impossibility
        # Check if connections exists
        sorted_connections = []
        if city.connections:
            # Close connection heuristic for to_city (if connections exists, else set to zero)
            sorted_connections = self.game.get_connections_sorted_for_highest_population_first(city)
            to_city = self.game.cities[sorted_connections[0]]
        else:
            close_connection = 0
            to_city = None
        # Check if any action did already happen
        if city.under_quarantine:
            # If city is under quarantine every mobility action becomes irrelevant
            close_connection = close_airport = put_under_quarantine = 0
        elif city.airport_closed:
            # If airports are already closed closing anything further become 0 while quarantine just gets less important
            close_connection = close_airport = 0
            put_under_quarantine = put_under_quarantine * 0.6
        elif city.closed_connections:
            tmp_counter = 0
            for closed_con in city.closed_connections:
                # For each closed connection reduce rank of others and remove from valid connection
                tmp_counter += 1
                sorted_connections.remove(closed_con)

            if not sorted_connections:
                # if empty, no connection are available hence equal to airport closed
                close_connection = close_airport = 0
                put_under_quarantine = put_under_quarantine * 0.6
            else:
                close_airport = close_airport * max(1 - (tmp_counter * 0.2), 0)
                put_under_quarantine -= put_under_quarantine * max(1 - (tmp_counter * 0.1), 0)
        # Check if ava_points is enough for an action
        if actions.CloseConnection.get_max_rounds(self.game.points) == 0:
            close_connection = 0
        if actions.CloseAirport.get_max_rounds(self.game.points) == 0:
            close_airport = 0
        if actions.PutUnderQuarantine.get_max_rounds(self.game.points) == 0:
            put_under_quarantine = 0

        # Add to scale group
        # TODO refactor such actions for closing any connection with any amount of rounds exists with an importance value
        action_scale.sg['close_connection'] = (close_connection, close_connection_rounds, to_city)
        # TODO refactor such that both actions with any amount of round has an importance value
        action_scale.sg['close_airport'] = (close_airport, close_airport_rounds)
        action_scale.sg['put_under_quarantine'] = (put_under_quarantine, put_under_quarantine_rounds)
