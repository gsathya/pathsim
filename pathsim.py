import os
import sys
import pickle
import logging
from collections import defaultdict

import stem.descriptor.reader as reader

def process_server_desc(paths):
    descs = {}

    with reader.DescriptorReader(paths, validate=False) as desc_reader:
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

    desc_path = [sys.argv[1]]
    consensus_path =[sys.argv[2]]

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("Starting pathsim.")

    print desc_path, consensus_path
