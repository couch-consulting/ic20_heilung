from heilung.models import actions
import math
from .h_utils import compute_pathogen_importance


class Gameplan:
    """
    Gameplan for the current game state for the human heuristic
    """

    def __init__(self, game, sorted_city_action, sorted_global_actions, weighted_pathogens, dev_needed):
        self.game = game
        self.sorted_city_action = sorted_city_action
        self.sorted_global_actions = sorted_global_actions
        self.weighted_pathogens = weighted_pathogens
        self.dev_needed = dev_needed

        self.max_list_len = 10

    def build_action_list(self):
        """
        Build a list of actions whereby the first one is the most important action to perform in this round
        List may vary depending on the gameplan
            - sometimes only 1 action is suggested due to the game state and gameplan
        :return: List[Action]
        """

        result = self.get_best_action()
        if not isinstance(result, list):
            result = [result]
        else:
            result = [action for (action, rank) in result]

        return result

    def get_best_action(self):
        """
        Get the best action for the current game state
        :return: Action
        """
        # Tmp vars
        ava_points = self.game.points

        # Round 1 Gameplan - special because guaranteed to have 40 points and early in game
        if self.game.round == 1:
            return self.round_1_gameplan(ava_points)

        # Round X Gameplan
        return self.round_x_gameplan(ava_points)

    # Gameplan
    def round_1_gameplan(self, ava_points):
        """
        Get best action in round 1
        :param ava_points: points to spend in this round
        :return: Action object or list of action objects depending on the gameplan situation
        """

        if ava_points < 40:
            return actions.EndRound()

        # Else First action in first round
        # Get all cities in which the mobility must be reduced
        candidate_cities = self.get_duration_candidate_cities()

        if candidate_cities:
            # Features
            pats_in_candidate_cities = [city.outbreak.pathogen for city in candidate_cities]
            not_candidate = [pat for pat in self.game.pathogens_in_cities if pat not in pats_in_candidate_cities]
            most_important_pat_candidate = sorted(candidate_cities, key=lambda x: compute_pathogen_importance(
                self.weighted_pathogens[x.outbreak.pathogen.name], x.outbreak.pathogen), reverse=True)[0]
            pat_cand_rank = compute_pathogen_importance(
                self.weighted_pathogens[most_important_pat_candidate.outbreak.pathogen.name],
                most_important_pat_candidate.outbreak.pathogen)
            more_important_ava = [pat for pat in not_candidate if
                                  compute_pathogen_importance(self.weighted_pathogens[pat.name], pat) > pat_cand_rank]

            # Use features to test if a harmless mobile exits
            # (e.g. a pathogen which would spread to every city and infect them before any other could
            # and if a more important existing pathogen is not a candidate,
            # if both are True skip this step and go to global actions
            if not more_important_ava:
                return self.get_action_for_candidate_cities(candidate_cities, ava_points)

        return self.sorted_global_actions[:self.max_list_len]

    def round_x_gameplan(self, ava_points):
        """
        Get best action any round greater 1
        :param ava_points: points to spend in this round
        :return: Action object or list of action objects depending on the gameplan situation
        """

        # Build up fall back points for bio terrorism and isolation in round X gameplan
        ava_points -= 20
        saved_points = 20

        isolated_cities = self.get_isolated_cities()

        # Isolated Gameplan (Make pathogens die out)
        if isolated_cities:
            # Get real number of points to avoid having not isolated cities
            # Also counters bio terrorism since bio terrorism only needs to be specially treated if it is also isolated
            # It only does no catch if we have an isolated bio terrorism with mobility equal 0
            # - this case is handled by default by the global action gamneplan and heuristic
            return self.get_action_for_isolated_cities(isolated_cities, ava_points, saved_points)

        cities_with_bio_terrorism = self.game.has_new_bioTerrorism
        # Bio Terrorism game plan (counter bio terrorism of completely new pathogens)
        if cities_with_bio_terrorism:
            # we have a isolated bio terrorism with mobility equal 0, hence add saved points to ava points
            ava_points += saved_points

        # Save points
        if ava_points <= 0:
            return actions.EndRound()

        if not self.sorted_global_actions:
            # If no global actions anymore, do most important city action
            return self.get_best_city_action(ava_points)

        return self.get_action_for_global_actions(ava_points)

    # Specifics for City actions
    def get_best_city_action(self, ava_points, points_needed=0):
        """
        Get most important action of a given sorted action list
        and optionally consider how much point shall be available in the future
        :param points_needed: points needed for an action that is desired to be executed next
        :param ava_points: point allowed to use
        :return: the best possible city action ready to be build
        """

        if ava_points == 0:
            # Impossible to do anything if current amount of points is 0
            # However, currently, this should never become relevant since this case is considered earlier
            return [(actions.EndRound(), 1)]

        # Check if desired action for next round exists
        if points_needed == 0:
            return self.select_action_for_points(ava_points)
        # Logic for wait "heuristic"
        points_per_round = self.game.points_per_round
        if points_per_round < points_needed:
            # If pointer_per_round < needed points
            if ava_points > points_needed - points_per_round:  # 42 > 40 - 20

                # if pointer_per_round + ava__points > needed_points, spend: ava - (needed - per_round)
                points_to_spend = ava_points - (points_needed - points_per_round)

                return self.select_action_for_points(points_to_spend)

            elif points_per_round + ava_points == points_needed:
                # if pointer per round + ava = needed points, end round
                return [(actions.EndRound(), 1)]

            elif points_per_round + ava_points < points_needed:
                # if pointer per round + ava < needed_points, check additional_num rounds
                # and if you can execute action right now
                additional_missing_points = abs(ava_points + points_per_round - points_needed)
                additional_num_of_rounds_to_wait = math.ceil(additional_missing_points / points_per_round)
                # Amount of points that are not used while waiting for the points to do the desired action
                too_much_points = additional_num_of_rounds_to_wait * points_per_round - additional_missing_points
                if ava_points >= too_much_points:
                    # If the points, that are going to be too much later, are already available, use them
                    # Simply search for best city action whereby needed points is adapted
                    # As "Next round, only the points that are not too much + the default points per round are needed"
                    tmp_points_needed = points_per_round + (ava_points - too_much_points)
                    return self.get_best_city_action(ava_points, points_needed=tmp_points_needed)

                # If the overflow of points does not happen in this round,
                # the following executions of the code in the next round will catch the points and spend them
                # Hence we can just end the round here
                # same case as if we have to wait the num of round and are not allowed to spend any of it
                return [(actions.EndRound(), 1)]
        # if pointer_per_round >= needed_points, spend all ava_points
        return self.select_action_for_points(ava_points)

    def select_action_for_points(self, points):
        """
        Logic for spending the specified amount of points
        :param points: points to spend
        :return: list of best possible actions for the specified number of points
        """
        result_list = []
        for _ in range(self.max_list_len):
            most_important_action = self.sorted_city_action[0][0]
            most_important_action_rank = self.sorted_city_action[0][1]

            # Basic idea
            if most_important_action.costs <= points or most_important_action.recalculate_costs_for_points(
                    points).costs <= points:
                # Do most important if possible
                result_list.append((most_important_action, most_important_action_rank))
            else:
                # Recalculate for actions (only changes the value if it would become due to the adjustment)
                recalc_actions = [(action.recalculate_costs_for_points(points), importance)
                                  for (action, importance) in self.sorted_city_action]
                # Find best possible action in list for points whereby reduce mobility action costs are fitted
                possible_actions_for_points = [(action, importance) for (action, importance) in recalc_actions
                                               if action.costs <= points]

                if possible_actions_for_points:
                    # Return most important of these actions
                    result_list.append((possible_actions_for_points[0][0], possible_actions_for_points[0][1]))
                else:
                    # Not enough points for any action
                    rank = 1
                    if result_list:
                        rank = result_list[-1][1] * 0.8
                    result_list.append((actions.EndRound(), rank))

            # Remove element from list
            selected_action = result_list[-1][0]
            if not selected_action.type == 'endRound':
                self.remove_element_from_list(selected_action)

        return result_list

    def get_action_for_candidate_cities(self, candidate_cities, points_to_spend):
        """
        Return the best action for cities infected with a low duration pathogen
        :param candidate_cities: list of cities which could be isolated
        :param points_to_spend: points allowed to be spend
        :return: One or multiple actions depending on the amount of candidate cities
        """
        # sort for biggest city first
        candidate_cities.sort(key=lambda x: x.population, reverse=True)
        # Sort for most important pathogen
        candidate_cities = sorted(candidate_cities, key=lambda x: compute_pathogen_importance(
            self.weighted_pathogens[x.outbreak.pathogen.name], x.outbreak.pathogen), reverse=True)

        # List return in this case (can be 1)
        result = []
        for index, city in enumerate(candidate_cities, start=1):
            tmp_action = self.get_action_for_mobile_city(city, points_to_spend)
            if not tmp_action:
                tmp_action = self.get_best_city_action(points_to_spend)[0][0]
            result.append((tmp_action, 1 / index))

        return result

    def get_action_for_isolated_cities(self, isolated_cities, ava_points, saved_points):

        ava_points = saved_points + ava_points

        still_isolated = [city for city in isolated_cities if city.under_quarantine or city.airport_closed]
        no_isolation_present = [city for city in isolated_cities if city not in still_isolated]

        if still_isolated:
            # all isolated cities are still isolated - hence get points to keep them isolated next round
            points_needed_in_future = actions.PutUnderQuarantine.get_costs(2)

            if ava_points + self.game.points_per_round >= points_needed_in_future:
                if no_isolation_present:
                    return self.get_action_for_no_isolation_present(no_isolation_present, ava_points, saved_points)

                # # Additional puffer
                points_needed_in_future *= 2

                pats_isolated = [city.outbreak.pathogen.name for city in isolated_cities]
                # more points than needed in future, do something with them
                rest_points = ava_points - points_needed_in_future + self.game.points_per_round
                # Get global actions which are cheap enough and of a different pathogen
                global_actions = [(self.plan_global_action(action, rest_points), rank)
                                  for (action, rank) in self.sorted_global_actions if
                                  action.costs <= rest_points and action.parameters['pathogen'] not in pats_isolated]
                # Get action list for city
                action_list = self.get_best_city_action(ava_points, points_needed=points_needed_in_future)

                # Needed for later
                med_or_vac_in_list = [bool(action.type in ['deployVaccine', 'deployMedication']) for (action, _)
                                      in action_list]

                # Check if global action might be a better idea
                if global_actions and (True not in med_or_vac_in_list):
                    # if 20 or more points try a global action
                    # (global action list would be empty if less than 20 points and thus also considered like this)
                    action_list = global_actions

                return action_list

            # need more points, hence wait for them
            return actions.EndRound()

        return self.get_action_for_no_isolation_present(no_isolation_present, ava_points, saved_points)

    def get_action_for_no_isolation_present(self, no_isolation_present, ava_points, saved_points):
        # Sort for most important pathogen
        city = sorted(no_isolation_present, key=lambda x: compute_pathogen_importance(
            self.weighted_pathogens[x.outbreak.pathogen.name], x.outbreak.pathogen), reverse=True)[0]

        tmp_num_rounds = actions.PutUnderQuarantine.get_max_rounds(ava_points)
        if tmp_num_rounds:
            # Put under quarantine possible
            return actions.PutUnderQuarantine(city, min(tmp_num_rounds, 2))

        return self.get_best_city_action(ava_points - saved_points)

    # Specifics for Global actions
    def get_action_for_global_actions(self, ava_points):
        """
        Get the best global action or the best action to perform this global action in the future
        :param ava_points: points to spend
        :return: Action object
        """
        tmp_var_developing, tmp_var_developed, tmp_var_developing_or_developed, \
        tmp_developed_state_dict, tmp_overall_state_dict, \
        tmp_every_pat_has_dev, tmp_any_pat_has_ava = self.get_pat_state()

        # If for every pathogen something is developing and nothing is already developed
        if tmp_every_pat_has_dev and not tmp_any_pat_has_ava:
            # just save the points to deploy once everything is developed
            return actions.EndRound()

        # If at least one medication or vaccine is still developing
        if tmp_var_developing:
            if tmp_var_developing_or_developed:
                # and each pathogen has a medication or a vaccine in development or already developed
                # Do best city action
                return self.get_best_city_action(ava_points)

            # or and not each pathogen has a medication or a vaccine in development or already developed
            # Do best global action (i.e. develop a medication or vaccine for a so far not considered pathogen
            # Filter out actions for pathogens which are already developing or developed
            filtered_global_actions = [(tmp_action, rank) for (tmp_action, rank) in self.sorted_global_actions
                                       if not tmp_overall_state_dict[tmp_action.parameters['pathogen']]]
            # Resulting list can not be empty since this would result in the previous if being true,
            # further order is preserved
            # Thus simply get new most important by taking the first one
            return [(self.plan_global_action(action, ava_points), rank) for (action, rank) in filtered_global_actions]

        # If non is currently developing
        if not tmp_var_developed:
            # and not each pathogen has either medication or vaccine developed
            filtered_global_actions = [(tmp_action, rank) for (tmp_action, rank) in self.sorted_global_actions
                                       if not tmp_developed_state_dict[tmp_action.parameters['pathogen']]]
            return [(self.plan_global_action(action, ava_points), rank) for (action, rank) in filtered_global_actions]

        # Dynamic cap which is maxed at 3 rounds - defines when another global action should be performed
        # A pat is in need of a global action if medi/vaci is needed but not available
        pat_in_need_of_global_action = [pat.name for pat in self.game.pathogens_in_cities if
                                        self.dev_needed.get(pat.name, 0)
                                        >= int(0.5 * len(self.game.get_cities_with_pathogen(pat)))]
        filtered_global_actions = [global_action for global_action in self.sorted_global_actions
                                   if global_action[0].parameters['pathogen'] in pat_in_need_of_global_action]
        # Check whether a global action for a pathogen exists which is in need of action
        if pat_in_need_of_global_action and filtered_global_actions:
            # Special trigger
            return [(self.plan_global_action(action, ava_points), rank)
                    for (action, rank) in filtered_global_actions]

        # if self.game.last_development_finished_since >= len(self.game.pathogens_in_cities)*2:
        # if self.game.last_development_finished_since >= 1:
        # if self.game.last_development_finished_since >= 3:
        # if self.game.last_development_finished_since >= 6:
        # 5

        if self.game.last_development_finished_since >= 3:
            # TODO: Possible improvement: extend features to use for dynamic max and create exceptions
            return [(self.plan_global_action(action, ava_points), rank)
                    for (action, rank) in self.sorted_global_actions]

        return self.get_best_city_action(ava_points)

    def plan_global_action(self, global_action, ava_points):
        """
        'Schedules" to return the desired global action, if enough points available, it will be returned immediately
        if not either the round will be ended
        or an action using the points that are not used is played such that next round this action is still possible
        :param global_action: a global action which is ready to be build
        :param ava_points: point allowed to use
        :return: action to perform to achieve doing this action now or later
        """
        action = global_action
        # get costs - no need to check other get_costs instances since all global actions have constant costs
        costs = global_action.get_costs()

        # Check if selected global action is possible
        if ava_points < costs:
            # If not, select an action that makes it possible when just waiting next time
            action = self.get_best_city_action(ava_points, points_needed=costs)[0][0]
            # This works because the select action will see that no points to play exists in the 2nd time triggering
            # and thus just ends the round

        return action

    # Utils
    def get_duration_candidate_cities(self):
        """
        Returns a list of cities which have a small duration and either very small population or high population
        """
        candidate_cities = []
        for pathogen in self.game.pathogens_in_cities:
            if pathogen.mobility > 0 and len(self.game.get_cities_with_pathogen(pathogen)) == 1:
                for city in self.game.get_cities_with_pathogen(pathogen):
                    if not (city.airport_closed or city.under_quarantine):
                        candidate_cities.append(city)
        return candidate_cities

    def get_isolated_cities(self):
        """
        Get cities which need to be isolated
        :return: List[City]
        """
        isolated_cities = []

        for pathogen in self.game.pathogens_in_cities:
            # only cities with mob higher 0 are important because mob 0 pats are and will be isolated for ever mostly
            if len(self.game.get_cities_with_pathogen(pathogen)) == 1 \
                    and not self.game.pat_state_dict[pathogen.name]['any_action'] \
                    and ((pathogen.mobility > 0) or (
                    pathogen.duration >= 0.5 and pathogen.lethality >= 0.75)):
                # and not self.game.pat_state_dict[pathogen.name]['any_action']

                # Get new infected or isolated city
                tmp_city = self.game.get_cities_with_pathogen(pathogen)[0]

                # Prevent a city from being put into the list if it has no way of becoming not-isolated by itself
                neighbor_infected_state = [bool(self.game.cities[city_name].outbreak) for city_name in
                                           tmp_city.open_connections]
                if (not neighbor_infected_state or False not in neighbor_infected_state) and pathogen.mobility < 0.5:
                    continue

                isolated_cities.append(tmp_city)

        return isolated_cities

    def get_pat_state(self):
        """
        Collect a list of features about the current pat state
        :return: Features about pat state
        """
        # Get features needed for decisions below
        # Tmp var for medi or vac is developing for at least one pathogen
        tmp_var_developing = False
        tmp_var_developed = True
        # Tmp var for medi or vac is developing/developed for at least one pathogen
        tmp_var_developing_or_developed = True
        tmp_overall_state_dict = {}
        tmp_developed_state_dict = {}
        # tmp var
        tmp_every_pat_has_dev = True
        tmp_any_pat_has_ava = False
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
            # Other
            tmp_every_pat_has_dev = tmp_every_pat_has_dev and developing_state
            tmp_any_pat_has_ava = tmp_any_pat_has_ava or developed_state

        return tmp_var_developing, tmp_var_developed, tmp_var_developing_or_developed, \
               tmp_developed_state_dict, tmp_overall_state_dict, tmp_every_pat_has_dev, tmp_any_pat_has_ava

    @staticmethod
    def get_action_for_mobile_city(city, points_to_spend):
        max_rounds_for_points = actions.PutUnderQuarantine.get_max_rounds(points_to_spend)
        max_rounds_for_points_airport = actions.CloseAirport.get_max_rounds(points_to_spend)

        if not max_rounds_for_points and not max_rounds_for_points_airport:
            # Nothing possible
            return None

        # No need to check if already closed/under quarantine since first round)

        if max_rounds_for_points:
            return actions.PutUnderQuarantine(city, min(max_rounds_for_points, 2))

        if not city.connections:
            return None

        return actions.CloseAirport(city, max_rounds_for_points_airport)

    def remove_element_from_list(self, selected_action):
        """
        Removes selected action element from action list
        :param selected_action: action
        """
        for action_tuple in self.sorted_city_action:
            action = action_tuple[0]
            if action.type == 'closeConnection':
                city = action.parameters['fromCity']
            else:
                city = action.parameters['city']
            if selected_action.type == 'closeConnection':
                selected_city = selected_action.parameters['fromCity']
            else:
                selected_city = selected_action.parameters['city']

            if action.type == selected_action.type and city == selected_city:
                self.sorted_city_action.remove(action_tuple)
                break
