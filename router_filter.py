class RouterFilter:
    def validate(self):
        raise NotImplementedError

class RouterFilters:
    """
    Maintain list of routers
    """
    def __init__(self):
        self.filters = []

    def add_filter(self, filter):
        """
        :param RouterFilter filter: filter is an object of RouterFilter
        """
        self.filters.append(filter)

    def execute(self, router):
        """
        :param router: router object
        """
        for router_filter in self.filters:
            if not router_filter.validate(router):
                return False
        return True

class FlagFilter(RouterFilter):
    """
    Return true if given flag is present
    """
    def __init__(self, flag, consensus):
        """
        :param consensus: dict of all relays in consensus
        :param str flag: flag to be checked
        """
        #XXX: check if 'flag' is valid flag?
        self.flag = flag
        self.consensus = consensus

    def validate(self, router):
        """
        :param router: router object
        """
        # raise exception if not found?
        if router.fingerprint in self.consensus:
            return self.flag in consensus[router.fingerprint].flags

        return False

class PortFilter(RouterFilter):
    """
    Returns if there is *some* ip that relay will exit to port.
    """
    def __init__(self, port):
        """
        :param int port: port to be checked against
        """
        self.port = port

    def validate(self, router):
        """
        :param router: router object
        """
        for rule in router.exit_policy:
            if (self.port >= rule.min_port and self.port <= rule.max_port and
                rule.is_accept):
                return True
            elif (self.port >= rule.min_port and self.port <= rule.max_port and
                  rule.is_address_wildcard() and not rule.is_accept):
                return False

        # if no rule matches, return True
        return True
