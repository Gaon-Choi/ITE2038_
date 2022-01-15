import psycopg2 as pg

conn = None

# default postgres settings
db_connection_info = {"host": "localhost", "user": "postgres", "dbname": "postgres", "port": 5432}

# TODO: Override connection info
# when postgres runs on docker container
db_connection_info["host"] = "localhost"  # windows, macOS
# db_connection_info["host"] = "172.17.0.1"  # linux
db_connection_info["port"] = 54321
db_connection_info["password"] = 1234
db_connection_info["dbname"] = "baedal"

db_connection_str = "host={host} user={user} dbname={dbname} password={password} port={port}".format(
    **db_connection_info
)


def get_db_connection():
    print("Connecting To: ", db_connection_str)
    conn = pg.connect(db_connection_str)
    return conn


try:
    conn = get_db_connection()
except Exception as err:
    print("Cannot Create DB Connection", err)
