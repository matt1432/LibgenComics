class LibgenBadGatewayException(Exception):
    pass


class LibgenInternalServerException(Exception):
    pass


class LibgenMaxUserConnectionsException(Exception):
    pass


class LibgenNginxException(Exception):
    pass


class LibgenRateLimitedException(Exception):
    pass


class LibgenRequestURITooLargeException(Exception):
    pass


class LibgenSSLHandshakeFailedException(Exception):
    pass


class LibgenTimeoutException(Exception):
    pass
