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

    def get_decision(self):

        city_ranks, city_weighted_pathogens = self.rank_cities()
        # print({k: v for k, v in sorted(city_ranks.items(), key=lambda item: item[1], reverse=True)})

        exit()




        ranked_actions = self.rank_actions(city_ranks)
        # print(sorted(ranked_actions, key=lambda x: x[1], reverse=True))


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

    def rank_actions(self, city_ranks):
        """
        Returns each possible (without regard to available points) action with a rank
        :param city_ranks:
        :return: List[Action, int]
        """

        # TODO think about maybe using something similar to compute importance for each value to decide influnces here
        # make sure that vaccine for each pathogen most important!

        # put this game plan as bias!
        # define a gameplan which defines what genreal actions should happen first etc and select the highest of these
        # start with developing medi or vaci of one each, e.g. make first few actions soly work on getting vaccines, medication etc but that is stupid, if city really small it should quarantine until all a dead/immune (e.g. bias is vaccine -> medication -> reduce citiy mobility)


        result = []
        # Global city unspecific book keeping of action - e.g. for development of vaccine or medication
        development_actions = {}

        for _, tmp_list in city_ranks.items():
            rank = tmp_list[0]
            city = tmp_list[1]

            # tmp vars
            reduce_city_mob = 0
            deploy_vaccine = develop_vaccine = 0
            deploy_medication = develop_medication = 0

            # Pathogen/outbreak rank influence
            if city.outbreak:
                pathogen = city.outbreak.pathogen
                if pathogen.name not in development_actions:
                    development_actions[pathogen.name] = {'develop_vaccine': 0, 'develop_medication': 0}

                # Put here to avoid calculating it twice every time
                total_prevalence = h_utils.percentage_to_num_value(self.game.get_percentage_of_infected(pathogen))

                # Collect rank data - only relevant when outbreak exists
                reduce_city_mob = self.rank_reduce_city_mobility(city, pathogen)

                # Medication/Vaccine Ranking
                vaccine = self.rank_vaccine(city, pathogen, total_prevalence)
                medication = self.rank_medication(city, pathogen, total_prevalence)

                # Readjust
                deploy_medication, develop_medication = self.readjust_medication(pathogen, medication)
                deploy_vaccine, develop_vaccine = self.readjust_vaccine(pathogen, vaccine, city.deployed_vaccines)

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

            # 3er-Action Ranks
            exert_influence = self.rank_exert_influence(city)
            apply_hyg_msr = self.rank_apply_hyg_msr(city)
            call_elections = self.rank_call_elections(city)
            launch_campaign = self.rank_launch_campaign(city)

            # Add bias (or rather subtract bias)
            reduce_city_mob = max(reduce_city_mob - 2, 1)
            exert_influence = max(exert_influence - 2, 1)
            apply_hyg_msr = max(apply_hyg_msr - 2, 1)
            call_elections = max(call_elections - 2, 1)
            launch_campaign = max(launch_campaign - 2, 1)

            max_rank = max(reduce_city_mob, exert_influence, apply_hyg_msr, call_elections,
                           launch_campaign, deploy_vaccine, develop_vaccine, deploy_medication, develop_medication)
            # MAKE SURE THAT IF CITY IS REALLY SMALL AND HIGHLY POTENT PATHOGEN TO LET EVERYON IN THEIR DIE

            # Rank mobility actions
            close_connection, close_airport, put_under_quarantine = self.get_mobility_ranks(reduce_city_mob, max_rank)

            # TODO add num of rounds heuristic for actions above - for now default to max
            #  (change below where result is appended to list)

            # Close connection heuristic for to_city (if connections exists, else set close_connectio to zero)
            sorted_connections = []
            if city.connections:
                sorted_connections = self.get_sorted_connections(city)
            else:
                close_connection = 0

            # Readjust for non outbreak actions
            # 3er action no adjustment needed - all are possible and medication/vaccine already done above
            put_under_quarantine, close_airport, close_connection, sorted_connections = \
                self.readjust_mobility(city, sorted_connections, put_under_quarantine, close_airport, close_connection)

            # Add action ranks with biased city offset for 3er-actions
            reduced_rank = math.ceil(rank / 5)
            result.append([actions.ExertInfluence(city), exert_influence + reduced_rank])
            result.append([actions.ApplyHygienicMeasures(city), apply_hyg_msr + reduced_rank])
            result.append([actions.CallElections(city), call_elections + reduced_rank])
            result.append([actions.LaunchCampaign(city), launch_campaign + reduced_rank])

            if close_connection > 0:
                num_rounds = actions.CloseConnection.get_max_rounds(self.game.points)
                # TODO think about refactoring to have multiple actions for each connection
                to_city = self.game.cities[sorted_connections[0]]
                result.append([actions.CloseConnection(city, to_city, num_rounds), close_connection + rank])
            if close_airport > 0:
                num_rounds = actions.CloseAirport.get_max_rounds(self.game.points)
                result.append([actions.CloseAirport(city, num_rounds), close_airport + rank])
            if put_under_quarantine > 0:
                num_rounds = actions.PutUnderQuarantine.get_max_rounds(self.game.points)
                result.append([actions.PutUnderQuarantine(city, num_rounds), put_under_quarantine + rank])

        # Add global actions to result list
        for pat_name, action_ranks in development_actions.items():
            print(pat_name)
            print(action_ranks)
            if action_ranks['develop_vaccine'] > 0:
                result.append([actions.DevelopVaccine(pat_name, input_is_str=True), action_ranks['develop_vaccine']])
            if action_ranks['develop_medication'] > 0:
                result.append(
                    [actions.DevelopMedication(pat_name, input_is_str=True), action_ranks['develop_medication']])

        return result

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
        tmp_scale_group, city_weighted_pathogens = self.get_city_sg_and_pathogens(cities_list, weighted_pathogens)
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

        return importance_dict, city_weighted_pathogens

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

    def rank_reduce_city_mobility(self, city, pathogen):
        """
        Intermitade value which is used later for the rank of closeConnection, closeAirport and PutUnderQuarantine
        :param city: city object
        :param pathogen: pathogen object
        :return: int value
        """
        reduce_city_mobility = 0
        # Reduce mobility features
        outbreak_lifetime = self.compute_since_round_rank(city)
        infected_cit = h_utils.percentage_to_num_value(self.game.get_percentage_of_infected(pathogen))
        immune_cit = h_utils.percentage_to_num_value(self.game.get_percentage_of_immune(pathogen))
        duration = pathogen.duration
        mobility = pathogen.mobility

        # Increase as in the higher this value the better for reduce_city_mobility
        reduce_city_mobility = h_utils.increase_on_dependency(reduce_city_mobility, outbreak_lifetime)
        reduce_city_mobility = h_utils.increase_on_dependency(reduce_city_mobility, mobility)
        # The lower this value the better
        reduce_city_mobility = h_utils.increase_on_dependency(reduce_city_mobility, duration, inverted=True,
                                                              default_inv=pathogen.max_prop)
        # These are the lower the better but are rather seen as a punishment instead of increasing
        reduce_city_mobility = h_utils.decrease_on_dependency(reduce_city_mobility, infected_cit)
        reduce_city_mobility = h_utils.decrease_on_dependency(reduce_city_mobility, immune_cit)

        return reduce_city_mobility

    def rank_exert_influence(self, city):
        rank = 0
        if city.has_event(events.EconomicCrisis):
            rank += 1
        if city.has_event(events.InfluenceExerted):
            rank -= 1
        rank = h_utils.increase_on_dependency(rank, city.economy, inverted=True)

        return rank

    def rank_call_elections(self, city):
        rank = 0
        if city.has_event(events.Uprising):
            rank += 1
        if self.game.has_event(events.LargeScalePanic):
            rank += 1
        if city.has_event(events.ElectionsCalled):
            rank -= 1
        rank = h_utils.increase_on_dependency(rank, city.government, inverted=True)

        return rank

    def rank_apply_hyg_msr(self, city):
        rank = 0
        if city.has_event(events.AntiVaccinationism):
            rank += 1
        if city.has_event(events.HygienicMeasuresApplied):
            # higher minus because event makes it to higher categorical value by default
            rank -= 3

        rank = h_utils.increase_on_dependency(rank, city.hygiene, inverted=True)

        if city.outbreak:
            rank = h_utils.increase_on_dependency(rank, h_utils.percentage_to_num_value(city.outbreak.prevalence),
                                                  inverted=True)
            rank = h_utils.increase_on_dependency(rank, city.outbreak.pathogen.infectivity)

        return max(rank, 1)

    def rank_launch_campaign(self, city):
        rank = 0
        if city.has_event(events.CampaignLaunched):
            rank -= 3

        rank = h_utils.increase_on_dependency(rank, city.awareness, inverted=True)

        return max(rank, 1)

    def rank_vaccine(self, city, pathogen, total_prev):
        rank = 0
        if not city.has_event(events.AntiVaccinationism):
            rank += 1
        if city.deployed_medication:
            rank += 2
        if pathogen in self.pat_with_vac:
            rank += 3

        rank = h_utils.increase_on_dependency(rank, pathogen.mobility)
        rank = h_utils.increase_on_dependency(rank, pathogen.duration)
        rank = h_utils.increase_on_dependency(rank, total_prev, inverted=True)
        rank = h_utils.increase_on_dependency(rank, pathogen.lethality, inverted=True, default_inv=pathogen.max_prop)
        rank = h_utils.increase_on_dependency(rank, pathogen.infectivity, inverted=True, default_inv=pathogen.max_prop)

        return rank

    def rank_medication(self, city, pathogen, total_prev):
        rank = 0
        if city.has_event(events.AntiVaccinationism):
            rank += 1
        if city.deployed_medication:
            # negative bias for deploying medication multiple times
            rank -= 3
        if pathogen in self.pat_with_med:
            rank += 3

        rank = h_utils.increase_on_dependency(rank, pathogen.mobility, inverted=True, default_inv=pathogen.max_prop)
        rank = h_utils.increase_on_dependency(rank, pathogen.duration, inverted=True, default_inv=pathogen.max_prop)
        rank = h_utils.increase_on_dependency(rank, total_prev)
        rank = h_utils.increase_on_dependency(rank, pathogen.lethality)
        rank = h_utils.increase_on_dependency(rank, pathogen.infectivity)

        return rank

    def get_mobility_ranks(self, reduce_city_mob, max_rank):
        """
        Get rank values for all mobility related action
        :param reduce_city_mob: rank of reduce_city_mob
        :param max_rank: highest value for an action rank so far
        :return:
        """
        # TODO revisit after closeness theory is done
        # Specify reduce_city_mobility
        # Scale down first again
        if reduce_city_mob > 1:
            # Get scale of reduce city mob and decide depending on this scale for subactions of city mobility
            tmp_per = h_utils.compute_percentage(max_rank, reduce_city_mob)
            # Scale down before adding rank
            close_connection = close_airport = put_under_quarantine = max(reduce_city_mob - 3, 1)
            if tmp_per <= 0.25:
                close_connection += 3
                close_airport += 2
                put_under_quarantine += 1
            elif tmp_per <= 0.6:
                close_connection += 1
                close_airport += 3
                put_under_quarantine += 2
            else:
                close_connection += 1
                close_airport += 2
                put_under_quarantine += 3
        else:
            # in this case prefer default everything to 1 - unlikely that any action is relevant
            close_connection = close_airport = put_under_quarantine = 1

        return close_connection, close_airport, put_under_quarantine

    def get_sorted_connections(self, city):
        """
        Heuristic for to_city of close connection
        Return connection list sorted for most important (highest population) first
        :param city:
        :return: list
        """
        con_with_pop = [[tmp_city_name, self.game.cities[tmp_city_name].population] for tmp_city_name in
                        city.connections]
        con_sorted = [con_tuple[0] for con_tuple in sorted(con_with_pop, key=lambda x: x[1], reverse=True)]
        return con_sorted

    def readjust_medication(self, pathogen, medication):
        """
        Readjust heuristic to ignore impossible tasks - for medication
        """
        # Keep values with their initialised value - as zero
        # if it is currently in development, thus just nothing
        deploy_medication = develop_medication = 0

        if pathogen not in self.pat_with_med and pathogen not in self.pat_with_med_dev:
            develop_medication = medication
        elif pathogen in self.pat_with_med:
            deploy_medication = medication

        return deploy_medication, develop_medication

    def readjust_vaccine(self, pathogen, vaccine, deployed_vaccines):
        """
        Readjust heuristic to ignore impossible tasks - for vaccine
        """
        # Keep values with their initialised value - as zero
        # if it is currently in development, thus just nothing
        deploy_vaccine = develop_vaccine = 0

        if pathogen not in self.pat_with_vac and pathogen not in self.pat_with_vac_dev:
            develop_vaccine = vaccine
        elif pathogen in self.pat_with_vac and not deployed_vaccines:
            deploy_vaccine = vaccine

        return deploy_vaccine, develop_vaccine

    def readjust_mobility(self, city, sorted_connections, put_under_quarantine, close_airport, close_connection):
        # Readjust heuristic to ignore impossible tasks - only for mobility actions
        if city.under_quarantine:
            # If city is under quarantine every mobility action becomes irrelevant
            close_connection = close_airport = put_under_quarantine = 0
        elif city.airport_closed:
            close_connection = close_airport = 0
            put_under_quarantine -= 3
        elif city.closed_connections:
            tmp_counter = 0
            for closed_con in city.closed_connections:
                # For each closed connection reduce rank of others and remove from valid connection
                tmp_counter += 1
                sorted_connections.remove(closed_con)

            if not sorted_connections:
                # if empty, no connection are available hence equal to airport closed
                close_connection = close_airport = 0
                put_under_quarantine -= 3
            else:
                close_airport -= tmp_counter
                put_under_quarantine -= tmp_counter

        # Check if ava_points is enough for an action
        if actions.CloseConnection.get_max_rounds(self.game.points) == 0:
            close_connection = 0
        if actions.CloseAirport.get_max_rounds(self.game.points) == 0:
            close_airport = 0
        if actions.PutUnderQuarantine.get_max_rounds(self.game.points) == 0:
            put_under_quarantine = 0

        return put_under_quarantine, close_airport, close_connection, sorted_connections
