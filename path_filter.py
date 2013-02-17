class PathFilter:
    def validate(self, path):
        raise NotImplementedError

class SubnetFilter(Filter):
    """
    Takes IPv4 addresses as strings and validates if the first two bytes
    are equal.
    """
    # XXX: Do IPv4 checks initially - use stem helper methods.
    def validate(self, address1, address2):
        return address1.rsplit('.', 1)[0] == address2.rsplit('.', 1)[0]
