from flask import Flask, request, abort, jsonify

from heilung.models import Game
from heilung.models.actions import EndRound

app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    game = Game(request.json)
    print(game.round)

    # Example for endRound
    action = EndRound()
    return action.build_action()


if __name__ == '__main__':
    app.run()
