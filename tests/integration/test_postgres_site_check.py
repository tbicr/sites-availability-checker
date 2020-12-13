import pytest


@pytest.mark.asyncio
async def test_operations__success(pg_cursor, site_check_pg_manager):
    site_check = await site_check_pg_manager.create("http://test.com", "test")
    site_check_id = site_check.id
    assert site_check.id > 0
    assert site_check.url == "http://test.com"
    assert site_check.regexp == "test"

    site_check = await site_check_pg_manager.get_by_id(0)
    assert site_check is None

    site_check = await site_check_pg_manager.get_by_id(site_check_id)
    assert site_check.id == site_check_id
    assert site_check.url == "http://test.com"
    assert site_check.regexp == "test"

    async for site_check in site_check_pg_manager.get_all():
        assert site_check.id == site_check_id
        assert site_check.url == "http://test.com"
        assert site_check.regexp == "test"

    await site_check_pg_manager.delete_all()
    assert [e async for e in site_check_pg_manager.get_all()] == []
