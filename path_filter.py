class PathFilter:
    def validate(self, path):
        raise NotImplementedError

class SubnetFilter(PathFilter):
    """
    Takes a path and checks if two relays belong to same /16 subnet.
    Returns true if they do not.
    """
    def validate(self, path):
        """
        :param list path: list of relays in path (maybe create a Path class later?)
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
    pass
