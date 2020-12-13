import contextlib

import aiopg

from service import config
from service.entities import SiteCheck, Event


async def postgres_pool_factory(config):
    return await aiopg.create_pool(**config)


@contextlib.asynccontextmanager
async def postgres_cursor(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            yield cursor


class SiteCheckPgManager:

    table = "sites"

    def __init__(self, cursor):
        self._cursor = cursor

    async def create(self, url, regexp):
        await self._cursor.execute(
            f"""
            INSERT INTO {self.table} (url, regexp)
            VALUES (%s, %s)
            RETURNING (id)
        """,
            (url, regexp),
        )
        (site_check_id,) = await self._cursor.fetchone()
        return SiteCheck(site_check_id, url, regexp)

    async def get_by_id(self, site_id):
        await self._cursor.execute(
            f"""
            SELECT id, url, regexp
            FROM {self.table}
            WHERE id = %s
        """,
            (site_id,),
        )
        raw_entity = await self._cursor.fetchone()
        if raw_entity is not None:
            return SiteCheck(*raw_entity)
        return None

    async def get_all(self):
        await self._cursor.execute(
            f"""
            SELECT id, url, regexp
            FROM {self.table}
        """
        )
        while True:
            raw_entities = await self._cursor.fetchmany(config.PG_FETCH_CHUNK_SIZE)
            if not raw_entities:
                break
            for raw_entity in raw_entities:
                yield SiteCheck(*raw_entity)

    async def delete_all(self):
        await self._cursor.execute(
            f"""
            DELETE
            FROM {self.table}
        """
        )

    async def create_pg_schema(self):
        # assume we can prevent duplicates by url to avoid duplicate checks, so only one regexp
        # can be specified in this case
        await self._cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id SERIAL PRIMARY KEY,
                url VARCHAR(255) UNIQUE,
                regexp VARCHAR(255)
            )"""
        )


class EventPgManager:

    table = "events"

    def __init__(self, cursor):
        self._cursor = cursor

    async def create(self, created_at, url, duration, status_code, regexp_found):
        await self._cursor.execute(
            f"""
            INSERT INTO {self.table} (created_at, url, duration, status_code, regexp_found)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING (id)
        """,
            (created_at, url, duration, status_code, regexp_found),
        )
        (event_id,) = await self._cursor.fetchone()
        return Event(event_id, created_at, url, duration, status_code, regexp_found)

    async def get_by_id(self, site_id):
        await self._cursor.execute(
            f"""
            SELECT id, created_at, url, duration, status_code, regexp_found
            FROM {self.table}
            WHERE id = %s
        """,
            (site_id,),
        )
        raw_entity = await self._cursor.fetchone()
        if raw_entity is not None:
            return Event(*raw_entity)
        return None

    async def get_all(self):
        await self._cursor.execute(
            f"""
            SELECT id, created_at, url, duration, status_code, regexp_found
            FROM {self.table}
        """
        )
        while True:
            raw_entities = await self._cursor.fetchmany(config.PG_FETCH_CHUNK_SIZE)
            if not raw_entities:
                break
            for raw_entity in raw_entities:
                yield Event(*raw_entity)

    async def delete_all(self):
        await self._cursor.execute(
            f"""
            DELETE
            FROM {self.table}
        """
        )

    async def create_pg_schema(self):
        # there are no indexes for this table, however they are can be added for appropriate use
        # cases
        await self._cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP,
                url VARCHAR(255),
                duration FLOAT,
                status_code INT NULL,
                regexp_found BOOL NULL
            )"""
        )


async def ensure_db_configured(pool):
    async with postgres_cursor(pool) as cursor:
        await SiteCheckPgManager(cursor).create_pg_schema()
        await EventPgManager(cursor).create_pg_schema()
