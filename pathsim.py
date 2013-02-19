import os
import sys
import pickle
import argparse
import logging

from utils import timestamp

import stem.descriptor.reader as reader

# move to utils.py?
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

def find_desc(descs, consensus_paths, desc_writer):
    """
    Find descriptors pertaining to a particular consensus document
    """
    with reader.DescriptorReader(consensus_paths) as desc_reader:
        valid_after = None

        # this is O(n*n). optimize.
        for router in desc_reader:
            if valid_after != router.document.valid_after:
                # when valid_after is None we shouldn't write
                # anything
                if valid_after:
                    desc_writer(descs_per_consensus, valid_after)
                    logging.info("Descriptors - Found : %s, Not Found : %s",
                                 found, not_found)
                descs_per_consensus = []
                found, not_found = 0, 0
                valid_after = router.document.valid_after

            matched_descs = descs.get(router.fingerprint, None)
            if matched_descs:
                found += 1
                published = timestamp(router.published)
                selected_desc = matched_descs[0]
                for desc in matched_descs:
                    if (desc.unix_timestamp <= published and
                        desc.unix_timestamp >= selected_desc.unix_timestamp):
                        selected_desc = desc
                # server descs don't have flags, lets steal
                # it from the consensus
                selected_desc.flags = router.flags
                descs_per_consensus.append(selected_desc)
            else:
                not_found += 1

def descriptor_writer(output_dir):
    def write_processed_descs(descs_per_consensus, valid_after):
        file_name = valid_after.strftime('%Y-%m-%d-%H-%M-%S-descriptors')
        logging.info("Writing descs into %s", file_name)
        outpath = os.path.join(output_dir, file_name)

        with open(outpath, 'wb') as output:
            output.write('@type server-descriptor 1.0\n')
            for desc in descs_per_consensus:
                output.write(unicode(desc).encode('utf8'))
                output.write('\n')

    return write_processed_descs

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

def parse_args(parser):
    parser.add_argument("-p", "--process", help="Pair consensuses with recent descriptors",
                    action="store_true")
    parser.add_argument("-x", "--simulate", help="Do a bunch of simulated path selections using consensus from --in, processed descriptors from --out, and taking --samples",
                    action="store_true")
    parser.add_argument("-c", "--consensus", help="List of input consensus documents", default="in/consensuses")
    parser.add_argument("-d", "--descs", help="List of input descriptor documents", default='in/desc')
    parser.add_argument("-o", "--output", help="Output dir", default='out/processed-descriptors')
    parser.add_argument("-l", "--log", help="Logging level", default="DEBUG")

    return parser.parse_args()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parse_args(parser)

    if not args.process or args.simulate:
        parser.error('No action requested, add --process or --simulate')

    if not os.path.exists(args.descs):
        parser.error('%s does not exist' % args.descs)

    if not os.path.exists(args.consensus):
        parser.error('%s does not exist' % args.consensus)

    output_dir = os.path.abspath(args.output)
    if not os.path.exists(args.output):
        os.makedirs(output_dir)

    log_level = getattr(logging, args.log.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.log)

    desc_path = []
    consensus_path = []
    descs = {}

    logging.basicConfig(level=log_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("Starting pathsim.")

    if args.process:
        desc_writer = descriptor_writer(output_dir)
        descs = process_server_desc(os.path.abspath(args.descs))
        find_desc(descs, output_dir, desc_writer)
