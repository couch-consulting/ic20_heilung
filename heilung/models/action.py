class Action(object):
    """Basic Action Model
    """

    def __init__(self, action_type, costs, parameters):
        """
        :param action_type: type of action
        :param costs: Number of points the action costs
        :param parameters: action specific parameters as a dict
        """
        self.type = action_type
        self.costs = costs
        self.parameters = parameters

    def build_action(self):
        """
        Generic build action function
        (Put as method for possible changes later, could also be just a property)
        :return: JSON Object of the action
        """
        # Merge dict of type with parameters
        action = {"type": self.type, **self.parameters}

        return action
