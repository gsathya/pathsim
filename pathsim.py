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

    return descs

def find_desc(descs, consensus_paths):
    with reader.DescriptorReader(consensus_paths) as desc_reader:
        descs_per_consensus = []
        # this is O(n*n). optimize.
        for router in desc_reader:
            matched_descs = descs.get(router.fingerprint, None)
            if matched_descs:
                published = timestamp(router.published)
                selected_desc = matched_descs[0]
                for desc in matched_descs:
                    if desc.unix_timestamp <= published and desc.unix_timestamp >= selected_desc.unix_timestamp:
                        selected_desc = desc
                # server descs don't have flags, lets steal
                # it from the consensus
                selected_desc.flags = router.flags
                descs_per_consensus.setdefault(router.document.valid_after, []).append(selected_desc)

    return descs_per_consensus

def port_filter(desc, port):
    return desc.exit_policy.can_exit_to(port=port)


def family_filter(desc, families):
    return any(fp in families for fp in desc.family)

# make modular for diff subnets
def subnet_filter(desc, ip):
    def find_prefix(ip):
        return '.'.join(ip.split('.')[:-1])

    return find_prefix(desc.address) == find_prefix(ip)

def flag_filter(desc, flag):
    # desc is from ns doc, not server desc
    # flags is not present in server desc
    return flag in desc.flags

def calculate_bw(desc):
    return min(desc.average_bandwidth, desc.burst_bandwidth, desc.observed_bandwidth)

def find_cw(desc, weights, position):
    bw = desc.calculate_bw(desc)
    flags = desc.flags

    guard = 'Guard' in flags
    exit = 'Exit' in flags

    # improve this by writing some py magic
    if position == 'guard':
        if guard and exit:
            bw *= weights['Wgd']
        elif guard:
            bw *= weights['Wgg']
        else:
            bw *= weights['Wgm']
    elif position == 'middle':
        if guard and exit:
            bw *= weights['Wmd']
        elif guard:
            bw *= weights['Wgm']
        elif exit:
            bw *= weights['Wme']
        else:
            bw *= weights['Wmm']
    elif position == 'exit':
        if guard and exit:
            bw *= weights['Wed']
        elif guard:
            bw *= weights['Weg']
        elif exit:
            bw *= weights['Wee']
        else:
            bw *= weights['Wed']

    return bw

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
