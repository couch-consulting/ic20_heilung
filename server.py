import argparse
import sys

from flask import Flask, abort, request

from heilung.heuristics.ensemble import ensemble
from heilung.heuristics.human import human
from heilung.heuristics.stupid import StupidHeuristic
from heilung.models import Game
from heilung.utility_tools.observer import Observer

app = Flask(__name__)

last_state_dic = {}


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    if request.json.get('error') is not None:
        print(request.json.get('error'))

    game = Game(request.json)

    if game.outcome in ['win', 'loss']:
        # Save Results -- has no direct influence on statelessness of the service
        # Just used for evaluation in comparisons
        global last_state_dic
        last_state_dic['outcome'] = game.outcome
        # - 1 since only the round up to this current round were survived
        last_state_dic['rounds'] = game.round - 1

    # Heuristics
    if app.config.get('H', 0) == '1':
        stupid = StupidHeuristic(game)
        response = stupid.get_decision()[0]
    elif app.config.get('H', 0) == '2':
        response = human.get_decision(game)[0]
    else:
        response = ensemble.get_decision(game)

    # Output
    if not app.config.get('SILENT', False):
        # Temporary to monitor round change
        print(game.state_recap(short=True))
        if 'city' in response.parameters and game.cities[response.parameters['city']].outbreak:
            print('Action for Pathogen: ' + str(game.cities[response.parameters['city']].outbreak.pathogen.name))
        print(response.build_action())

    # Observer
    if not app.config.get('NO_OBS', False):
        Observer(game, response, app.config.get('SEED', 'unknown'))

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
    parser = argparse.ArgumentParser(description='IC20 Contribution Flask Based Development Server -- Do not use for production purposes')
    parser.add_argument('--seed', type=str, help='A custom seed to know for observation purposes', default='unknown')
    parser.add_argument('--silent', help='Remove any output of the game', action='store_true')
    parser.add_argument('--port', type=str, help='Port for server', default='5000')
    parser.add_argument('--no_obs', help='Disable Observer', action='store_true')
    parser.add_argument('--h', type=str, help='Used for switching between heuristics', default='0')

    args = parser.parse_args()
    app.config['SEED'] = args.seed
    app.config['SILENT'] = args.silent
    app.config['NO_OBS'] = args.no_obs
    app.config['H'] = args.h

    if args.silent:
        # Mute Flask completely
        import logging

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

    app.run(port=args.port)
