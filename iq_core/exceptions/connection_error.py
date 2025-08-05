from .iqoption_error import IQOptionError


class ConnectionError(IQOptionError):
    """
    🇧🇷 Erros relacionados à conexão.

    🇺🇸 Connection related errors.
    """

    pass


class NetworkUnavailableError(IQOptionError):
    """
    🇧🇷 Erro ao tentar se conectar com a internet ou serviço remoto.

    🇺🇸 Error trying to connect to internet or remote service.
    """

    pass
