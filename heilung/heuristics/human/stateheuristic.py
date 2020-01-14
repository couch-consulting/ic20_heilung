from . import h_utils
from .scalegroup import Scalegroup
from . import scalegroup
from heilung.models import actions, events
from heilung.models.pathogen import Pathogen


class Stateheuristic:
    """
    Heuristic for the current game state for the human heuristic
    """

    def __init__(self, game):
        self.game = game

        # Get all pathogens which are relevant
        self.relevant_pathogens = self.game.pathogens_in_cities
        self.relevant_pathogens_dict = {pat.name: pat for pat in self.relevant_pathogens}
        # Weigh relevant pathogens and store in a dict
        self.weighted_pathogens = self.reweigh_pathogens()
        # Reweigh the pathogen for each city they are in
        self.city_weighted_pathogens = self.reweigh_pathogen_for_city()
        # Store for a feature that is needed later
        self.dev_needed = {}

    # Global Action Heuristic
    def rank_global_actions(self):
        """
        Ranks global actions (develop-actions for each pathogen)
        :return: List of Tuples of actions ready to be build and their rank
        """
        # Initialize scale group for all pathogens
        global_action_scale = scalegroup.init_global_action_sg(self.weighted_pathogens, self.relevant_pathogens_dict)

        # Scale values
        for adapted_pathogen_name, rank in global_action_scale.sg.items():
            name_ending = adapted_pathogen_name[-3:]
            pathogen = self.relevant_pathogens_dict[adapted_pathogen_name[:-3]]

            # Features
            medication_state = (pathogen not in self.game.pathogens_with_medication
                                and pathogen not in self.game.pathogens__with_developing_medication)
            vaccine_state = (pathogen not in self.game.pathogens_with_vaccine
                             and pathogen not in self.game.pathogens__with_developing_vaccine)

            if name_ending == '_dV':
                if vaccine_state:
                    # vaccine importance

                    # The longer the duration the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, pathogen.duration
                                                               * global_action_scale.influence_lvl2)
                    # The less lethal the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, (1 - pathogen.lethality)
                                                               * global_action_scale.influence_lvl2)

                    # More important the higher or the lower it is but not really in between thus formula: 4(x-0.5)^2
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               max(4 * (pathogen.mobility - 0.5) ** 2, 0.25)
                                                               * global_action_scale.influence_lvl2)

                    # The less infective the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, (1 - pathogen.infectivity)
                                                               * global_action_scale.influence_lvl2)

                    # If the pathogen is only in one city or only one pathogen is overall relevant, increase importance
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               int((len(self.game.pathogens_in_cities) == 1) or (len(
                                                                   self.game.get_cities_with_pathogen(pathogen)) == 1))
                                                               * global_action_scale.influence_lvl2)
                else:
                    global_action_scale.sg[adapted_pathogen_name] = 0
            else:
                if medication_state:
                    # medication importance:

                    # The shorter the duration of the pathogen the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, (1 - pathogen.duration)
                                                               * global_action_scale.influence_lvl2)
                    # The more lethal the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, pathogen.lethality
                                                               * global_action_scale.influence_lvl3)

                    # The less mobile the pathogen, the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name,
                                                               (1 - pathogen.mobility)
                                                               * global_action_scale.influence_lvl2)

                    # The more infective the more important
                    global_action_scale.increase_on_dependency(adapted_pathogen_name, pathogen.infectivity
                                                               * global_action_scale.influence_lvl2)

                else:
                    global_action_scale.sg[adapted_pathogen_name] = 0

        return self.finalize_global_actions(global_action_scale)

    def finalize_global_actions(self, global_action_scale):
        """
        Makes a scalegroup of global actions build ready
        :param global_action_scale: created by rank global actions
        :return: List of Tuples of actions ready to be build and their rank
        """
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

    # City Specific Actions Heuristic
    def rank_actions_for_cities(self):
        """
        Builds a ranked list of all possible actions
        :return: {city_name: (action, rank), ...}
        """
        action_ranks_per_city = {}

        for city in self.game.cities_list:
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
            outbreak_lifetime = h_utils.since_round_percentage(self.game.round, city)  # The higher the older
            compared_pop = h_utils.compute_percentage(self.game.biggest_city.population, city.population)
            anti_vac = city.has_event(events.AntiVaccinationism)
            dep_meds = bool(city.deployed_medication)
            med_state = pathogen in self.game.pathogens_with_medication
            vac_state = (pathogen in self.game.pathogens_with_vaccine) and pathogen not in city.deployed_vaccines

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

            # TODO: Possible new feature - average prevalence of neighbors and what pathogen they have

            # Weigh Vaccine
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

            # Increase if low prev
            action_scale.increase_on_dependency('deploy_vaccine',
                                                (1 - city.outbreak.prevalence) * action_scale.influence_lvl3)

            # Medication Ranking
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
            # For each time medication was already deployed, reduce importance (hard cap 5 times in one city)
            action_scale.decrease_on_dependency('deploy_medication',
                                                len(city.deployed_medication) / 5 * action_scale.influence_lvl3)
            # Increase if high prev
            action_scale.increase_on_dependency('deploy_medication',
                                                city.outbreak.prevalence * action_scale.influence_lvl3)
            tmp_val = action_scale.sg['deploy_vaccine']

            if not vac_state:
                if action_scale.sg['deploy_vaccine'] > action_scale.sg['deploy_medication']:
                    # Counts how often vaccine was needed but not developed
                    self.dev_needed[pathogen.name] = self.dev_needed.get(pathogen.name, 0) + 1

                # In case the vaccine is not yet developed
                action_scale.sg['deploy_vaccine'] = 0

            if not med_state:
                if action_scale.sg['deploy_medication'] > tmp_val:
                    self.dev_needed[pathogen.name] = self.dev_needed.get(pathogen.name, 0) + 1

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
        self.readjust_mobility_actions(action_scale, city)  # adjusts action_scale object in place

        return action_scale

    def readjust_mobility_actions(self, action_scale, city):
        """
        Computes importance for mobility actions (close_connection, close airport, put under quarantine)
        and modifies action scale group in place
        :param action_scale: action scale object
        :param city: city object
        """

        # Get scale of reduce city mob and decide depending on this scale for subactions of city mobility
        # Get and remove reduce city mob
        reduce_mob_rank = action_scale.sg.pop('reduce_city_mob')

        # Bias
        close_connection = reduce_mob_rank * 0.5
        close_airport = reduce_mob_rank * 0.75
        put_under_quarantine = reduce_mob_rank

        # Get rounds for actions - default to max since gameplan handles this
        close_connection_rounds = actions.CloseConnection.get_max_rounds(self.game.points)
        # Max possible round number is 5 and 2 because for these numbers you can always repeat the action when its done
        close_airport_rounds = min(actions.CloseAirport.get_max_rounds(self.game.points), 5)
        put_under_quarantine_rounds = min(actions.PutUnderQuarantine.get_max_rounds(self.game.points), 2)

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
        if not actions.CloseConnection.get_max_rounds(self.game.points):
            close_connection = 0
        if not actions.CloseAirport.get_max_rounds(self.game.points):
            close_airport = 0
        if not actions.PutUnderQuarantine.get_max_rounds(self.game.points):
            put_under_quarantine = 0

        # Add to scale group for rescale
        action_scale.sg['close_connection'] = close_connection
        action_scale.sg['close_airport'] = close_airport
        action_scale.sg['put_under_quarantine'] = put_under_quarantine
        action_scale.rescale()

        # Add fully to scale group
        action_scale.sg['close_airport'] = (action_scale.sg['close_airport'], close_airport_rounds)
        action_scale.sg['put_under_quarantine'] = (action_scale.sg['put_under_quarantine'], put_under_quarantine_rounds)
        # TODO: Possible improvement: Add actions for closing any connection
        action_scale.sg['close_connection'] = (action_scale.sg['close_connection'], close_connection_rounds, to_city)

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

    # City Heuristic
    def rank_cities(self):
        """
        Create a dict with the name of each city as a key and their importance in this heuristic as a value
        :return: dict of importance
        """
        importance_dict = {}

        # Dict to store city specific pathogen weight

        # Needed Game data
        biggest_city_pop = self.game.biggest_city.population
        cities_list = self.game.cities_list

        # Initialize scale group
        city_scale = scalegroup.init_city_sg(cities_list, self.city_weighted_pathogens)

        for city in cities_list:
            name = city.name

            # Get influence of outbreak
            if city.outbreak:
                # The older the outbreak the more important the city to cure since deaths are closer
                city_scale.increase_on_dependency(name, h_utils.since_round_percentage(self.game.round, city)
                                                  * city_scale.influence_lvl2)

                # The higher the actually infected people in the city the more important the city
                compared_pop_infected_per = h_utils.compute_percentage(biggest_city_pop,
                                                                       city.outbreak.prevalence * city.population)
                city_scale.increase_on_dependency(name, compared_pop_infected_per * city_scale.influence_lvl3)

                if city.outbreak.pathogen in self.game.pathogens_with_medication \
                        or city.outbreak.pathogen in self.game.pathogens_with_vaccine:
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

    # Pathogen Heuristic
    def reweigh_pathogens(self):
        """
        Reweighs the properties of pathogens according to the game state
        :return: dict of pathogen names associated to a reweighed pathogen object
        """

        tmp_dict = {}
        for pathogen in self.relevant_pathogens:
            pat_scale = Scalegroup({'lethality': 1, 'infectivity': 1,
                                    'mobility': 1, 'duration': 1})

            # Apply base bias (lethality stays the same)
            pat_scale.apply_bias('infectivity', 0.9)
            pat_scale.apply_bias('duration', 0.8)
            pat_scale.apply_bias('mobility', 0.6)

            # Collect Game Feature
            infected_citz = self.game.get_percentage_of_infected(pathogen)
            immune_citz = self.game.get_percentage_of_immune(pathogen)
            # Influences
            pat_scale.increase_on_dependency('infectivity', infected_citz * pat_scale.influence_lvl3)
            pat_scale.increase_on_dependency('lethality', infected_citz * pat_scale.influence_lvl3)
            pat_scale.decrease_on_dependency('infectivity', immune_citz * pat_scale.influence_lvl2)

            pat_scale.increase_on_dependency('mobility', pathogen.infectivity * pat_scale.influence_lvl3)
            # Infectivity is more important the longer the duration
            pat_scale.increase_on_dependency('infectivity', pathogen.duration * pat_scale.influence_lvl3)
            # The shorter the duration the more important is lethality
            pat_scale.increase_on_dependency('lethality', (1 - pathogen.duration) * pat_scale.influence_lvl3)

            pat_scale.rescale()
            tmp_dict[pathogen.name] = Pathogen(pathogen.name, pat_scale.sg['infectivity'], pat_scale.sg['mobility'],
                                               pat_scale.sg['duration'], pat_scale.sg['lethality'],
                                               transformation=False)

        return tmp_dict

    def reweigh_pathogen_for_city(self):
        """
        Reweighs properties of pathogens for the city in which they are
        :return: city specific pathogen weights as dict whereby key is city name and value is pathogen object
        """

        tmp_dict = {}
        for city in self.game.cities_list:
            if city.outbreak:
                pathogen = self.weighted_pathogens[city.outbreak.pathogen.name]

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
                outbreak_lifetime = h_utils.since_round_percentage(self.game.round, city)

                # If outbreak_lifetime exists longer then the duration becomes more important because kill is sooner
                pat_scale.increase_on_dependency('duration', outbreak_lifetime * pat_scale.influence_lvl2)
                # Increase mobility of the city, increases mobility of the pathogen
                pat_scale.increase_on_dependency('mobility', city_mob * pat_scale.influence_lvl2)

                if vacc_dep:
                    pat_scale.sg['infectivity'] = 0
                else:
                    pat_scale.increase_on_dependency('infectivity', int(anti_vac) * pat_scale.influence_lvl1)
                    pat_scale.decrease_on_dependency('infectivity', city_hyg * pat_scale.influence_lvl2)
                    pat_scale.decrease_on_dependency('infectivity', int(med_dep) * pat_scale.influence_lvl2)

                pat_scale.rescale()

                # Add pathogen to dict
                tmp_dict[city.name] = Pathogen(pathogen.name, pat_scale.sg['infectivity'], pat_scale.sg['mobility'],
                                               pat_scale.sg['duration'], pat_scale.sg['lethality'],
                                               transformation=False)

        return tmp_dict
