from flask import Flask, request, abort, g

from heilung.models import Game
from heilung.cli_game.observer import Observer
from heilung.builders.action import ActionBuilder

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

    action_builder = ActionBuilder(game)
    action_list = action_builder.get_actions()

    # Example for random iterations
    response = action_builder.random_action(action_list)

    # TODO: Check for events with no state indicator in error message
    return response.build_action()

    # obs = Observer(game)

    # global action_plan
    # if len(action_plan) > 0:
    #     return action_plan.pop(0).build_action()
    #
    #
    # action_plan = obs.get_action_plan()
    #
    # return action_plan.pop(0).build_action()


if __name__ == '__main__':
    app.run()
