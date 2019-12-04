from flask import Flask, request, abort, g

from heilung.models import Game
from heilung.models.actions import EndRound
from heilung.cli_game.play_game import play
from heilung.cli_game.observer import Observer
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
    # print(game.state_recap())

    # # Example for cli game [tip: adapt timeout of test program]
    # return play()

    obs = Observer(game)

    global action_plan
    if len(action_plan) > 0:
        return action_plan.pop(0).build_action()


    action_plan = obs.get_action_plan()

    return action_plan.pop(0).build_action()

    # Example for endRound
    action = EndRound().build_action()
    return action


if __name__ == '__main__':
    app.run()
