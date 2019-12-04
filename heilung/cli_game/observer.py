from os.path import isfile
import json

from heilung.models import actions
from heilung.models.events.sub_event.pathogen import Pathogen


class Observer:
    """Observes the game and what is happening.
    """
    encountered_pathogens = dict()
    encountered_happenings = dict()
    global_events = dict()
    action_plan = list()

    def __init__(self, game: 'Game'):
        self.game = game

        self.load_state()

        for city, outbreak in game.outbreaks:
            self.encountered_pathogens[outbreak.pathogen.name] = outbreak.pathogen.to_dict()

        for city, events in game.city_events:
            for event in events:
                if isinstance(event, dict):
                    self.encountered_happenings[event['type']] = event
                else:
                    self.encountered_happenings[event.type] = event

        for event in game.events:
            if event['type'] == 'pathogenEncountered':
                pathogen = event['pathogen']
                self.encountered_pathogens[event['pathogen']['name']] = pathogen
            self.global_events[event['type']] = event

        self.save_state()
        return

    def load_state(self):
        """load the last observations from disk
        """
        if isfile('observer.json'):
            with open('observer.json', 'r') as f:
                data = json.load(f)
                self.encountered_pathogens = data['encountered_pathogens']
                self.encountered_happenings = data['encountered_happenings']
                self.global_events = data['global_events']

        return

    def save_state(self):
        """Save observations to disk
        """
        with open('observer.json', 'w') as f:
            data = {
                'encountered_pathogens': self.encountered_pathogens,
                'encountered_happenings': self.encountered_happenings,
                'global_events': self.global_events
            }
            json.dump(data, f, indent=4, sort_keys=True)
        return

    def get_action_plan(self):
        """Returns a random action
        """
        # Test medication
        for event in self.game.events:
            if event['type'] == 'pathogenEncountered':
                pathogen = event['pathogen']
                pathogen = Pathogen.from_dict(pathogen)
                self.action_plan.append(actions.DevelopMedication(pathogen))
                for _ in range(4):
                    self.action_plan.append(actions.EndRound())

                for city, outbreak in self.game.outbreaks:
                    if outbreak.pathogen.name == pathogen.name:
                        self.action_plan.append(actions.DeployMedication(city, pathogen))
                        break
                break
        self.plan_finished = True

        self.action_plan.append(actions.EndRound())
        print(self.action_plan)
        return self.action_plan
