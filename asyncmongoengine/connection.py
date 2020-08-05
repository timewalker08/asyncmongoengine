

from motor.motor_asyncio import AsyncIOMotorClient

DEFAULT_CONNECTION_NAME = "default"
DEFAULT_DATABASE_NAME = "test"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 27017

_connection_settings = {}
_connections = {}
_dbs = {}

class ConnectionFailure(Exception):
    """Error raised when the database connection can't be established or
    when a connection with a requested alias can't be retrieved.
    """

    pass


def _build_connection_settings(
    db=None,
    name=None,
    host=None,
    port=None,
    username=None,
    password=None,
    authentication_source=None,
    authentication_mechanism=None,
    **kwargs
):
    conn_settings = {
        "name": name or db or DEFAULT_DATABASE_NAME,
        "host": host or DEFAULT_HOST,
        "port": port or DEFAULT_PORT,
        "username": username,
        "password": password,
        "authentication_source": authentication_source,
        "authentication_mechanism": authentication_mechanism,
    }

    conn_host = conn_settings["host"]
    if isinstance(conn_host, str):
        conn_settings["host"] = [conn_host]

    conn_settings.update(kwargs)
    return conn_settings

def register_connection(
    alias,
    db=None,
    name=None,
    host=None,
    port=None,
    username=None,
    password=None,
    authentication_source=None,
    authentication_mechanism=None,
    **kwargs
):
    conn_settings = _build_connection_settings(
        db=db,
        name=name,
        host=host,
        port=port,
        username=username,
        password=password,
        authentication_source=authentication_source,
        authentication_mechanism=authentication_mechanism,
        **kwargs
    )
    _connection_settings[alias] = conn_settings


def get_connection(alias=DEFAULT_CONNECTION_NAME, reconnect=False):
    """Return a connection with a given alias."""
    if alias in _connections:
        return _connections[alias]

    if alias not in _connection_settings:
        if alias == DEFAULT_CONNECTION_NAME:
            msg = "You have not defined a default connection"
        else:
            msg = 'Connection with alias "%s" has not been defined' % alias
        raise ConnectionFailure(msg)

    raw_conn_settings = _connection_settings[alias].copy()
    raw_conn_settings.pop("name")
    raw_conn_settings.pop("authentication_source")
    raw_conn_settings.pop("authentication_mechanism")

    connection_class = AsyncIOMotorClient
    _connections[alias] = connection_class(**raw_conn_settings)
    
    return _connections[alias]

def get_db(alias=DEFAULT_CONNECTION_NAME):
    if alias not in _dbs:
        conn = get_connection(alias)
        conn_settings = _connection_settings[alias]
        db = conn[conn_settings["name"]]
        _dbs[alias] = db
    return _dbs[alias]

def connect(db=None, alias=DEFAULT_CONNECTION_NAME, **kwargs):
    if alias in _connections:
        prev_conn_setting = _connection_settings[alias]
        new_conn_settings = _build_connection_settings(db, **kwargs)
        if new_conn_settings != prev_conn_setting:
            err_msg = (
                "A different connection with alias `{}` was already "
                "registered. Use disconnect() first"
            ).format(alias)
            raise ConnectionFailure(err_msg)
    else:
        register_connection(alias, db, **kwargs)

    return get_connection(alias)