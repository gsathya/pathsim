class FilterList:
    """
    Maintain list of filters
    """
    def __init__(self, filters=[], descs=None):
        self.filters = filters
        self.descs = descs

    def add_filter(self, filter):
        """
        :param filter: filter is a filter object or list of filters objects
        """
        if isinstance(filter, list):
            self.filters.extend(filter)
        else:
            self.filters.append(filter)

    def execute(self, router):
        """
        :param router: router object
        """
        for router_filter in self.filters:
            if not router_filter.validate(router):
                return False

        return True

    def validate(self):
        """
        Return dict of all routers that conform to the filters
        """
        return dict(filter(lambda (key, value): self.execute(value[0]), self.descs.items()))

class RouterFilter:
    def validate(self, router):
        raise NotImplementedError

class FlagFilter(RouterFilter):
    """
    Return 'inverse' if given flag is present
    """
    def __init__(self, flag, consensus, inverse=True):
        """
        :param consensus: dict of all relays in consensus
        :param str flag: flag to be checked
        """
        #XXX: check if 'flag' is a valid flag string?
        self.flag = flag
        self.consensus = consensus
        self.inverse = inverse

    def validate(self, router):
        """
        :param router: router object
        """
        try:
            if self.flag in self.consensus[router.fingerprint].flags:
                return self.inverse
            else:
                return not self.inverse
        except:
                return not self.inverse

class PortFilter(RouterFilter):
    """
    Returns true if there is *some* ip that relay will exit to port.
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

class HibernateFilter(RouterFilter):
    """
    Returns true if router is not hibernating
    """
    def validate(self, router):
        """
        :param router: router object
        """
        return not router.hibernating

class MinBWFilter(RouterFilter):
    """
    Returns true if router's bw is above min bw
    """
    def __init__(self, bw, consensus):
        """
        :param int bw: minimum bandwidth
        :param consensus: dict of all relays in consensus
        """
        self.bw = bw
        self.consensus = consensus

    def validate(self, router):
        """
        :param router: router object
        """
        return self.consensus[router.fingerprint].bandwidth > self.bw

class PathFilter:
    def validate(self, path):
        raise NotImplementedError

class SubnetFilter(PathFilter):
    """
    Takes a path and returns true if no two relays belong to same /16 subnet
    """
    def validate(self, path):
        """
        :param list path: list of relays in a path
        """
        while path:
            relay = path.pop()
            # XXX: Do IPv4 checks  - use stem helper methods.
            address = relay.address.rsplit('.', 1)[0]

            for relay in path:
                if address == relay.address.rsplit('.', 1)[0]:
                    return False

        return True

class UniqueFilter(PathFilter):
    """
    Takes a path and returns true if no two same relays are present in the path.
    """
    def validate(self, path):
        """
        :param list path: list of relays in a path
        """
        unique_path = set([router.fingerprint for router in path])

        return len(unique_path) == len(path)

class FamilyFilter(PathFilter):
    """
    Takes a path and returns true if no two relays belonging to same family
    are present in the given path.
    """
    def validate(self, path):
        """
        :param list path: list of relays in a path
        """

        while path:
            relay = path.pop()
            fp = '$'+relay.fingerprint
            nick = relay.nickname
            family = relay.family

            for relay in path:
                for member in relay.family:
                    if member == fp or member == nick:
                        if ('$'+relay.fingerprint in family or
                            relay.nickname in family):
                            return False
        return True
