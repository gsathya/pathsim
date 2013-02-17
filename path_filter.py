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
