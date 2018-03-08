import json


def format_message(message_string_json):
    '''
    Format messages from icoming strings.
    Makes sure that the message has correct structure.

    Takes a json formatted string and returns a dict.
    >>> format_message('{"foo": "bar"}')
    {'foo': 'bar'}

    If the json format is wrong, raise a ValueError.
    '''
    try:
        message_dict = json.loads(message_string_json)
    except json.decoder.JSONDecodeError as e:
        raise ValueError('Input is not in correct JSON format: "{}"'.format(message_string_json)) from None
    return message_dict

if __name__ == '__main__':
    import doctest
    doctest.testmod()
