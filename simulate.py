from utils import *
import stem.descriptor.reader as reader
# read consensus file
# find correct processed desc file
# load it into memory

class Simulation:
    def __init__(self, desc_path, cons_path):
        self.valid_after = None
        self.fresh_until = None
        self.bw_weights = None
        self.bw_weightscale = None
        self.descs = None
        self.cons = {}
        self.desc_path = desc_path
        self.cons_path = cons_path

    def process_consensus(self):
        with reader.DescriptorReader([self.cons_path]) as desc_reader:
            for router in desc_reader:
                self.cons[router.fingerprint] = router
            self.valid_after = router.document.valid_after
            self.fresh_until = timestamp(router.document.fresh_until)
            self.bw_weights = router.document.bandwidth_weights
            if 'bwweightscale' in router.document.params:
                self.bw_weightscale = router.document.params['bwweightscale']
            
            
    def simulate(self):
        self.descs = process_server_desc(self.desc_path)
        self.process_consensus()

        # yucky test. think of alternative. commented out for now
        # if not len(set(self.cons.keys())) == len(set(self.descs.keys())):
        #     logging.error('No. of processed descs != No. of routers in consensus')
