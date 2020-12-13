from unittest import mock

import arq
import httpx
import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from service import config
from service.jobs import redis_pool_factory
from service.kafka import kafka_producer_factory, kafka_consumer_factory
from service.db import (
    SiteCheckPgManager,
    EventPgManager,
    postgres_pool_factory,
    postgres_cursor,
)

POSTGRES_MAINTENANCE_DB = "postgres"


@pytest.fixture(scope="session")
def pg_database():
    return f"{config.POSTGRES_DB}_test"


@pytest.fixture(scope="session")
def pg_config(pg_database):
    return dict(config.POSTGRES_CONFIG, database=pg_database)


@pytest.fixture(scope="session")
def pg_db(pg_database, pg_config):
    setup_config = dict(pg_config, database=POSTGRES_MAINTENANCE_DB)
    conn = psycopg2.connect(**setup_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {pg_database}")
    cursor.execute(f"CREATE DATABASE {pg_database}")
    cursor.close()
    conn.close()


@pytest.fixture
async def pg_pool(pg_db, pg_config):
    pool = await postgres_pool_factory(pg_config)
    yield pool
    pool.close()


@pytest.fixture
async def pg_cursor(pg_pool):
    async with postgres_cursor(pg_pool) as cursor:
        # await cursor.execute('BEGIN')
        yield cursor
        # await cursor.execute('ROLLBACK')


@pytest.fixture
async def site_check_pg_manager(pg_cursor):
    manager = SiteCheckPgManager(pg_cursor)
    await manager.create_pg_schema()
    await manager.delete_all()
    yield manager


@pytest.fixture
async def event_pg_manager(pg_cursor):
    manager = EventPgManager(pg_cursor)
    await manager.create_pg_schema()
    await manager.delete_all()
    yield manager


@pytest.fixture(scope="session")
def redis_db():
    return config.REDIS_DB + 1


@pytest.fixture(scope="session")
def redis_config(redis_db):
    return dict(config.REDIS_CONFIG, database=redis_db)


@pytest.fixture
async def redis_pool(redis_config):
    pool = await redis_pool_factory(redis_config)
    yield pool
    pool.close()


@pytest.fixture(scope="session")
def kafka_topic():
    topic = f"{config.KAFKA_TOPIC}_test"
    with mock.patch.object(config, "KAFKA_TOPIC", topic):
        yield topic


@pytest.fixture
async def kafka_producer(kafka_topic):
    producer = await kafka_producer_factory(config.KAFKA_PRODUCER_CONFIG)
    yield producer
    await producer.stop()


@pytest.fixture
async def kafka_consumer(kafka_topic):
    consumer = await kafka_consumer_factory(kafka_topic, config.KAFKA_CONSUMER_CONFIG)
    yield consumer
    await consumer.stop()


@pytest.fixture
async def http_client():
    client = httpx.AsyncClient()
    yield client
    await client.aclose()


@pytest.fixture
def ctx(http_client, pg_pool, redis_pool, kafka_producer, kafka_consumer):
    return {
        "http_client": http_client,
        "pg_pool": pg_pool,
        "redis_pool": redis_pool,
        "kafka_producer": kafka_producer,
        "kafka_consumer": kafka_consumer,
    }


@pytest.fixture
def arq_worker(redis_pool, ctx):
    def factory(**conf):
        return arq.Worker(
            redis_pool=redis_pool,
            burst=True,
            # max_burst_jobs=1,
            ctx=ctx,
            **conf,
        )

    return factory
