import datetime

def timestamp(time):
    """
    Returns UNIX timestamp
    """
    time_diff = time - datetime.datetime(1970, 1, 1)
    timestamp = td.days*24*60*60 + td.seconds
    return timestamp
