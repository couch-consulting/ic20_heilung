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


def combine_lists(rl_1, rl_2, bias):
    new_actio_rank_list = []
    for indx_1, s_action, in enumerate(rl_1, start=1):
        # Bias such that action which were more important in s_heuristic stay more important overall
        tmp_action_rank = 1 + bias / indx_1

        for indx_2, h_action in enumerate(rl_2, start=1):
            if same(s_action, h_action):
                tmp_action_rank += 1 / indx_2

        new_actio_rank_list.append((s_action, tmp_action_rank))

    return new_actio_rank_list

def get_decision(game: 'Game'):
    stupid = StupidHeuristic(game)
    stupid_rl = stupid.get_decision()  # list of action

    # TODO neu machen mit bias und vollstädniger liste aka correct ensemble
    # TODO bedenken: 1-zu-1-identisch oder nur typ/pathogen | alle listen element bedacht und verglichen | bias
    # TODO could build training for this like # better than the other one
    human_rl = [action for (action, rank) in human.get_decision(game)]  # list of (action, rank) tuples

    list_bias_human = combine_lists(human_rl, stupid_rl, 1.35)
    list_bias_stupid = combine_lists(stupid_rl, human_rl, 2)

    for (action, rank) in list_bias_human:
        no_similar_exists = True
        for indx, (tmp_action, tmp_rank) in enumerate(list_bias_stupid):
            if same(action, tmp_action):
                # If same,
                if rank > tmp_rank:
                    list_bias_stupid[indx] = (tmp_action, rank)
                no_similar_exists = False
                break

        if no_similar_exists:
            list_bias_stupid.append((action, rank))

    new_actio_rank_list = list_bias_stupid


    # Sort for best
    new_actio_rank_list.sort(key=lambda x: x[1], reverse=True)

    # print(new_actio_rank_list)

    return new_actio_rank_list[0][0]
