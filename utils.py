import datetime

def timestamp(time):
    """
    Returns UNIX timestamp
    """
    time_diff = time - datetime.datetime(1970, 1, 1)
    timestamp = time_diff.days*24*60*60 + time_diff.seconds
    return timestamp
