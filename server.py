import argparse
import sys

from flask import Flask, abort, g, request

from heilung.builders.action import ActionBuilder
from heilung.cli_game.observer import Observer
from heilung.heuristics.human import human
from heilung.heuristics.stupid import StupidHeuristic
from heilung.models import Game

app = Flask(__name__)

action_plan = list()
last_state_dic = {}


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    if request.json.get('error') is not None:
        print(request.json.get('error'))

    game = Game(request.json)

    if game.outcome in ['win', 'loss']:
        # Save Results
        global last_state_dic
        last_state_dic['outcome'] = game.outcome
        # - 1 since only the round up to this current round were survived
        last_state_dic['rounds'] = game.round - 1

    # Heuristics
    # Human heuristic response
    # response = human.get_decision(game)[0][0]  # [0][0] := most important action

    stupid = StupidHeuristic(game)
    response = stupid.get_decision()[0]

    # # Example for random iterations
    # action_builder = ActionBuilder(game)
    # action_list = action_builder.get_actions()
    # response = action_builder.random_action(action_list)

    # Output
    if not app.config['SILENT']:
        # Temporary to monitor round change
        print(game.state_recap(short=True))
        if 'city' in response.parameters and game.cities[response.parameters['city']].outbreak:
            print('Action for Pathogen: ' + str(game.cities[response.parameters['city']].outbreak.pathogen.name))
        print(response.build_action())

    # Observer
    if not app.config['NO_OBS']:
        Observer(game, response, app.config['SEED'])

    return response.build_action()


# Routes for testing
@app.route('/last_state', methods=['GET'])
def last_state():
    global last_state_dic
    return last_state_dic


@app.route('/seed/<seed_id>', methods=['POST'])
def seed_update(seed_id):
    app.config['SEED'] = seed_id
    return {}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IC20 Contribution Flask Based Server')
    parser.add_argument('--seed', type=str, help='A custom seed to know for observation purposes', default='unknown')
    parser.add_argument('--silent', help='Remove any output of the game', action='store_true')
    parser.add_argument('--port', type=str, help='Port for server', default='5000')
    parser.add_argument('--no_obs', help='Disable Observer', action='store_true')

    args = parser.parse_args()
    app.config['SEED'] = args.seed
    app.config['SILENT'] = args.silent
    app.config['NO_OBS'] = args.no_obs

    if args.silent:
        # Mute Flask completely
        import logging

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

    app.run(port=args.port)
