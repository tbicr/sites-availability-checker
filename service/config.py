import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_CONFIG = {
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "database": POSTGRES_DB,
}


REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_DB = int(os.environ["REDIS_DB"])
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_SSL = bool(int(os.environ.get("REDIS_SSL", 0)))
REDIS_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "database": REDIS_DB,
    "password": REDIS_PASSWORD,
    "ssl": REDIS_SSL,
}

KAFKA_SERVERS = os.environ["KAFKA_SERVERS"]
KAFKA_TOPIC = "events"
KAFKA_CONSUMER_WAIT_TIMEOUT = 1000
KAFKA_CONSUMER_MAX_RECORDS = 1000

KAFKA_SECURITY_PROTOCOL = os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
KAFKA_ACCESS_KEY = os.environ.get("KAFKA_ACCESS_KEY")
KAFKA_ACCESS_CERTIFICATE = os.environ.get("KAFKA_ACCESS_CERTIFICATE")
KAFKA_CA_CERTIFICATE = os.environ.get("KAFKA_CA_CERTIFICATE")
KAFKA_SSL_CONTEXT = None
if KAFKA_SECURITY_PROTOCOL == "SSL":
    KAFKA_SSL_CONTEXT = {
        "cafile": KAFKA_CA_CERTIFICATE,
        "certfile": KAFKA_ACCESS_CERTIFICATE,
        "keyfile": KAFKA_ACCESS_KEY,
    }
KAFKA_PRODUCER_CONFIG = {
    "bootstrap_servers": KAFKA_SERVERS,
    "security_protocol": KAFKA_SECURITY_PROTOCOL,
    "ssl_context": KAFKA_SSL_CONTEXT,
}
KAFKA_CONSUMER_CONFIG = {
    "bootstrap_servers": KAFKA_SERVERS,
    "security_protocol": KAFKA_SECURITY_PROTOCOL,
    "ssl_context": KAFKA_SSL_CONTEXT,
    "group_id": "kafka_to_postgres_transfer",
    "enable_auto_commit": False,
}

FETCH_TIMEOUT = 10  # seconds
PG_FETCH_CHUNK_SIZE = 10000

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
