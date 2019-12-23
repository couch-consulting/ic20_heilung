# Global vars


class Scalegroup:
    """
    Class to keep values always in scale between 0-1
    By instead of every increasing the values always decrease them
    Thus compared to other instances it is the question: "Who was decreased the fewest"
    """

    def __init__(self, scale_group):
        self.sg = scale_group
        self.MAX_PER_CONST = 1

        # Maybe use later
        self.inverted = []

        # Define influence levels for less important dependencies
        self.influence_lvl1 = 0.1
        self.influence_lvl2 = 0.3
        self.influence_lvl3 = 0.5

    def increase_on_dependency(self, val_to_increase_name, dependent_val, inverted=False):
        """
        Increase the rank of a given value based on a 2nd given value
        :param val_to_increase_name: rank to increase
        :param dependent_val: value that influences the rank
        :param inverted: indicate that lower value should have higher influence than higher values
        """
        if dependent_val < 0 or dependent_val > 1:
            raise ValueError("dependent_val must be value between 0 and 1")

        # Current method: only increases the value here, the higher the dependent_val the higher the increase
        # Make sure it does not become 0
        # - if dependent_val would be 0 the increase would be 0
        # Assumption: this makes value step out of their scale, thus they must be rescaled at some point
        # This can be done directly by instead of increasing the value you just decrease all other values
        # Thus the value which shall be increased is more important
        # - if dependent_val is 1 the decrease to other values should not make them zero

        for item_name, rank in self.sg.items():
            if item_name == val_to_increase_name:
                continue

            # max for numerical robustness and avoid 0-values
            if inverted:
                # if inverted, then the lower the dependent_val the higher the influence
                self.sg[item_name] = rank * max(dependent_val, 0.00001)
            else:
                self.sg[item_name] = rank * max((1 - dependent_val), 0.00001)

    def decrease_on_dependency(self, val_to_decrease_name, dependent_val, inverted=False):
        """
        Decrease the rank directly
        :param val_to_decrease_name: rank to decrease
        :param dependent_val: value that influences the rank
        :param inverted: indicate that lower value should have higher influence than higher values
        """
        if dependent_val < 0 or dependent_val > 1:
            raise ValueError("dependent_val must be value between 0 and 1")

        if inverted:
            self.sg[val_to_decrease_name] = self.sg[val_to_decrease_name] * max(dependent_val, 0.00001)
        else:
            self.sg[val_to_decrease_name] = self.sg[val_to_decrease_name] * max((1 - dependent_val), 0.00001)

    def apply_bias(self, value_to_decrease_name, bias_per):
        """
        Reduces the value of a given rank by a defined bias percentage
        :param value_to_decrease_name: rank percentage that shall be reduced
        :param bias_per: % of how much rank should be weighed as
        """
        if bias_per < 0 or bias_per > 1:
            raise ValueError("bias_per must be value between 0 and 1")

        self.sg[value_to_decrease_name] = self.sg[value_to_decrease_name] * bias_per

    def invert_rank(self, name):
        """
        Invert rank of value such that it is still inside the defined scale
        :param name: name of value to invert
        :return: inverted value
        """
        if self.sg[name] > self.MAX_PER_CONST:
            raise ValueError("value to invert is higher than max value")
        self.inverted.append(name)
        self.sg[name] = self.MAX_PER_CONST - self.sg[name]

    # Utils
    @property
    def max_val(self):
        return max([value for key, value in self.sg.items()])

    def print_recap(self):
        output = ""
        for key, value in self.sg.items():
            output += "%s: %s \n" % (key, str(value))
        print(output)

    def rescale(self):
        """
        Normalizes values of scale group to be between 0-1
        """
        max_val = self.max_val
        for key, value in self.sg.items():
            self.sg[key] = self.MAX_PER_CONST / max_val * value
