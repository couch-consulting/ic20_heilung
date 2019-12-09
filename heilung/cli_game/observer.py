from os.path import isfile
import json

from heilung.models import actions
from heilung.models.pathogen import Pathogen


class Observer:
    """Observes the game and what is happening.
    """
    encountered_pathogens = dict()
    encountered_happenings = dict()
    global_events = dict()
    planned_executions = dict()
    action_plan = list()

    def __init__(self, game: 'Game'):
        self.game = game

        self.load_state()

        for city, outbreak in game.outbreaks:
            self.encountered_pathogens[outbreak.pathogen.name] = outbreak.pathogen.to_dict()

        for city, events in game.city_events:
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
        if isfile('observer.json'):
            with open('observer.json', 'r') as f:
                data = json.load(f)
                self.encountered_pathogens = data['encountered_pathogens']
                self.encountered_happenings = data['encountered_happenings']
                self.global_events = data['global_events']

                self.planned_executions = data.get('planned_executions', dict())

    def save_state(self):
        """Save observations to disk
        """
        with open('observer.json', 'w') as f:
            data = {
                'encountered_pathogens': self.encountered_pathogens,
                'encountered_happenings': self.encountered_happenings,
                'global_events': self.global_events,
                'planned_executions': self.planned_executions
            }
            json.dump(data, f, indent=4, sort_keys=True)

    def get_action_plan(self):
        """Plans executions to test
        """

        # Plan 1: Develop Medication/Vaccination + Deploy
        if 'medication' not in self.planned_executions:
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

            self.planned_executions['medication'] = {
                'pathogen': pathogen.name,
                'city_before': self.get_city_state(city)
            }

        elif 'city_after' not in self.planned_executions['medication']:
            city_name = self.planned_executions['medication']['city_before']['name']
            self.planned_executions['medication']['city_after'] = self.get_city_state(self.game.cities[city_name])

        elif 'vaccination' not in self.planned_executions:
            for event in self.game.events:
                if event['type'] == 'pathogenEncountered':
                    pathogen = event['pathogen']
                    pathogen = Pathogen.from_dict(pathogen)
                    self.action_plan.append(actions.DevelopVaccine(pathogen))
                    for _ in range(6):
                        self.action_plan.append(actions.EndRound())

                    for city, outbreak in self.game.outbreaks:
                        if outbreak.pathogen.name == pathogen.name:
                            self.action_plan.append(actions.DeployVaccine(city, pathogen))
                            break
                break

            self.planned_executions['vaccination'] = {
                'pathogen': pathogen.name,
                'city_before': self.get_city_state(city)
            }

        elif 'city_after' not in self.planned_executions['vaccination']:
            city_name = self.planned_executions['vaccination']['city_before']['name']
            self.planned_executions['vaccination'][f'city_after'] = self.get_city_state(self.game.cities[city_name])


        # Plan 2: Develop Vaccine + Deploy

        self.action_plan.append(actions.EndRound())

        self.save_state()

        return self.action_plan

    def get_city_state(self, city):

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
                'prevalence': city.outbreak.prevalence
            }
        }
