from flask import Flask, request, abort, g

from heilung.models import Game
from heilung.models.actions import EndRound
from heilung.cli_game.play_game import play
from heilung.cli_game.observer import Observer
from heilung.models import actions
from heilung.models.events.sub_event.pathogen import Pathogen
from heilung.builders.action import ActionBuilder

app = Flask(__name__)

action_plan = list()

# Testing vars
test_city = ""
counter1 = 0
counter2 = 0

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

    # For testing specif use cases
    input("Press Enter to continue...\n")

    # # Test Develop and Deploy Vaccine
    # pat = Pathogen('N5-10', "", "", "", "")
    # global counter1, counter2
    # if game.round == 1 and counter1 == 0:
    #     counter1 = 1
    #     return actions.DevelopVaccine(pat).build_action()
    # if game.round == 7 and counter2 == 0:
    #     counter2 = 1
    #     global test_city
    #     test_city = game.get_cities_with_pathogen(pat)[0]
    #     print(len(game.get_cities_with_pathogen(pat)))
    #     print(test_city.__dict__)
    #     print(test_city.outbreak.pathogen.name)
    #     return actions.DeployVaccine(test_city, pat).build_action()
    # if game.round == 8:
    #     print(game.cities[test_city.name].__dict__)


    response = action_list[-1].build_action()

    print(response)
    return response

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
