from typing import List

GRADE_MAPPING = {
    '--': 0.01,  # not zero to have at least some computational effect and does not make everything zero
    '-': 0.25,
    'o': 0.5,
    '+': 0.75,
    '++': 1.0,
}


def grade_to_scalar(grade: str) -> float:
    """Converts the used "grades" (--, -, o, +, ++) to a value between 0 and 4

    Arguments:
        grade {str} -- The grade from the request

    Returns:
        int -- An integer representation
    """
    # Catch empty string used for 'empty_city'
    if grade == '':
        return -1

    return GRADE_MAPPING[grade]
