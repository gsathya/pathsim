from utils import *
import stem.descriptor.reader as reader

class Simulation:
    def __init__(self, desc_path, cons_path):
        self.document = None
        self.descs = None
        self.cons = {}
        self.desc_path = desc_path
        self.cons_path = cons_path
        self.guards = {}
        self.circuits = []
        self.exit_circuits = []
        self.internal_circuits = []

    def process_consensus(self):
        with reader.DescriptorReader([self.cons_path]) as desc_reader:
            for router in desc_reader:
                self.cons[router.fingerprint] = router
            self.document = router.document

    def simulate(self):
        self.descs = process_server_desc(self.desc_path)
        self.process_consensus()

        # yucky test. think of alternative. commented out for now
        # if not len(set(self.cons.keys())) == len(set(self.descs.keys())):
        #     logging.error('No. of processed descs != No. of routers in consensus')
