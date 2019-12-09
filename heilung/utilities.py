from typing import List

GRADE_MAPPING = {
    '--': 0,
    '-': 1,
    'o': 2,
    '+': 3,
    '++': 4,
}


def grade_to_scalar(grade: str) -> int:
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
