import json
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Optional


def datetime_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


def detetime_restore(data, key):
    try:
        data[key] = datetime.strptime(data[key], "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        data[key] = datetime.strptime(data[key], "%Y-%m-%dT%H:%M:%S")
    return data


@dataclass
class SiteCheck:
    id: Optional[int]  # None for not persisted entity
    url: str
    regexp: Optional[str] = None  # UTF8 encoded pattern, will check binary representation of it


@dataclass
class Event:
    id: Optional[int]  # None for not persisted entity
    created_at: datetime
    url: str  # assume we don't need to use ForeignKey to SiteCheck
    duration: float
    status_code: Optional[int] = None  # None for http error or timeout
    regexp_found: Optional[bool] = None  # None in case of empty regexp or no response

    def serialize(self):
        return json.dumps(self.__dict__, default=datetime_default).encode("utf8")

    @classmethod
    def deserialize(cls, data):
        return cls(**json.loads(data.decode("utf8"), object_hook=partial(detetime_restore, key="created_at")))
