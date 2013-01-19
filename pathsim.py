import os
import sys
import datetime
import pickle

from collections import defaultdict

import stem.descriptor.reader as reader

def timestamp(t):
    """Returns UNIX timestamp"""
    td = t - datetime.datetime(1970, 1, 1)
    ts = td.days*24*60*60 + td.seconds
    return ts

def process_server_desc(paths):
    descs = {}

    with reader.DescriptorReader(paths) as desc_reader:
        for desc in desc_reader:
            desc.unix_timestamp = timestamp(desc.published)
            descs.setdefault(desc.fingerprint, []).append(desc)
            print desc

    return descs

def find_desc(descs, consensus_paths):
    with reader.DescriptorReader(consensus_paths) as desc_reader:
        # this is O(n*n). optimize.
        for router in desc_reader:
            matched_descs = descs.get(router.fingerprint, None)
            if matched_descs:
                published = timestamp(router.published)
                selected_desc = matched_descs[0]
                for desc in matched_descs:
                    if desc.unix_timestamp <= published and desc.unix_timestamp >= selected_desc.unix_timestamp:
                        selected_desc = desc
                print selected_desc.fingerprint

if __name__ == "__main__":
    desc_path = []
    consensus_path = []

    for dirpath, dirname, filenames in os.walk(sys.argv[1]):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if 'desc' in dirpath:
                desc_path.append(path)
            elif 'consensus' in dirpath:
                consensus_path.append(path)

    print desc_path, consensus_path

    try:
        with open('server_desc.pkl', 'rb') as input_pickle:
            descs = pickle.load(input_pickle)
    except:
        descs = process_server_desc(desc_path)
        with open('server_desc.pkl', 'wb') as output_pickle:
            pickle.dump(descs, output_pickle)

    find_desc(descs, consensus_path)
