

BOOLEANS = {
    0: False, 1: True,
    '0': False, '1': True,
    'false': False, 'true': True,
    'False': False, 'True': True
}

def convert_to_boolean(val):
    if val not in BOOLEANS:
        raise ValueError("invalid literal for convert_to_boolean(): %r" % (val,))
    return BOOLEANS[val]

