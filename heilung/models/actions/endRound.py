from heilung.models.action import Action


class EndRound(Action):
    """Ends the current round. No further action can be executed. Next game state will be calculated by game engine.
    """

    def __init__(self):
        costs = 0
        action_type = "endRound"
        parameters = {}
        super().__init__(action_type, costs, parameters)
