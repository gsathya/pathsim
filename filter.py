class Filter:
    def validate(self, router):
        raise NotImplementedError

class RouterFilters:
    def __init__(self):
        self.filters = []

    def add_filter(self, filter):
        self.filters.append(filter)

    def execute(self, descriptor):
        for router_filter in self.filters:
            if not router_filter.validate(descriptor):
                return False
        return True

class PortFilter(Filter):
    """
    Returns if there is *some* ip that relay will exit to on port.
    """
    def __init__(self, port):
        self.port = port

    def validate(self, router):
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
    Takes IPv4 addresses as strings and validates if the first two bytes
    are equal.
    """
    # XXX: Do IPv4 checks initially - use stem helper methods.
    def validate(self, address1, address2):
        return address1.rsplit('.', 1)[0] == address2.rsplit('.', 1)[0]
