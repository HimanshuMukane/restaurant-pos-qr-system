from utils.data.core import connect_db, MySQLCompatConnection, MySQLCompatCursor
from . import rows, errors

def connect(*args, **kwargs):
    return connect_db()
