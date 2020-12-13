import re
import time
from datetime import datetime
from typing import Tuple, Optional

import httpx

from service import config
from service.entities import Event


async def fetch(client: httpx.AsyncClient, url: str) -> Tuple[Event, Optional[bytes]]:
    # assume that availability check doesn't require other to GET method and extra headers
    start = time.time()
    try:
        # assume we don't need to handle case when response body too big
        # by the way it can be handled by timeout indirectly
        # in bad case no response size limit can be issue of huge memory and networking usage
        # attacks for user content
        response = await client.get(url, timeout=config.FETCH_TIMEOUT)
        return (
            Event(
                id=None,
                created_at=datetime.fromtimestamp(start),
                url=url,
                duration=time.time() - start,
                status_code=response.status_code,
            ),
            response.content,
        )

    except httpx.HTTPError as err:
        return (
            Event(id=None, created_at=start, url=url, duration=time.time() - start),
            None,
        )


def regexp_check(regexp: str, content: bytes) -> Optional[bool]:
    # assume that there are no valid user inputted regexp that do heavy computations
    if content is None or regexp is None:
        return None

    try:
        return re.search(regexp.encode("utf8"), content) is not None
    except re.error:
        return False
