from datetime import datetime

from service.entities import Event


def test_serializer():
    event = Event(id=None, created_at=datetime(2020, 12, 12), url="http://test.com", duration=1.1, status_code=200)
    serialized = event.serialize()
    restored_event = Event.deserialize(serialized)
    assert event == restored_event
