from typing import List, Tuple

from heilung.models import actions, events
from heilung.models.pathogen import Pathogen


class StupidHeuristic:
    """A stupid heuristic.
    Nobody will survive.
    """
    weights = {
        'pathogen': {
            'global': 1,
            'prevalence': 1,
            'duration': 1,
            'infectivity': 3,
            'lethality': 4,
            'mobility': 3,
        },
        'isolation': {
            'global': 1,
            'prevalence': 1,
            'duration': 1,
            'infectivity': 1,
            'lethality': 1,
            'mobility': 1,
        },
        'treatment': {
            'global': 1,
            'prevalence': 1,
            'duration': 1,
            'infectivity': 1,
            'lethality': 1,
            'mobility': 1,
        },
        'city_eligibility': 1,
    }

    def __init__(self, game: 'Game'):
        """Initialize heuristic with important data

        Arguments:
            game {Game} -- Game object
        """
        self.game = game
        self.action_list = list()

    def get_decision(self) -> List['Action']:
        """Top level interface for the heuristic to generate a decision
        """
        if self.game.points == 0:
            return [actions.EndRound()]

        # Handle BioTerrorism Events with higher priority
        if len(self.game.has_new_bioTerrorism) > 0:
            city = self.game.has_new_bioTerrorism[0]
            if actions.PutUnderQuarantine.is_possible(self.game, 2, city):
                return [actions.PutUnderQuarantine(city, 2)]

        if self.game.round > 1 and self.game.points <=20:
            return [actions.EndRound()]


        # Add an EndRound action, so action_list will never be empty
        # TODO: Rethink rank
        self.action_list.append((0, actions.EndRound()))

        # Focus on pathogens first
        # This will populate the action list
        self.evaluate_pathogens()

        # Order action list descending by rank
        self.action_list = sorted(
            self.action_list,
            key=lambda action: action[0],
            reverse=True)

        # Return just the action without rank
        return [ranked_action[1] for ranked_action in self.action_list]

    def rank_pathogen(self, pathogen: Pathogen, prevalence: float) -> float:
        weights = self.weights['pathogen']
        rank = weights['global'] * (
                (weights['prevalence'] * prevalence) +
                (weights['lethality'] * pathogen.lethality) +
                (weights['infectivity'] * pathogen.infectivity) +
                (weights['duration'] * pathogen.duration) +
                (weights['mobility'] * pathogen.mobility))
        # print(f'{pathogen.name}: {rank}')
        return rank

    def evaluate_pathogens(self):
        pathogens = self.game.pat_state_dict
        weights = self.weights['treatment']

        # First get the most relevant pathogen (so we always get one to fight against)
        if len(pathogens) == 0:
            # Last round. All pathogens gone. Evaluation will fail
            return
        relevant_pathogens = sorted(
            pathogens.keys(),
            key=lambda pat_name: self.rank_pathogen(
                pathogens[pat_name]['pathogen'],
                pathogens[pat_name]['prevalence']),
            reverse=True)
        relevant_pathogen = relevant_pathogens[0]

        # Get the actual pathogen for statistical pathogen data
        pathogen = pathogens[relevant_pathogen]['pathogen']
        if pathogens[relevant_pathogen]['mAva']:
            self.deploy_in_cities(pathogen, 'medication')
        if pathogens[relevant_pathogen]['vAva']:
            self.deploy_in_cities(pathogen, 'vaccine')

        if not pathogens[relevant_pathogen]['any_action']:
            # Maybe we should develop something
            action = self.decide_vacc_or_med(pathogen)
            rank = weights['global'] * (
                (weights['prevalence'] * pathogens[relevant_pathogen]['prevalence']) *
                (weights['lethality'] * pathogen.lethality) *
                (weights['infectivity'] * pathogen.infectivity))

            if action.is_possible(self.game, pathogen):
                self.action_list.append((rank, action))

        if pathogen.mobility >= 0.5:
            self.isolate_cities(pathogen)

        # When a medication for the most relevant pathogen is currently under
        # development and containment doesn't make sense it may be a good idea
        # to already prepare a medication for the second most relevant pathogen.
        if (pathogens[relevant_pathogen]['vDev'] or pathogens[relevant_pathogen]['mDev']) and len(relevant_pathogens) > 1:
            second_pathogen = relevant_pathogens[1]
            pathogen = pathogens[second_pathogen]['pathogen']

            if pathogens[second_pathogen]['any_action']:
                return

            action = self.decide_vacc_or_med(pathogen)
            rank = weights['global'] * (
                (weights['prevalence'] * pathogens[second_pathogen]['prevalence']) *
                (weights['lethality'] * pathogen.lethality) *
                (weights['infectivity'] * pathogen.infectivity))

            if action.is_possible(self.game, pathogen):
                self.action_list.append((rank, action))


    def decide_vacc_or_med(self, pathogen: Pathogen) -> 'Action':
        # High infectivity
        if pathogen.infectivity >= 0.5:
            if pathogen.lethality >= 0.5:
                return actions.DevelopMedication(pathogen)
            else:
                return actions.DevelopVaccine(pathogen)
        elif pathogen.infectivity > 0.25:
            if pathogen.lethality >= 0.75:
                return actions.DevelopMedication(pathogen)
            else:
                return actions.DevelopVaccine(pathogen)
        else:
            return actions.DevelopVaccine(pathogen)

    def get_eligible_cities(self, pathogen_name: str) -> Tuple[List['City'], 'City']:
        """Get Cities with a pathogen and the largest one
        """
        eligible_cities = self.game.cities_with_pathogen[pathogen_name]

        largest_city = max(eligible_cities, key=lambda city: city.population)

        return eligible_cities, largest_city

    def deploy_in_cities(self, pathogen: Pathogen, kind: str):
        """Deploy medication or vaccine to city
        Generates the according actions.

        Arguments:
            pathogen {Pathogen} -- Pathogen to treat
            kind {str} -- medication or vaccine
        """

        eligible_cities, largest_city = self.get_eligible_cities(pathogen.name)

        for city in eligible_cities:
            # Priority will be affected by rank later
            rank = (city.outbreak.prevalence * city.population)/largest_city.population
            rank *= self.weights['city_eligibility']
            if kind == 'medication':
                action = (rank, actions.DeployMedication(city,
                city.outbreak.pathogen))
            else:
                if city.has_event(events.AntiVaccinationism):
                    # Do not vaccinate in cities with AntiVaccinationism
                    continue
                if pathogen in city.deployed_vaccines:
                    continue
                action = (rank, actions.DeployVaccine(city,
                city.outbreak.pathogen))
            self.action_list.append(action)

    def isolate_cities(self, pathogen: 'Pathogen'):
        """Generate isolation events if applicable

        Arguments:
            pathogen {Pathogen} -- [description]
        """
        if len(self.game.get_cities_with_pathogen(pathogen)) > 1:
            # Virus has already spread. Pointless to isolate
            return
        eligible_cities, largest_city = self.get_eligible_cities(pathogen.name)
        for city in eligible_cities:
            if city.under_quarantine or city.airport_closed:
                continue
            weights = self.weights['isolation']

            rank = weights['global'] * (
                    (weights['prevalence'] * (city.outbreak.prevalence * city.population)/largest_city.population) *
                    (weights['lethality'] * pathogen.lethality) *
                    (weights['mobility'] * pathogen.mobility) *
                    (weights['infectivity'] * pathogen.infectivity))

            quarantine_rounds = actions.PutUnderQuarantine.get_max_rounds(self.game.points)

            if quarantine_rounds >= 2:
                action = actions.PutUnderQuarantine(city, 2)
                self.action_list.append((rank, action))
