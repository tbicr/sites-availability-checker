from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_operations__success(pg_cursor, event_pg_manager):
    event = await event_pg_manager.create(datetime(2020, 12, 20), "http://test.com", 1.1, 200, None)
    event_id = event.id
    assert event.id > 0
    assert event.created_at == datetime(2020, 12, 20)
    assert event.url == "http://test.com"
    assert event.duration == 1.1
    assert event.status_code == 200
    assert event.regexp_found is None

    site_check = await event_pg_manager.get_by_id(0)
    assert site_check is None

    event = await event_pg_manager.get_by_id(event_id)
    assert event.id == event_id
    assert event.created_at == datetime(2020, 12, 20)
    assert event.url == "http://test.com"
    assert event.duration == 1.1
    assert event.status_code == 200
    assert event.regexp_found is None

    async for event in event_pg_manager.get_all():
        assert event.id == event_id
        assert event.created_at == datetime(2020, 12, 20)
        assert event.url == "http://test.com"
        assert event.duration == 1.1
        assert event.status_code == 200
        assert event.regexp_found is None

    await event_pg_manager.delete_all()
    assert [e async for e in event_pg_manager.get_all()] == []
