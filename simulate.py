from utils import *
from filters import *

import stem.descriptor.reader as reader

class Circuit:
    def __init__(self):
        self.time = None
        self.fast = None
        self.stable = None
        self.internal = None
        self.dirty_time = None
        self.ports = None
        self.path = None

class Simulation:
    def __init__(self, desc_path, cons_path):
        self.document = None
        self.descs = None
        self.consensus = {}
        self.desc_path = desc_path
        self.cons_path = cons_path
        self.guards = {}
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

    def get_position_weights(self, routers, position, bwweightscale):
        """
        Computes the consensus "bandwidth" weighted by position weights.
        """
        weights = {}
        for router in routers.keys():
            bw = float(self.consensus[router].bandwidth)
            weight = float(get_bw_weight(router, position)) / float(bwweightscale)
            weights[router] = bw * weight

        return weights

    def get_weighted_routers(self, routers, weights):
        """
        Takes list of routers (rel_stats) and weights (as a dict) and outputs
        a list of (router, cum_weight) pairs, where cum_weight is the cumulative
        probability of the routers weighted by weights.
        """
        # compute total weight
        total_weight = 0
        for router in routers:
            total_weight += weights[router]
        # create cumulative weights
        weighted_routers = []
        cum_weight = 0
        for router in routers:
            cum_weight += weights[router]/total_weight
            weighted_routers.append((router, cum_weight))

        return weighted_routers


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

    def get_bw_weight(self, router, position):
        """
        Returns weight to apply to relay's bandwidth for given position.

        position: position for which to find selection weight
        bw_weights: bandwidth_weights from NetworkStatusDocumentV3 consensus
        """

        bw_weight = None
        flags = router.flags
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

        # yucky test. think of alternative. commented out for now
        # if not len(set(self.consensus.keys())) == len(set(self.descs.keys())):
        #     logging.error('No. of processed descs != No. of routers in consensus')

        self.rotate_guards()
        exit_nodes = self.get_exit_nodes(fast=True, stable=True)
