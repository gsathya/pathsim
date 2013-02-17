class PathFilter:
    def validate(self, path):
        raise NotImplementedError

class SubnetFilter(PathFilter):
    """
    Takes a path and returns true if no two relays belong to same /16 subnet
    """
    def validate(self, path):
        """
        :param list path: list of relays in path (maybe create a Path class)
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
        :param list path: list of relays in path (maybe create a Path class)
        """
        unique_path = set([router.fingerprint for router in path])

        return len(unique_path) == len(path)
