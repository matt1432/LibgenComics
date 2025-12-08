class LibgenException(Exception):
    pass


class LibgenBadGatewayException(LibgenException):
    pass


class LibgenMaxUserConnectionsException(LibgenException):
    pass


class LibgenNginxException(LibgenException):
    pass


class LibgenRateLimitedException(LibgenException):
    pass


class LibgenRequestURITooLargeException(LibgenException):
    pass


class LibgenSSLHandshakeFailedException(LibgenException):
    pass


class LibgenTimeoutException(LibgenException):
    pass
