from flask import Flask, request, abort

from heilung.models import Game
from heilung.models.actions import EndRound
from heilung.cli_game.play_game import play
app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    game = Game(request.json)

    # Temporary to monitor round change
    print(game.state_recap())

    # # Example for cli game [tip: adapt timeout of test program]
    # return play()

    # Example for endRound
    action = EndRound().build_action()
    return action


if __name__ == '__main__':
    app.run()
