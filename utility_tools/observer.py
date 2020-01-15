import json
from os.path import isfile, dirname

from heilung.models.action import Action
from heilung.models.game import Game

BASEPATH = dirname(dirname(__file__))


class Observer:
    """Observes the game and what is happening.
    """
    encountered_pathogens = dict()
    encountered_happenings = dict()
    global_events = dict()
    errors = list()
    actions = list()
    state_recaps = list()

    def __init__(self, game: Game, action: Action, seed: str):
        """Initializes the observer

        Arguments:
            game {Game} -- The current game state object
            action {Action} -- The action chosen by the heuristic
            seed {str} -- Seed used for this execution
        """
        self.game = game
        self.seed = seed

        self.load_state()

        if game.error != '':
            self.errors.append(game.error)

        if len(self.state_recaps) == 0 or self.state_recaps[-1]['round'] != game.round:
            self.state_recaps.append(game.get_state_dict())
        self.actions.append(str(self.game.round) + " | " + str(action.build_action()))

        for _, outbreak in game.outbreaks:
            self.encountered_pathogens[outbreak.pathogen.name] = outbreak.pathogen.to_dict()

        city_events = [city.events for city in game.cities.values() if len(city.events) > 0]
        for events in city_events:
            for event in events:
                self.encountered_happenings[event.type] = event.to_dict()

        for event in game.events:
            if event.type == 'pathogenEncountered':
                pathogen = event.pathogen
                self.encountered_pathogens[pathogen.name] = pathogen.to_dict()
            self.global_events[event.type] = event.to_dict()

        self.save_state()

    def load_state(self):
        """load the last observations from disk
        """
        if isfile(f'{BASEPATH}/observations/observer-{self.seed}.json'):
            with open(f'{BASEPATH}/observations/observer-{self.seed}.json', 'r') as f:
                data = json.load(f)
                self.encountered_pathogens = data['encountered_pathogens']
                self.encountered_happenings = data['encountered_happenings']
                self.global_events = data['global_events']

                self.errors = data.get('errors', list())
                self.actions = data.get('actions', list())
                self.state_recaps = data.get('state_recaps', list())

    def save_state(self):
        """Save observations to disk
        """
        with open(f'{BASEPATH}/observations/observer-{self.seed}.json', 'w') as f:
            data = {
                'encountered_pathogens': self.encountered_pathogens,
                'encountered_happenings': self.encountered_happenings,
                'global_events': self.global_events,
                'errors': self.errors,
                'actions': self.actions,
                'state_recaps': self.state_recaps,
            }
            json.dump(data, f, indent=4, sort_keys=True)

    def get_city_state(self, city) -> dict:
        """Render a dictionary from city data

        Arguments:
            city {City} -- A city object

        Returns:
            dict -- Dictionary of city attributes
        """
        return {
            'name': city.name,
            'population': city.population,
            'connections': city.connections,
            'economy': city.economy,
            'government': city.government,
            'hygiene': city.hygiene,
            'awareness': city.awareness,
            'outbreak': {
                'pathogen': city.outbreak.pathogen.name,
                'prevalence': city.outbreak.prevalence,
                'since_round': city.outbreak.sinceRound
            }
        }
