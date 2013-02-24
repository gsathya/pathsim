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

    def get_exit_nodes(self, fast=None, stable=None, internal=None, port=None):
        filters = []
        exit_nodes = {}

        filters.extend([FlagFilter("BadExit", self.consensus, False),
                       FlagFilter("Running", self.consensus),
                       FlagFilter("Valid", self.consensus)])
        if fast:
            filters.append(FlagFilter("Fast", self.consensus))
        if stable:
            filters.append(FlagFilter("Stable", self.consensus))
        if not internal and port:
            filters.append(PortFilter(port))

        exit_filter = RouterFilterList()
        exit_filter.add_filter(filters)

        for fp, router in self.descs.items():
            if exit_filter.execute(router[0]):
                exit_nodes[fp] = router

        return exit_nodes

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
        exit_nodes = self.get_exit_nodes(True, True)
