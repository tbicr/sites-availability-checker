import logging
from functools import partial

import arq
import httpx

from service import config
from service.db import (
    postgres_cursor,
    SiteCheckPgManager,
    EventPgManager,
    postgres_pool_factory,
    ensure_db_configured,
)
from service.entities import Event
from service.kafka import (
    put_results_to_kafka,
    kafka_producer_factory,
    kafka_consumer_factory,
)
from service.utils import fetch, regexp_check


logger = logging.getLogger()


async def redis_pool_factory(config):
    return await arq.create_pool(arq.connections.RedisSettings(**config))


async def availability_check(ctx, site_check):
    logger.info("start site availability check for url: %s", site_check.url)
    http_client = ctx["http_client"]
    kafka_producer = ctx["kafka_producer"]
    check_result, content = await fetch(http_client, site_check.url)
    check_result.regexp_found = regexp_check(site_check.regexp, content)
    await put_results_to_kafka(kafka_producer, check_result)
    logger.info("finished site availability check for url: %s", site_check.url)


async def schedule_availability_checks(ctx):
    logger.info("start availability checks scheduling")
    postgres_pool = ctx["pg_pool"]
    redis = ctx["redis_pool"]
    count = 0
    async with postgres_cursor(postgres_pool) as cursor:
        async for site_check in SiteCheckPgManager(cursor).get_all():
            await redis.enqueue_job(
                availability_check.__name__, site_check, _queue_name=AvailabilityCheckerWorkerSettings.queue_name
            )
            logger.info("scheduled site availability for url: %s", site_check.url)
            count += 1
    logger.info("finished availability checks scheduling count: %s", count)


async def kafka_to_pg_transfer(ctx):
    logger.info("start kafka to postgres transfer")
    postgres_pool = ctx["pg_pool"]
    kafka_consumer = ctx["kafka_consumer"]
    count = 0
    async with postgres_cursor(postgres_pool) as cursor:
        while True:
            committed = 0
            # https://aiokafka.readthedocs.io/en/stable/consumer.html#manual-vs-automatic-committing
            result = await kafka_consumer.getmany(
                timeout_ms=config.KAFKA_CONSUMER_WAIT_TIMEOUT, max_records=config.KAFKA_CONSUMER_MAX_RECORDS
            )
            for tp, messages in result.items():
                await cursor.execute("BEGIN")
                for msg in messages:
                    # assume we don't need to avoid duplicated records can be appeared in postgres
                    # for at least one delivery, however it can be avoided with upsert usage
                    event = await EventPgManager(cursor).create(
                        **{k: v for k, v in Event.deserialize(msg.value).__dict__.items() if k != "id"}
                    )
                    logger.info("transferred site availability for url: %s", event.url)
                await cursor.execute("COMMIT")
                await kafka_consumer.commit({tp: messages[-1].offset + 1})
                committed += 1
            if committed == 0:
                break
            count += committed
    logger.info("finished kafka to postgres transfer count: %s", count)


async def startup(
    ctx,
    http=False,
    postgres=False,
    redis=False,
    kafka_producer=False,
    kafka_consumer=False,
):
    if http:
        ctx["http_client"] = httpx.AsyncClient()
    if postgres:
        ctx["pg_pool"] = await postgres_pool_factory(config.POSTGRES_CONFIG)
        await ensure_db_configured(ctx["pg_pool"])
    if redis:
        ctx["redis_pool"] = await redis_pool_factory(config.REDIS_CONFIG)
    if kafka_producer:
        ctx["kafka_producer"] = await kafka_producer_factory(config.KAFKA_PRODUCER_CONFIG)
    if kafka_consumer:
        ctx["kafka_consumer"] = await kafka_consumer_factory(config.KAFKA_TOPIC, config.KAFKA_CONSUMER_CONFIG)


async def shutdown(ctx):
    if "http_client" in ctx:
        await ctx["http_client"].aclose()
    if "pg_pool" in ctx:
        ctx["pg_pool"].close()
    if "redis_pool" in ctx:
        ctx["redis_pool"].close()
    if "kafka_producer" in ctx:
        await ctx["kafka_producer"].stop()
    if "kafka_consumer" in ctx:
        await ctx["kafka_consumer"].stop()


class AvailabilityCheckerWorkerSettings:
    redis_settings = arq.connections.RedisSettings(**config.REDIS_CONFIG)
    queue_name = "arq:queue:availability_check"
    max_jobs = config.AVAILABILITY_CHECKER_MAX_JOBS
    retry_jobs = False  # assume we can ignore failed checks and reschedule it next time
    on_startup = partial(startup, http=True, redis=True, kafka_producer=True)
    on_shutdown = shutdown
    functions = [availability_check]


class CheckSchedulerWorkerSettings:
    redis_settings = arq.connections.RedisSettings(**config.REDIS_CONFIG)
    queue_name = "arq:queue:check_scheduler"
    on_startup = partial(startup, postgres=True, redis=True)
    on_shutdown = shutdown
    # assume we don't need to parallelize scheduling, can sacrifice redundancy and assume workers
    # handle checks faster than queue grows to keep current implementation more simple
    cron_jobs = [arq.cron(schedule_availability_checks, unique=True, minute={i for i in range(60)})]


class KafkaToPostgresTransferWorkerSettings:
    redis_settings = arq.connections.RedisSettings(**config.REDIS_CONFIG)
    queue_name = "arq:queue:kafka_to_postgres_transfer"
    on_startup = partial(startup, postgres=True, kafka_consumer=True)
    on_shutdown = shutdown
    # in general this job can be run in parallel, but it require more efforts to rewrite runner
    # so sorry if you see this ugly approach with cron unique job and infinite loop inside
    cron_jobs = [arq.cron(kafka_to_pg_transfer, unique=True, minute={i for i in range(60)})]
