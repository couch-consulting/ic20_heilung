from flask import Flask, request, abort

from heilung.models import Game
from heilung.models.actions import EndRound

app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    game = Game(request.json)

    # Temporary to monitor round change
    print(game.round)

    # Example for endRound
    action = EndRound().build_action()
    return action


if __name__ == '__main__':
    app.run()
