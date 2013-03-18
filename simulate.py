from utils import *
from filters import *

import stem.descriptor.reader as reader

class Stream:
    def __init__(self, hostname=None, port=None):
        self.hostname = hostname
        self.port = port
        self.type = None
        self.time = None

class Circuit:
    def __init__(self):
        self.time = None
        self.fast = None
        self.stable = None
        self.internal = None
        self.dirty_time = None
        self.ports = None
        self.streams = None

class Simulation:
    def __init__(self, desc_path, cons_path):
        self.document = None
        self.descs = None
        self.consensus = {}
        self.desc_path = desc_path
        self.cons_path = cons_path
        self.guards = {}
        self.streams = []
        self.circuits = []
        self.exit_circuits = []
        self.internal_circuits = []

    def process_consensus(self):
        with reader.DescriptorReader([self.cons_path]) as desc_reader:
            for router in desc_reader:
                self.consensus[router.fingerprint] = router
            self.document = router.document

    def rotate_guards(self):
        pass

    def get_exit_nodes(self, fast=None, stable=None, internal=None, ip=None, port=None):
        filters = []
        exit_nodes = {}

        filters.extend([
            FlagFilter("BadExit", self.consensus, False),
            FlagFilter("Running", self.consensus),
            FlagFilter("Valid", self.consensus),
            HibernateFilter()
            ])
        if fast:
            filters.append(FlagFilter("Fast", self.consensus))
        if stable:
            filters.append(FlagFilter("Stable", self.consensus))
        if not internal and port:
            filters.append(PortFilter(port))

        exit_filter = FilterList(filters, self.descs)
        exit_nodes = exit_filter.validate()

        return exit_nodes

    def get_position_weights(self, nodes, position, bwweightscale):
        """
        Computes the consensus "bandwidth" weighted by position weights.
        """
        weights = {}
        for node in nodes.keys():
            bw = float(self.consensus[node].bandwidth)
            weight = float(self.get_bw_weight(node, position)) / float(bwweightscale)
            weights[node] = bw * weight

        return weights

    def get_weighted_nodes(self, nodes, weights):
        """
        Takes list of nodes (rel_stats) and weights (as a dict) and outputs
        a list of (node, cum_weight) pairs, where cum_weight is the cumulative
        probability of the nodes weighted by weights.
        """
        # compute total weight
        total_weight = sum(weights.values())

        # create cumulative weights
        weighted_nodes = []
        cum_weight = 0

        #XXX: shouldn't we iterate on a sorted list of nodes by weights
        for node in nodes:
            cum_weight += weights[node]/total_weight
            weighted_nodes.append((node, cum_weight))

        return weighted_nodes


    def get_weighted_exits(self, bwweightscale, fast, stable, internal, ip, port):
        """
        Returns list of (fprint,cum_weight) pairs for potential exits along with
        cumulative selection probabilities for use in a circuit with the indicated
        properties.
        """
        if not (port or internal):
            raise ValueError('get_weighted_exits() needs a port.')

        # filter exit list
        exits = get_exit_nodes(fast, stable, internal, ip, port)

        # create weights
        weights = None
        if internal:
            weights = get_position_weights(exits, cons_rel_stats, 'm',\
                        bw_weights, bwweightscale)
        else:
            weights = get_position_weights(exits, cons_rel_stats, 'e',\
                bw_weights, bwweightscale)

        return get_weighted_nodes(exits, weights)

    def get_bw_weight(self, node, position):
        """
        Returns weight to apply to relay's bandwidth for given position.

        position: position for which to find selection weight
        bw_weights: bandwidth_weights from NetworkStatusDocumentV3 consensus
        """

        bw_weight = None
        flags = self.consensus[node].flags
        weights = self.document.bandwidth_weights
        guard = 'Guard' in flags
        exit = 'Exit' in flags

        if position == 'guard':
            if guard and exit:
                bw_weight = weights['Wgd']
            elif guard:
                bw_weight = weights['Wgg']
            else:
                bw_weight = weights['Wgm']
        elif position == 'middle':
            if guard and exit:
                bw_weight = weights['Wmd']
            elif guard:
                bw_weight = weights['Wgm']
            elif exit:
                bw_weight = weights['Wme']
            else:
                bw_weight = weights['Wmm']
        elif position == 'exit':
            if guard and exit:
                bw_weight = weights['Wed']
            elif guard:
                bw_weight = weights['Weg']
            elif exit:
                bw_weight = weights['Wee']
            else:
                bw_weight = weights['Wed']

        if not bw_weight:
            raise ValueError("Bandwidth weight does not exist for %s position" %
                             position)

        return bw_weight

    def get_middle_nodes(self, fast=None, stable=None, exit=None, path=None):
        filters = []
        middle_nodes = {}

        filters.extend([
            FlagFilter("Running", self.consensus),
            HibernateFilter()
            ])
        if fast:
            filters.append(FlagFilter("Fast", self.consensus))
        if stable:
            filters.append(FlagFilter("Stable", self.consensus))

    def simulate(self):
        self.descs = process_server_desc(self.desc_path)

        # for fp in self.descs:
        #     if len(self.descs[fp]) > 1:
        #         print self.descs[fp]

        self.process_consensus()
        bwweightscale = self.document.params['bwweightscale']

        # yucky test. think of alternative. commented out for now
        # if not len(set(self.consensus.keys())) == len(set(self.descs.keys())):
        #     logging.error('No. of processed descs != No. of routers in consensus')

        self.rotate_guards()

        self.streams = [Stream(port=80)]

        for stream in self.streams:
            exit_nodes = self.get_exit_nodes(fast=True, stable=True, port=stream.port)
            exit_weights = self.get_position_weights(exit_nodes, 'exit', bwweightscale)
            weighted_exits = self.get_weighted_nodes(exit_nodes, exit_weights)
            # weighted_exits.sort(key=lambda s:s[1])
            # print self.consensus[weighted_exits[-1][0]]
            # print self.descs[weighted_exits[-1][0]][0]
