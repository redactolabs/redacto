from redacto.events.events import ALL_EVENTS, EventType


class TestEventType:
    def test_values(self):
        assert EventType.TEST_EVENT == "test.event"
        assert EventType.DOCUMENT_EXPIRED == "platform.document.expired"
        assert EventType.VRM_FORM_SUBMITTED == "vrm.form.submitted"

    def test_str(self):
        assert str(EventType.TEST_EVENT) == "test.event"

    def test_all_events_contains_all_types(self):
        for event_type in EventType:
            assert event_type in ALL_EVENTS

    def test_all_events_length(self):
        assert len(ALL_EVENTS) == len(EventType)
