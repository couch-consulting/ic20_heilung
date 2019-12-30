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

    def recalculate_costs_for_points(self, points):
        """
        Recalculates the costs of actions with dynamic costs to be in range for the specified number of points
        only if they are possible for the specified amount of points at all
        If they are not possible for the amount of points or do not have dynamic costs, no changes will be made
        :param points: maximal points available
        :return the object itself
        """
        if self.type in ["closeAirport", "closeConnection", "putUnderQuarantine"]:
            # Check if alternative round number would be possible
            max_rounds_for_points = self.get_max_rounds(points)
            if self.get_max_rounds(points) > 0:
                # Adapt round and costs of object
                self.parameters['rounds'] = max_rounds_for_points
                self.costs = self.get_costs(max_rounds_for_points)
        return self
