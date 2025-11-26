class LibgenBadGatewayException(Exception):
    pass


class LibgenMaxUserConnectionsException(Exception):
    pass


class LibgenNginxException(Exception):
    pass


class LibgenRateLimitedException(Exception):
    pass


class LibgenRequestURITooLargeException(Exception):
    pass


class LibgenTimeoutException(Exception):
    pass
