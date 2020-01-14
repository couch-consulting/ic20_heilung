from heilung.models.action import Action


class DevelopMedication(Action):
    """Starts the development of the medication against a specified pathogen. This takes 3 rounds. The pathogen must
    have had an outbreak in the given game so far.
    """

    def __init__(self, pathogen, input_is_str=False):
        """Generates on object of this action

        Arguments:
            pathogen {Opional[Pathogen, str]} -- pathogen object of the pathogen for which a medication shall be developed

        Keyword Arguments:
            input_is_str {bool} -- Whether the Pathon is either a string or Pathogen object (default: {False})
        """
        action_type = "developMedication"
        if input_is_str:
            parameters = {"pathogen": pathogen}
        else:
            parameters = {"pathogen": pathogen.name}
        super().__init__(action_type, self.get_costs(), parameters)

    @staticmethod
    def get_costs():
        return 20

    @staticmethod
    def is_possible(game, pathogen):
        # "Is possible for this game"

        # Game has enough points, the medication is not already developed and is not getting developed right now
        if game.points >= DevelopMedication.get_costs() and \
                pathogen not in game.pathogens_with_medication \
                and pathogen not in game.pathogens__with_developing_medication:
            return True
        return False
