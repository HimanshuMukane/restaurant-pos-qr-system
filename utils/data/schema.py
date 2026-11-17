from psycopg.rows import dict_row
from .core import connect_db

def init_db(_ignored=None, schema_file="schema.pg.sql"):
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with connect_db() as conn:
        with conn.cursor() as c:
            c.execute(schema_sql)