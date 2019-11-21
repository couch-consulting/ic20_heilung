from flask import Flask, request, abort, jsonify

from heilung.models import Game


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if not request.json:
        abort(400)

    game = Game(request.json)

    return jsonify({"type": "endRound"})


if __name__ == '__main__':
    app.run()
