import arq
import pytest

from service.jobs import (
    availability_check,
    schedule_availability_checks,
    kafka_to_pg_transfer,
    CheckSchedulerWorkerSettings,
    AvailabilityCheckerWorkerSettings,
    KafkaToPostgresTransferWorkerSettings,
)


@pytest.mark.asyncio
async def test_schedule__success(pg_cursor, site_check_pg_manager, event_pg_manager, arq_worker, httpx_mock):
    assert [e async for e in site_check_pg_manager.get_all()] == []
    assert [e async for e in event_pg_manager.get_all()] == []
    await site_check_pg_manager.create("http://test.com", "test")

    schedule_worker = arq_worker(
        cron_jobs=[arq.cron(schedule_availability_checks, hour=1, run_at_startup=True)],
        queue_name=CheckSchedulerWorkerSettings.queue_name,
    )
    await schedule_worker.main()
    assert schedule_worker.jobs_complete == 1
    assert schedule_worker.jobs_failed == 0
    assert schedule_worker.jobs_retried == 0

    httpx_mock.add_response(status_code=200, data=b"ok")
    check_worker = arq_worker(functions=[availability_check], queue_name=AvailabilityCheckerWorkerSettings.queue_name)
    await check_worker.main()
    assert check_worker.jobs_complete == 1
    assert check_worker.jobs_failed == 0
    assert check_worker.jobs_retried == 0

    transfer_worker = arq_worker(
        cron_jobs=[arq.cron(kafka_to_pg_transfer, hour=1, run_at_startup=True)],
        queue_name=KafkaToPostgresTransferWorkerSettings.queue_name,
    )
    await transfer_worker.main()
    assert transfer_worker.jobs_complete == 1
    assert transfer_worker.jobs_failed == 0
    assert transfer_worker.jobs_retried == 0

    events = [e async for e in event_pg_manager.get_all()]
    assert len(events) == 1
    assert events[0].url == "http://test.com"
    assert events[0].status_code == 200
