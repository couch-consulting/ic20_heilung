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

    # Temporary to monitor round change
    print(game.state_recap(short=True))

    # Human heuristic response
    human = Human(game)
    response = human.get_decision()
    print(response.build_action())

    # Example for random iterations
    # action_builder = ActionBuilder(game)
    # action_list = action_builder.get_actions()
    # response = action_builder.random_action(action_list)

    # Observer
    obs = Observer(game, response)

    return response.build_action()


if __name__ == '__main__':
    app.run()
