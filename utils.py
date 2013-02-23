import datetime
import logging

import stem.descriptor.reader as reader

def timestamp(time):
    """
    Returns UNIX timestamp
    """
    time_diff = time - datetime.datetime(1970, 1, 1)
    timestamp = time_diff.days*24*60*60 + time_diff.seconds
    return timestamp

def skip_listener(path, exception):
    logging.error("%s : %s", path, exception)

def process_server_desc(paths):
    """
    Read server descriptors and store them in dicts along with their
    timestamps.

    descs = {fingerprint : descriptor}
    """
    descs = {}
    num_desc = 0

    logging.info("Reading descriptors from %s", paths)

    with reader.DescriptorReader(paths, validate=False) as desc_reader:
        desc_reader.register_skip_listener(skip_listener)
        for desc in desc_reader:
            desc.unix_timestamp = timestamp(desc.published)
            descs.setdefault(desc.fingerprint, []).append(desc)

            num_desc += 1
            if num_desc % 10000 == 0:
                logging.info("%s descriptors processed.", num_desc)

    return descs
