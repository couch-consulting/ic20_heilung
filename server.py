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

    obs = Observer(game)

    action_builder = ActionBuilder(game)
    action_list = action_builder.get_actions()

    # Example for random iterations
    response = action_builder.random_action(action_list)

    return response.build_action()


if __name__ == '__main__':
    app.run()
