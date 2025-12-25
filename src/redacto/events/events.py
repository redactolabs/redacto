from enum import Enum


class EventType(str, Enum):
    TEST_EVENT = "test.event"
    DOCUMENT_EXPIRED = "platform.document.expired"
    VRM_FORM_SUBMITTED = "vrm.form.submitted"
    VRM_VENDOR_TIER_UPDATED = "vrm.vendor.tier.updated"
    VRM_VENDOR_SCORE_UPDATED = "vrm.vendor.score.updated"
    VRM_ASSESSMENT_STATUS_UPDATED = "vrm.assessment.status.updated"
    VRM_COMMENT_UPSERTED = "vrm.form.comments.upserted"

    VRM_EXECUTE_POLICY = "vrm.policy.execute"
    VRM_EVALUATE_RULE = "vrm.rule.evaluate"

    def __str__(self):
        return self.value


ALL_EVENTS = set(EventType)
