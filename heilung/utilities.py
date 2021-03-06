GRADE_MAPPING = {
    '--': 0,
    '-': 0.25,
    'o': 0.5,
    '+': 0.75,
    '++': 1.0,
}


def grade_to_scalar(grade: str) -> float:
    """Converts the used "grades" (--, -, o, +, ++) to a value between 0 and 1

    Arguments:
        grade {str} -- The grade from the request

    Returns:
        float -- The value scaled between 0 and 1
    """
    # Catch empty string used for 'empty_city'
    if grade == '':
        return -1

    return GRADE_MAPPING[grade]
