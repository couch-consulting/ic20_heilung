from heilung.models.action import Action


class EndRound(Action):
    """Ends the current round. No further action can be executed. Next game state will be calculated by game engine.
    """

    def __init__(self):
        """Generate an endRound Action object
        """
        action_type = "endRound"
        parameters = {}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 0

    @staticmethod
    def is_possible():
        return True
