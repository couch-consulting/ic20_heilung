# Human heuristic
from heilung.models import actions, events
from heilung.models.pathogen import Pathogen
from . import h_utils
from .scalegroup import Scalegroup
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

        # Get all pathogens which are relevant and weigh them
        self.relevant_pathogens = self.game.pathogens_in_cities
        self.weighted_pathogens = self.reweigh_pathogens(self.relevant_pathogens)
        self.relevant_pathogens_dict = {pat.name: pat for pat in self.relevant_pathogens}

    def get_decision(self):

        # Simple shortcut to avoid recomputing everything in this case
        # because action list would consist only of this element in the end
        if self.game.points == 0:
            return [actions.EndRound()]  # if decide to add value: (actions.EndRound(), 1.0)

        # Rank of each global action (Scaled to 0-1 whereby most important is 1)
        ranked_global_actions = self.rank_global_actions()

        # Rank of each city (Scaled to 0-1 whereby most important is 1)
        city_ranks = self.rank_cities()

        # Rank of each action per city (Scaled to 0-1 for each city whereby most important = 1)
        ranked_city_actions_per_city = self.rank_actions_for_cities(self.game.cities_list)

        # Sort and print
        # print({k: sorted(ranked_city_actions_per_city[k], key=lambda item: item[1], reverse=True) for k, v in
        #        sorted(city_ranks.items(), key=lambda item: item[1], reverse=True)})

        combined_ranks = h_utils.compute_combined_importance(city_ranks, ranked_city_actions_per_city)
        action_list = self.build_action_list(combined_ranks, ranked_global_actions)

        return action_list

    def rank_global_actions(self):
        """
        Ranks global actions (develop-actions for each pathogen)
        :return: List of Tuples of actions ready to be build and their rank
        """
        # math robustness offset
        VAL = 100

        # Initialize scale group for all pathogens
        global_action_scale = Scalegroup({})
        for pathogen_name, weighted_pathogen in self.weighted_pathogens.items():
            importance = h_utils.compute_pathogen_importance(weighted_pathogen,
                                                             self.relevant_pathogens_dict[pathogen_name]) * VAL
            # Store annotated in scale group
            global_action_scale.sg[pathogen_name + '_dV'] = importance
            global_action_scale.sg[pathogen_name + '_dM'] = importance

            # Apply bias
            global_action_scale.apply_bias(pathogen_name + '_dV', 1)
            global_action_scale.apply_bias(pathogen_name + '_dM', 0.8)

        # Values scale for

        for adapted_pathogen_name, rank in global_action_scale.sg.items():
            name_ending = adapted_pathogen_name[-3:]
            pathogen = self.relevant_pathogens_dict[adapted_pathogen_name[:-3]]

            # Features
            # Both values are rather under guessed - since actual values can not be precisely calculated
            # Further immunity to other pathogens is not regarded and thus values are also different
            total_infected = self.game.get_percentage_of_infected(pathogen)
            total_immune = self.game.get_percentage_of_immune(pathogen)

            medication_state = (pathogen not in self.pat_with_med and pathogen not in self.pat_with_med_dev)
            vaccine_state = (pathogen not in self.pat_with_vac and pathogen not in self.pat_with_vac_dev)

            if name_ending == '_dV':
                if vaccine_state:
                    # vaccine importance
                    # The more mobile the pathogen, the more important to deploy the vaccine
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               pathogen.mobility * global_action_scale.influence_lvl2)
                    # The longer the duration the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               pathogen.duration * global_action_scale.influence_lvl2)
                    # The less lethal the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               (
                                                                       1 - pathogen.lethality) * global_action_scale.influence_lvl2)
                    # The more infective the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               pathogen.infectivity * global_action_scale.influence_lvl2)

                    # The more people are infected the less important is vaccine
                    global_action_scale.decrease_on_dependency(adapted_pathogen_name,
                                                               total_infected * global_action_scale.influence_lvl3)

                    # # The less people are immune the more important is vaccine - TODO change this if vaccine is to dominate
                    # global_action_scale.increase_on_dependency(adapted_pathogen_name,
                    #                                            (1 - total_immune) * global_action_scale.influence_lvl2)

                else:
                    global_action_scale.sg[adapted_pathogen_name] = 0
            else:
                if medication_state:
                    # medication importance:
                    # The less mobile the pathogen, the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               (
                                                                       1 - pathogen.mobility) * global_action_scale.influence_lvl2)
                    # The shorter the duration of the pathogen the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               (
                                                                       1 - pathogen.duration) * global_action_scale.influence_lvl2)
                    # The more lethal the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               pathogen.lethality * global_action_scale.influence_lvl3)
                    # The less infective the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               (
                                                                       1 - pathogen.infectivity) * global_action_scale.influence_lvl2)

                    # The more people are infected the more important is medication
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               total_infected * global_action_scale.influence_lvl3)

                    # # The less people are immune the less-more important is medication, TODO change this if vaccine is to dominate
                    # global_action_scale.increase_on_dependency(adapted_pathogen_name,
                    #                                            total_immune * global_action_scale.influence_lvl2)

                else:
                    global_action_scale.sg[adapted_pathogen_name] = 0

        # Build actions
        result = []
        global_action_scale.rescale()
        for adapted_pathogen_name, rank in global_action_scale.sg.items():
            name_ending = adapted_pathogen_name[-3:]
            pathogen = self.relevant_pathogens_dict[adapted_pathogen_name[:-3]]

            if rank <= 0:
                continue

            if name_ending == '_dV':
                result.append((actions.DevelopVaccine(pathogen), rank))
            else:
                result.append((actions.DevelopMedication(pathogen), rank))

        # Sort results
        if result:
            result.sort(key=lambda x: x[1], reverse=True)
        return result

    def rank_actions_for_cities(self, cities):
        """
        Builds a ranked list of all possible actions
        :param cities: list of cities
        :return: a dict of tuples containing the action ready to build and the rank percentage whereby the key is the name of the city
        """
        action_ranks_per_city = {}

        for city in cities:
            city_name = city.name

            # Get rank of each action
            action_scale = self.rank_actions_of_city(city)

            # Make build ready
            build_ready_actions = self.finalize_actions_of_city(city, action_scale.sg)

            # Add to dict
            action_ranks_per_city[city_name] = build_ready_actions

        return action_ranks_per_city

    def rank_actions_of_city(self, city):
        """
        Returns each possible (without regard to available points) action with a rank
        :param city: city object
        :return: scale group object
        """

        # Action scale group
        tmp_dict = {'reduce_city_mob': 1, 'exert_influence': 1, 'apply_hyg_msr': 1, 'call_elections': 1,
                    'launch_campaign': 1, 'deploy_vaccine': 1, 'deploy_medication': 1}
        action_scale = Scalegroup(tmp_dict)

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
            vac_state = (pathogen in self.pat_with_vac) and pathogen not in city.deployed_vaccines

            # Weigh city mobility - is only relevant when outbreak exists
            # The more mobile the pathogen the more important to reduce its mobility
            action_scale.increase_on_dependency('reduce_city_mob', pathogen.mobility * action_scale.influence_lvl2)
            # The shorter the duration of the pathogen the more important
            action_scale.increase_on_dependency('reduce_city_mob',
                                                (1 - pathogen.duration) * action_scale.influence_lvl3)
            # The lower the population the more important to reduce city mobility
            action_scale.increase_on_dependency('reduce_city_mob', (1 - compared_pop) * action_scale.influence_lvl2)
            # The older the pathogen the less important to reduce its mobility
            action_scale.decrease_on_dependency('reduce_city_mob', outbreak_lifetime * action_scale.influence_lvl3)

            # TODO implement neighbor check with infected and immune % (the higher immune and already infected neighbors the less important reduce city mobility/the less infected or immune the more important)
            # TODO implement hardcode 100% reduction if city very small and high pathogen importance with lwo duration high lethatily

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
                                                    pathogen.lethality * action_scale.influence_lvl3)
                # The less infective the more important
                action_scale.increase_on_dependency('deploy_medication',
                                                    (1 - pathogen.infectivity) * action_scale.influence_lvl2)

                # If anti vacs in city, more important
                action_scale.increase_on_dependency('deploy_medication', int(anti_vac) * action_scale.influence_lvl1)
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

        return action_scale

    def finalize_actions_of_city(self, city, rank_of_actions):
        """
        Finalize a list of action which are ready to be build
        :param city: city object
        :param rank_of_actions: dict with name of action as key and importance percentage as value
        :return: List of Tuples of actions ready to be build and their rank
        """

        # List of ready-to-build actions
        result = []

        if rank_of_actions['deploy_medication'] > 0:
            result.append(
                (actions.DeployMedication(city, city.outbreak.pathogen), rank_of_actions['deploy_medication']))
        if rank_of_actions['deploy_vaccine'] > 0:
            result.append((actions.DeployVaccine(city, city.outbreak.pathogen), rank_of_actions['deploy_vaccine']))

        result.append((actions.ExertInfluence(city), rank_of_actions['exert_influence']))
        result.append((actions.ApplyHygienicMeasures(city), rank_of_actions['apply_hyg_msr']))
        result.append((actions.CallElections(city), rank_of_actions['call_elections']))
        result.append((actions.LaunchCampaign(city), rank_of_actions['launch_campaign']))

        if rank_of_actions['close_connection'][0] > 0:
            num_rounds = rank_of_actions['close_connection'][1]
            to_city = rank_of_actions['close_connection'][2]
            result.append((actions.CloseConnection(city, to_city, num_rounds), rank_of_actions['close_connection'][0]))

        if rank_of_actions['close_airport'][0] > 0:
            num_rounds = rank_of_actions['close_airport'][1]
            result.append((actions.CloseAirport(city, num_rounds), rank_of_actions['close_airport'][0]))

        if rank_of_actions['put_under_quarantine'][0] > 0:
            num_rounds = rank_of_actions['put_under_quarantine'][1]
            result.append((actions.PutUnderQuarantine(city, num_rounds), rank_of_actions['put_under_quarantine'][0]))

        return result

    def rank_cities(self):
        """
        Create a dict with the name of each city as a key and their importance in this heuristic as a value
        :return: dict of importance
        """
        importance_dict = {}

        # Dict to store city specfic pathogen weight

        # Needed Game data
        biggest_city_pop = self.game.biggest_city.population
        cities_list = self.game.cities_list

        # Build scale group
        tmp_scale_group, self.city_weighted_pathogens = self.get_city_sg_and_pathogens(cities_list,
                                                                                       self.weighted_pathogens)
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
        city_scale.rescale()
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
        Computes importance for mobility actions (close_connection, close airport, put under quarantine)
        and modifies action scale group in place
        :param action_scale: action scale object
        :param city: city object
        """
        # TODO revisit after closeness theory is done and adjust how to what to do

        # Get scale of reduce city mob and decide depending on this scale for subactions of city mobility
        # Get and remove reduce city mob
        reduce_mob_rank = action_scale.sg.pop('reduce_city_mob')
        if city.outbreak:
            mobility = city.outbreak.pathogen.mobility
            # Depending on the mobility itself, define the importance of actual actions
            if mobility < 0.25:
                close_connection = reduce_mob_rank
                close_airport = reduce_mob_rank * 0.75
                put_under_quarantine = reduce_mob_rank * 0.5
            elif mobility <= 0.5:
                close_connection = reduce_mob_rank * 0.5
                close_airport = reduce_mob_rank
                put_under_quarantine = reduce_mob_rank * 0.75
            else:
                close_connection = reduce_mob_rank * 0.5
                close_airport = reduce_mob_rank * 0.75
                put_under_quarantine = reduce_mob_rank
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
                to_city = None
                # if empty, no connection are available hence equal to airport closed
                close_connection = close_airport = 0
                put_under_quarantine = put_under_quarantine * 0.6
            else:
                to_city = self.game.cities[sorted_connections[0]]
                close_airport = close_airport * max(1 - (tmp_counter * 0.2), 0)
                put_under_quarantine -= put_under_quarantine * max(1 - (tmp_counter * 0.1), 0)
        # Check if ava_points is enough for an action
        if actions.CloseConnection.get_max_rounds(self.game.points) == 0:
            close_connection = 0
        if actions.CloseAirport.get_max_rounds(self.game.points) == 0:
            close_airport = 0
        if actions.PutUnderQuarantine.get_max_rounds(self.game.points) == 0:
            put_under_quarantine = 0

        # Add to scale group for rescale
        action_scale.sg['close_connection'] = close_connection
        action_scale.sg['close_airport'] = close_airport
        action_scale.sg['put_under_quarantine'] = put_under_quarantine
        action_scale.rescale()

        # Add fully to scale group
        # TODO refactor such actions for closing any connection with any amount of rounds exists with an importance value
        action_scale.sg['close_connection'] = (action_scale.sg['close_connection'], close_connection_rounds, to_city)
        # TODO refactor such that both actions with any amount of round has an importance value
        action_scale.sg['close_airport'] = (action_scale.sg['close_airport'], close_airport_rounds)
        action_scale.sg['put_under_quarantine'] = (action_scale.sg['put_under_quarantine'], put_under_quarantine_rounds)

    def build_action_list(self, sorted_city_action, sorted_global_actions):
        """
        Build a list of actions whereby the first one is the most important action to perform in this round
        :param sorted_city_action: all city specific actions and a rank whereby the highest rank = most important
        :param sorted_global_actions: all possible global actions
        :return: List of tuples of actions and values
        """

        # Tmp vars
        city_with_bio_terrorism = self.game.has_new_bioTerrorism
        ava_points = self.game.points
        saved_points = 0

        # Build up fall back points for bio terrorism
        if self.game.round >= 10:
            ava_points -= 20
            saved_points = 20

        if ava_points <= 0:
            best_action = actions.EndRound()
        # Round 1 Gameplan - special because guaranteed to have 40 points and early in game
        elif self.game.round == 1:
            # Follow up action from previous round 1 steps
            if self.pat_with_med_dev:
                # Guarantees that if medication was chosen to be first action of this round,
                # that afterwards the best city action is chosen
                best_action = self.get_best_city_action(sorted_city_action, ava_points)
            elif ava_points < 40:

                # Follow up logic for candidate city action
                candidate_cities = self.game.duration_candidate_cities
                if candidate_cities:
                    best_action = self.get_action_for_candidate_cities(candidate_cities, ava_points)
                    if not best_action:
                        best_action = actions.EndRound()
                else:
                    # Guarantees that if previously action was to wait 1 round before developing vaccine
                    # that it actually waits after performing the action
                    best_action = actions.EndRound()
            else:
                # Else First action in first round
                # Get all cities in which the mobility must be reduced
                candidate_cities = self.game.duration_candidate_cities
                if candidate_cities:
                    best_action = self.get_action_for_candidate_cities(candidate_cities, ava_points)
                elif isinstance(sorted_global_actions[0][0], actions.DevelopMedication):
                    # If medication most important,develop it - follow up: do some action
                    best_action = sorted_global_actions[0][0]
                else:
                    # only happens if no candidate city
                    # if vaccine is most important, do best action and choose what to develop in the following round
                    # Since global actions are only develop medication or develop vaccine, this else is fine for now
                    # Follow up: end round (wait)
                    best_action = self.get_best_city_action(sorted_city_action, ava_points,
                                                            points_needed=actions.DevelopVaccine.get_costs())

        # Bio Terrorism game plan
        elif city_with_bio_terrorism:
            # Get real number of points to counter bio terrorism attack
            actual_points = saved_points + ava_points
            best_action = self.get_action_for_low_duration_city(city_with_bio_terrorism, actual_points)
            if not best_action:
                best_action = self.get_best_city_action(sorted_city_action, actual_points)

        # Round X Gameplan
        else:
            isolated_cities = []
            for pathogen in self.game.pathogens_in_cities:
                if len(self.game.get_cities_with_pathogen(pathogen)) == 1:
                    # Get new infected or isolated city
                    tmp_city = self.game.get_cities_with_pathogen(pathogen)[0]
                    isolated_cities.append(tmp_city)

            if isolated_cities:
                # Get real number of points to avoid having not isolated cities
                actual_points = saved_points + ava_points
                best_action = self.get_action_for_isolated_cities(isolated_cities, actual_points, sorted_city_action)

            elif not sorted_global_actions:
                # If no global actions anymore, do most important city action
                best_action = self.get_best_city_action(sorted_city_action, ava_points)
            else:
                best_action = self.get_action_for_global_actions(sorted_city_action, sorted_global_actions, ava_points)

        return [best_action]

    def plan_global_action(self, global_action, sorted_city_action, ava_points):
        """
        'Schedules" to return the desired global action, if enough points available, it will be returned immediately
        if not either the round will be ended
        or an action using the points that are not used is played such that next round this action is still possible
        :param global_action: a global action which is ready to be build
        :param sorted_city_action: sorted city action list (tuples of action and importance value)
        :param ava_points: point allowed to use
        :return: action to perform to achieve doing this action now or later
        """
        action = global_action
        # get costs - no need to check other get_costs instances since all global actions have constant costs
        costs = global_action.get_costs()

        # Check if selected global action is possible
        if ava_points < costs:
            # If not, select an action that makes it possible when just waiting next time
            action = self.get_best_city_action(sorted_city_action, ava_points, points_needed=costs)
            # This works because the select action will see that no points to play exists in the 2nd time triggering
            # and thus just ends the round

        return action

    def get_action_for_candidate_cities(self, candidate_cities, points_to_spend):
        """
        Return the best action for cities infected with a low duration pathogen
        :param candidate_cities:
        :param points_to_spend:
        :return:
        """
        # sort for biggest city first
        candidate_cities = sorted(candidate_cities, key=lambda x: x.population, reverse=True)
        # Sort for most important pathogen
        city = sorted(candidate_cities, key=lambda x: h_utils.compute_pathogen_importance(
            self.weighted_pathogens[x.outbreak.pathogen.name], x.outbreak.pathogen))[0]

        return self.get_action_for_low_duration_city(city, points_to_spend)

    def get_action_for_low_duration_city(self, city, points_to_spend):
        max_rounds_for_points = actions.PutUnderQuarantine.get_max_rounds(points_to_spend)
        max_rounds_for_points_airport = actions.CloseAirport.get_max_rounds(points_to_spend)

        if not max_rounds_for_points and not max_rounds_for_points_airport:
            # Nothing possible
            return None

        # No need to check if already closed/under quarantine since first round)
        if city.outbreak.pathogen.infectivity > 0.25:
            # If high infectivity or no airport put under quarantin
            if city.outbreak.pathogen.mobility >= 0.5 or not city.connections:
                if max_rounds_for_points:
                    return actions.PutUnderQuarantine(city, max_rounds_for_points)

                if not city.connections:
                    return None

                return actions.CloseAirport(city, max_rounds_for_points_airport)

            return actions.CloseAirport(city, max_rounds_for_points_airport)

        # else just try to close airport
        if not city.connections:
            # No airport
            if max_rounds_for_points:
                # try quarantine for 1 round
                return actions.PutUnderQuarantine(city, 1)

            # nothing possible
            return None

        return actions.CloseAirport(city, 1)

    def get_action_for_isolated_cities(self, isolated_cities, ava_points, sorted_city_action):
        still_isolated = [city for city in isolated_cities if city.under_quarantine or city.airport_closed]
        no_isolation_present = [city for city in isolated_cities if city not in still_isolated]

        if no_isolation_present:
            # Sort for most important pathogen
            city = sorted(no_isolation_present, key=lambda x: h_utils.compute_pathogen_importance(
                self.weighted_pathogens[x.outbreak.pathogen.name], x.outbreak.pathogen))[0]

            tmp_num_rounds = actions.PutUnderQuarantine.get_max_rounds(ava_points)
            tmp_num_rounds_airport = actions.CloseAirport.get_max_rounds(ava_points)
            if tmp_num_rounds and (city.outbreak.pathogen.mobility >= 0.5 or not city.connections):
                # Put under quarantine possible
                best_action = actions.PutUnderQuarantine(city, tmp_num_rounds)
            elif tmp_num_rounds_airport and city.connections:
                # Close airport possible
                best_action = actions.CloseAirport(city, tmp_num_rounds_airport)
            else:
                best_action = self.get_best_city_action(sorted_city_action, ava_points)
        else:
            # all isolated cities are still isolated
            points_needed_in_future = actions.CloseAirport.get_costs(5)
            for city in still_isolated:
                if city.under_quarantine:
                    points_needed_in_future = actions.PutUnderQuarantine.get_costs(2)
                    break

            if ava_points > points_needed_in_future:
                # more points than needed in future, do something with them
                best_action = self.get_best_city_action(sorted_city_action, ava_points,
                                                        points_needed=points_needed_in_future)
            else:
                # need more points, hence wait for them
                best_action = actions.EndRound()

        return best_action

    def get_action_for_global_actions(self, sorted_city_action, sorted_global_actions, ava_points):
        # Get features needed for decisions below
        # Tmp var for medi or vac is developing for at least one pathogen
        tmp_var_developing = False
        tmp_var_developed = True
        # Tmp var for medi or vac is developing/developed for at least one pathogen
        tmp_var_developing_or_developed = True
        tmp_overall_state_dict = {}
        tmp_developed_state_dict = {}
        for pat_name, state_dict in self.game.pat_state_dict.items():
            developing_state = (state_dict['mDev'] or state_dict['vDev'])
            developed_state = (state_dict['mAva'] or state_dict['vAva'])
            overall_state = (developing_state or developed_state)
            # Save for later
            tmp_developed_state_dict[pat_name] = developed_state
            tmp_overall_state_dict[pat_name] = overall_state
            # Becomes true if at least one is developing
            tmp_var_developing = tmp_var_developing or developing_state
            # Stays true if every pas has either medication or vaccine developed
            tmp_var_developed = tmp_var_developed and developed_state
            # Stays True if every pat has at least medication or vaccine developing or developed
            tmp_var_developing_or_developed = tmp_var_developing_or_developed and overall_state

        if tmp_var_developing:
            # If at least one medication or vaccine is still developing
            if tmp_var_developing_or_developed:
                # and each pathogen has a medication or a vaccine in development or already developed
                # Do best city action
                best_action = self.get_best_city_action(sorted_city_action, ava_points)
            else:
                # and not each pathogen has a medication or a vaccine in development or already developed
                # Do best global action (i.e. develop a medication or vaccine for a so far not considered pathogen
                # Filter out actions for pathogens which are already developing or developed
                filtered_global_actions = [tmp_action for (tmp_action, _) in sorted_global_actions
                                           if not tmp_overall_state_dict[tmp_action.parameters['pathogen']]]
                # Resulting list can not be empty since this would result in the previous if being true, further order is preserved
                # Thus simply get new most important by taking the first one

                best_action = self.plan_global_action(filtered_global_actions[0], sorted_city_action, ava_points)
        else:
            # If non is currently developing
            if not tmp_var_developed:
                # and not each pathogen has either medication or vaccine developed
                filtered_global_actions = [tmp_action for (tmp_action, _) in sorted_global_actions
                                           if not tmp_developed_state_dict[tmp_action.parameters['pathogen']]]
                best_action = self.plan_global_action(filtered_global_actions[0], sorted_city_action, ava_points)
            else:
                # and each pathogen has either medication or vaccine developed

                # [dynamic max] do city action or best global action if last development finished 5 round agao
                # no check for none, it is impossible that this gets executed when no development has finished
                if self.game.last_development_finished_since >= 5:
                    # TODO test other settings or flags here (e.g. importance)
                    best_action = self.plan_global_action(sorted_global_actions[0][0], sorted_city_action, ava_points)
                else:
                    best_action = self.get_best_city_action(sorted_city_action, ava_points)

        return best_action

    def get_best_city_action(self, sorted_action_list, ava_points, points_needed=0):
        """
        Get most important action of a given sorted action list
        and optionally consider how much point shall be available in the future
        :param sorted_action_list: sorted action list (tuples of action and importance value)
        :param points_needed: points needed for an action that is desired to be executed next
        :param ava_points: point allowed to use
        :return: the best possible city action ready to be build
        """

        if ava_points == 0:
            # Impossible to do anything if current amount of points is 0
            # However, currently, this should never become relevant since this case is considered earlier
            return actions.EndRound()

        # Check if desired action for next round exists
        if points_needed == 0:
            return self.select_action_for_points(sorted_action_list, ava_points)

        # Logic for wait "heuristic"
        points_per_round = self.game.points_per_round
        if points_per_round < points_needed:
            # If pointer_per_round < needed points
            if ava_points > points_needed - points_per_round:
                # if pointer_per_round + ava__points > needed_points, spend: ava - (needed - per_round)
                points_to_spend = ava_points - (points_needed - points_per_round)
                return self.select_action_for_points(sorted_action_list, points_to_spend)

            elif points_per_round + ava_points == points_needed:
                # if pointer per round + ava = needed points, end round
                return actions.EndRound()
            elif points_per_round + ava_points < points_needed:
                # if pointer per round + ava < needed_points, check additional_num rounds and if you can execute action right now
                additional_missing_points = abs(ava_points + points_per_round - points_needed)
                additional_num_of_rounds_to_wait = math.ceil(additional_missing_points / points_per_round)
                # Amount of points that are not used while waiting for the points to do the desired action
                too_much_points = additional_num_of_rounds_to_wait * points_per_round - additional_missing_points
                if ava_points >= too_much_points:
                    # If the points, that are going to be too much later, are already available, use them
                    # Simply search for best city action whereby needed points is adapted
                    # As "Next round, only the points that are not too much plus the default points per round are needed"
                    tmp_points_needed = points_per_round + (ava_points - too_much_points)
                    return self.get_best_city_action(sorted_action_list, ava_points, points_needed=tmp_points_needed)
                else:
                    # If the overflow of points does not happen in this round,
                    # the following executions of the code in the next round will catch the points and spend them
                    # Hence we can just end the round here
                    # same case as if we have to wait the num of round and are not allowed to spend any of it
                    return actions.EndRound()

        else:
            # if pointer_per_round >= needed_points, spend all ava_points
            return self.select_action_for_points(sorted_action_list, ava_points)

    def select_action_for_points(self, sorted_action_list, points):
        """
        Logic for spending the specified amount of points
        :param sorted_action_list:
        :param points:
        :return:
        """

        most_important_action = sorted_action_list[0][0]

        # TODO change 1 recalc
        # Basic idea
        if most_important_action.costs <= points or most_important_action.recalculate_costs_for_points(
                points).costs <= points:
            # Do most important if possible
            return most_important_action

        # Recalculate for all actions (only changes the value if it would become possible only due to the adjustment)
        recalc_actions = [(action.recalculate_costs_for_points(points), importance)
                          for (action, importance) in sorted_action_list]
        # Find best possible action in list for points whereby reduce mobility action costs are fitted to ava points
        possible_actions_for_points = [action for (action, importance) in recalc_actions if action.costs <= points]

        if possible_actions_for_points:
            # Return most important of these actions
            return possible_actions_for_points[0]
        else:
            # Not enough points for any action
            return actions.EndRound()

        # TODO improvements:
        # if important dif to nachfolger und nachnachfolger less than 5%/10% each
        # and both would be possible for same or less points do first of them
