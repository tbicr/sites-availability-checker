import httpx
import pytest

from service.utils import fetch, regexp_check


@pytest.mark.asyncio
async def test_fetch__ok(httpx_mock):
    httpx_mock.add_response(status_code=200, data=b"ok")
    async with httpx.AsyncClient() as client:
        check_result, content = await fetch(client, "http://test.com")
    assert check_result.status_code == 200
    assert check_result.duration > 0
    assert content == b"ok"


@pytest.mark.asyncio
async def test_fetch__raise_timeout(httpx_mock):
    def raise_timeout(request, ext):
        raise httpx.ReadTimeout("timeout", request=request)

    httpx_mock.add_callback(raise_timeout)
    async with httpx.AsyncClient() as client:
        check_result, content = await fetch(client, "http://test.com")
    assert check_result.status_code is None
    assert check_result.duration > 0
    assert content is None


def test_regexp__pattern_found():
    assert regexp_check("a", b"aaa") is True


def test_regexp__pattern_not_found():
    assert regexp_check("b", b"aaa") is False


def test_regexp__invalid_pattern():
    assert regexp_check("(b", b"aaa") is False


def test_regexp__no_pattern():
    assert regexp_check(None, b"aaa") is None


def test_regexp__no_content():
    assert regexp_check("a", None) is None
