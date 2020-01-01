import argparse
import sys

from flask import Flask, abort, g, request

from heilung.builders.action import ActionBuilder
from heilung.cli_game.observer import Observer
from heilung.heuristics.human.human import Human
from heilung.models import Game

app = Flask(__name__)

action_plan = list()


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    if request.json.get('error') is not None:
        print(request.json.get('error'))

    game = Game(request.json)

    # Heuristics
    # Human heuristic response
    human = Human(game)
    response = human.get_decision()[0]  # 0 := most important

    # # Example for random iterations
    # action_builder = ActionBuilder(game)
    # action_list = action_builder.get_actions()
    # response = action_builder.random_action(action_list)

    # Output
    if (not app.config['SHORT'] or game.outcome in ['win', 'loss']) and not app.config['SILENT']:
        # Temporary to monitor round change
        print(game.state_recap(short=True))
        print(response.build_action())

    # Observer
    obs = Observer(game, response, app.config['SEED'])

    return response.build_action()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IC20 Contribution Flask Based Server')
    parser.add_argument('--seed', type=str, help='A custom seed to know for observation purposes', default='unknown')
    parser.add_argument('--short', help='Print only a view game details', action='store_true')
    parser.add_argument('--silent', help='Remove any output of the game', action='store_true')

    args = parser.parse_args()
    app.config['SEED'] = args.seed
    app.config['SHORT'] = args.short
    app.config['SILENT'] = args.silent

    if args.silent:
        # Mute Flask completely
        import logging

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

    app.run()
