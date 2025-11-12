from enum import Enum


class EventType(str, Enum):
    TEST_EVENT = "test.event"
    DOCUMENT_EXPIRED = "platform.document.expired"
    VRM_FORM_SUBMITTED = "vrm.form.submitted"

    def __str__(self):
        return self.value


ALL_EVENTS = set(EventType)
