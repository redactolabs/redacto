from enum import Enum


class EventType(str, Enum):
    TEST_EVENT = "test.event"
    DOCUMENT_EXPIRED = "platform.document.expired"
    VRM_FORM_SUBMITTED = "vrm.form.submitted"
    VRM_VENDOR_TIER_CHANGED = "vrm.vendor__tier.changed"
    VRM_VENDOR_SCORE_CHANGED = "vrm.vendor__score.changed"
    VRM_ASSESSMENT_STATUS_CHANGED = "vrm.assessment__status.changed"
    VRM_COMMENT_UPSERTED = "vrm.comments.upserted"

    def __str__(self):
        return self.value


ALL_EVENTS = set(EventType)
