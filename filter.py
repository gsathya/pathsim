class Filter:
    def check(self, router):
        raise NotImplementedError

class RouterFilters:
    def __init__(self):
        self.filters = []

    def add_filter(self, filter):
        self.filters.append(filter)

    def execute(self, descriptor):
        for router_filter in self.filters:
            if not router_filter.check(descriptor):
                return False
        return True

class PortFilter(Filter):
    """
    Returns if there is *some* ip that relay will exit to on port.
    """
    def __init__(self, port):
        self.port = port

    def check(self, router):
        for rule in router.exit_policy:
            if (self.port >= rule.min_port and self.port <= rule.max_port and
                rule.is_accept):
                return True
            elif (self.port >= rule.min_port and self.port <= rule.max_port and
                  rule.is_address_wildcard() and not rule.is_accept):
                return False

        # if no rule matches, return True
        return True

class SubnetFilter(Filter):
    """
    Takes IPv4 addresses as strings and checks if the first two bytes
    are equal.
    """
    # XXX: Do IPv4 checks initially - use stem helper methods.
    # IPv4 checks will slow this down. Should we care enough?
    # Also, there is a more pythonic way to do this, but this is
    # faster.
    def check(self, address1, address2):
        octect = 1
        for (x, y) in zip(address1, address2):
            if x != y:
                return False
            if x == '.':
                octect += 1
            if octect > 2:
                # we have two equal octects
                return True

        if octect < 2:
            # this isn't valid ipv4
            raise ValueError('SubnetFilter needs IPv4 address strings')


