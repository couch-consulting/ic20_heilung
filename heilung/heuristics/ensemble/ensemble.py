from ..human import human
from ..stupid import StupidHeuristic


def get_decision(game: 'Game'):
    stupid = StupidHeuristic(game)
    stupid_rl = stupid.get_decision()  # list of action

    human_rl = human.get_decision(game)  # list of (action, rank) tuples

    new_actio_rank_list = []
    for indx_1, s_action in enumerate(stupid_rl, start=1):
        # Bias such that action which were more important in s_heuristic stay more important overall
        tmp_action_rank = 1.1 / indx_1

        for indx_2, (h_action, _) in enumerate(human_rl, start=1):
            if s_action and h_action and s_action.type == h_action.type:
                if s_action.type == 'endRound':
                    tmp_action_rank += 1 / indx_2
                elif s_action.type in ['developMedication', 'developVaccine']:
                    if s_action.parameters['pathogen'] == h_action.parameters['pathogen']:
                        tmp_action_rank += 1 / indx_2
                elif s_action.type == 'closeConnection':
                    if s_action.parameters['fromCity'] == h_action.parameters['fromCity']:
                        tmp_action_rank += 1 / indx_2
                elif s_action.parameters['city'] == h_action.parameters['city']:
                    tmp_action_rank += 1 / indx_2

        new_actio_rank_list.append((s_action, tmp_action_rank))

    # Sort for best
    new_actio_rank_list.sort(key=lambda x: x[1], reverse=True)

    # print(new_actio_rank_list)

    return new_actio_rank_list[0][0]
