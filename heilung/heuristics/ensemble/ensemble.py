from ..human import human
from ..stupid import StupidHeuristic


def same(action_1, action_2):
    if action_1 and action_2 and action_1.type == action_2.type:
        if action_1.type == 'endRound':
            return True
        elif action_1.type in ['developMedication', 'developVaccine']:
            if action_1.parameters['pathogen'] == action_2.parameters['pathogen']:
                return True
        elif action_1.type == 'closeConnection':
            if action_1.parameters['fromCity'] == action_2.parameters['fromCity']:
                return True
        elif action_1.parameters['city'] == action_2.parameters['city']:
            return True
    return False


def compute_combined_rank(rl_1, rl_2):
    """
    For two given lists, calculates the rank of every action in response list 1 by increasing the action rank if it is also in response list 2
    Inputs list are stored such that the first element is most important
    :param rl_1: List of action which shall be increased
    :param rl_2: List of action which are used to increase the rank
    :return: List of tuples of actions with a rank List[(Action, int)]
    """
    new_action_rank_list = []
    for indx_1, tmp_action_1, in enumerate(rl_1, start=1):
        tmp_action_rank = 1 / indx_1

        for indx_2, tmp_action_2 in enumerate(rl_2, start=1):
            if same(tmp_action_1, tmp_action_2):
                tmp_action_rank += 1 / indx_2

        new_action_rank_list.append((tmp_action_1, tmp_action_rank))

    return new_action_rank_list


def merge_lists(rl_1, rl_2):
    """
    Merges lists of actions such that if an action is in both lists, the higher rank is inserted with that action
    and only unique entries are present
    :param rl_1: List[(Action, int)]
    :param rl_2: List[(Action, int)]
    :return: List[(Action, int)]
    """

    for (action, rank) in rl_1:
        no_similar_exists = True
        for indx, (tmp_action, tmp_rank) in enumerate(rl_2):
            if same(action, tmp_action):
                # If same
                if rank > tmp_rank:
                    # If rank is better, store in list bias stupid
                    rl_2[indx] = (tmp_action, rank)
                no_similar_exists = False
                break

        if no_similar_exists:
            rl_2.append((action, rank))

    return rl_2


def get_decision(game: 'Game'):
    stupid = StupidHeuristic(game)
    stupid_rl = stupid.get_decision()
    human_rl = human.get_decision(game)

    list_human = compute_combined_rank(human_rl, stupid_rl)
    list_stupid = compute_combined_rank(stupid_rl, human_rl)

    merged_list = merge_lists(list_human, list_stupid)

    # Sort for best
    merged_list.sort(key=lambda x: x[1], reverse=True)

    # Return most important value
    return merged_list[0][0]
