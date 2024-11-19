from uuid import UUID


class CaseStatusEnum:
    APPEAL_FINAL_REVIEW = "appeal_final_review"
    APPEAL_REVIEW = "appeal_review"
    APPLICANT_EDITING = "applicant_editing"
    CHANGE_INTIAL_REVIEW = "change_initial_review"
    CHANGE_UNDER_FINAL_REVIEW = "change_under_final_review"
    CHANGE_UNDER_REVIEW = "change_under_review"
    CLC = "clc_review"
    OPEN = "open"
    UNDER_INTERNAL_REVIEW = "under_internal_review"
    RETURN_TO_INSPECTOR = "return_to_inspector"
    AWAITING_EXPORTER_RESPONSE = "awaiting_exporter_response"
    CLOSED = "closed"
    DEREGISTERED = "deregistered"
    DRAFT = "draft"  # System only status
    FINALISED = "finalised"
    INITIAL_CHECKS = "initial_checks"
    PV = "pv_review"
    REGISTERED = "registered"
    REOPENED_FOR_CHANGES = "reopened_for_changes"
    REOPENED_DUE_TO_ORG_CHANGES = "reopened_due_to_org_changes"
    RESUBMITTED = "resubmitted"
    REVOKED = "revoked"
    OGD_ADVICE = "ogd_advice"
    SUBMITTED = "submitted"
    SURRENDERED = "surrendered"
    SUSPENDED = "suspended"
    UNDER_APPEAL = "under_appeal"
    UNDER_ECJU_REVIEW = "under_ECJU_review"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"
    OGD_CONSOLIDATION = "ogd_consolidation"
    FINAL_REVIEW_COUNTERSIGN = "final_review_countersign"
    FINAL_REVIEW_SECOND_COUNTERSIGN = "final_review_second_countersign"
    SUPERSEDED_BY_EXPORTER_EDIT = "superseded_by_exporter_edit"

    _system_status = [DRAFT]

    _writeable_statuses = [
        DRAFT,
        APPLICANT_EDITING,
    ]

    _can_invoke_major_edit_statuses = [SUBMITTED, INITIAL_CHECKS, UNDER_REVIEW, REOPENED_FOR_CHANGES]

    _major_editable_statuses = [APPLICANT_EDITING, DRAFT]

    _terminal_statuses = [
        CLOSED,
        DEREGISTERED,
        FINALISED,
        REGISTERED,
        REVOKED,
        SURRENDERED,
        WITHDRAWN,
        SUPERSEDED_BY_EXPORTER_EDIT,
    ]

    _closed_statuses = [
        CLOSED,
        DEREGISTERED,
        FINALISED,
        REGISTERED,
        REVOKED,
        SURRENDERED,
        WITHDRAWN,
    ]

    # Cases with these statuses can be operated upon by caseworkers
    _caseworker_operable_statuses = [
        APPEAL_FINAL_REVIEW,
        APPEAL_REVIEW,
        APPLICANT_EDITING,
        CHANGE_INTIAL_REVIEW,
        CHANGE_UNDER_FINAL_REVIEW,
        CHANGE_UNDER_REVIEW,
        CLC,
        OPEN,
        UNDER_INTERNAL_REVIEW,
        RETURN_TO_INSPECTOR,
        AWAITING_EXPORTER_RESPONSE,
        CLOSED,
        DEREGISTERED,
        FINALISED,
        INITIAL_CHECKS,
        PV,
        REGISTERED,
        REOPENED_FOR_CHANGES,
        REOPENED_DUE_TO_ORG_CHANGES,
        RESUBMITTED,
        REVOKED,
        OGD_ADVICE,
        SUBMITTED,
        SURRENDERED,
        SUSPENDED,
        UNDER_APPEAL,
        UNDER_ECJU_REVIEW,
        UNDER_FINAL_REVIEW,
        UNDER_REVIEW,
        WITHDRAWN,
        OGD_CONSOLIDATION,
        FINAL_REVIEW_COUNTERSIGN,
        FINAL_REVIEW_SECOND_COUNTERSIGN,
    ]

    goods_query_statuses = [CLC, PV]

    clc_statuses = [SUBMITTED, CLOSED, WITHDRAWN]

    compliance_site_statuses = [OPEN, CLOSED]

    compliance_visit_statuses = [OPEN, UNDER_INTERNAL_REVIEW, RETURN_TO_INSPECTOR, AWAITING_EXPORTER_RESPONSE, CLOSED]

    non_precedent_statuses = [
        SUBMITTED,
        INITIAL_CHECKS,
    ]

    precedent_statuses = [
        UNDER_REVIEW,
        OGD_ADVICE,
        OGD_CONSOLIDATION,
        UNDER_FINAL_REVIEW,
        FINAL_REVIEW_COUNTERSIGN,
        FINAL_REVIEW_SECOND_COUNTERSIGN,
        FINALISED,
        SUPERSEDED_BY_EXPORTER_EDIT,
    ]

    choices = [
        (APPEAL_FINAL_REVIEW, "Appeal final review"),
        (APPEAL_REVIEW, "Appeal review"),
        (APPLICANT_EDITING, "Applicant editing"),
        (CHANGE_INTIAL_REVIEW, "Change initial review"),
        (CHANGE_UNDER_FINAL_REVIEW, "Change under final review"),
        (CHANGE_UNDER_REVIEW, "Change under review"),
        (CLC, "CLC review"),
        (OPEN, "Open"),
        (UNDER_INTERNAL_REVIEW, "Under internal review"),
        (RETURN_TO_INSPECTOR, "Return to inspector"),
        (AWAITING_EXPORTER_RESPONSE, "Awaiting exporter response"),
        (CLOSED, "Closed"),
        (DEREGISTERED, "De-registered"),
        (FINALISED, "Finalised"),
        (INITIAL_CHECKS, "Initial checks"),
        (PV, "PV grading review"),
        (REGISTERED, "Registered"),
        (REOPENED_FOR_CHANGES, "Re-opened for changes"),
        (REOPENED_DUE_TO_ORG_CHANGES, "Re-opened due to org changes"),
        (RESUBMITTED, "Resubmitted"),
        (REVOKED, "Revoked"),
        (SUBMITTED, "Submitted"),
        (SURRENDERED, "Surrendered"),
        (SUSPENDED, "Suspended"),
        (UNDER_APPEAL, "Under appeal"),
        (UNDER_ECJU_REVIEW, "Under ECJU appeal"),
        (UNDER_FINAL_REVIEW, "Under final review"),
        (UNDER_REVIEW, "Under review"),
        (WITHDRAWN, "Withdrawn"),
        (OGD_ADVICE, "OGD Advice"),
        (OGD_CONSOLIDATION, "OGD Consolidation"),
        (SUPERSEDED_BY_EXPORTER_EDIT, "Superseded by exporter edit"),
        (FINAL_REVIEW_COUNTERSIGN, "Final review countersign"),
        (FINAL_REVIEW_SECOND_COUNTERSIGN, "Final review second countersign"),
    ]

    priority = {
        SUBMITTED: 1,
        APPLICANT_EDITING: 2,
        RESUBMITTED: 3,
        INITIAL_CHECKS: 4,
        UNDER_REVIEW: 5,
        OGD_ADVICE: 6,
        OGD_CONSOLIDATION: 7,
        UNDER_FINAL_REVIEW: 8,
        FINAL_REVIEW_COUNTERSIGN: 9,
        FINAL_REVIEW_SECOND_COUNTERSIGN: 10,
        FINALISED: 11,
        CLC: 12,
        PV: 13,
        OPEN: 14,
        UNDER_INTERNAL_REVIEW: 15,
        RETURN_TO_INSPECTOR: 16,
        AWAITING_EXPORTER_RESPONSE: 17,
        WITHDRAWN: 18,
        CLOSED: 19,
        REGISTERED: 20,
        UNDER_APPEAL: 21,
        APPEAL_REVIEW: 22,
        APPEAL_FINAL_REVIEW: 23,
        REOPENED_FOR_CHANGES: 24,
        REOPENED_DUE_TO_ORG_CHANGES: 25,
        CHANGE_INTIAL_REVIEW: 26,
        CHANGE_UNDER_REVIEW: 27,
        CHANGE_UNDER_FINAL_REVIEW: 28,
        UNDER_ECJU_REVIEW: 29,
        REVOKED: 30,
        SUSPENDED: 31,
        SURRENDERED: 32,
        DEREGISTERED: 33,
        SUPERSEDED_BY_EXPORTER_EDIT: 34,
    }

    @classmethod
    def get_choices(cls):
        return cls.choices

    @classmethod
    def get_text(cls, status):
        # All available statuses and DRAFT (System only status)
        for k, v in [*cls.get_choices(), (cls.DRAFT, "Draft")]:
            if status == k:
                return v

    @classmethod
    def get_value(cls, status):
        # All available statuses and DRAFT (System only status)
        for k, v in [*cls.get_choices(), (cls.DRAFT, "Draft")]:
            if status == v:
                return k

    @classmethod
    def is_read_only(cls, status):
        return status in cls.read_only_statuses()

    @classmethod
    def is_editable(cls, status):
        return not cls.is_read_only(status)

    @classmethod
    def is_terminal(cls, status):
        return status in cls._terminal_statuses

    @classmethod
    def is_closed(cls, status):
        return status in cls._closed_statuses

    @classmethod
    def is_system_status(cls, status):
        return status in cls._system_status

    @classmethod
    def is_caseworker_operable(cls, status):
        return status in cls._caseworker_operable_statuses

    @classmethod
    def read_only_statuses(cls):
        return list(set(cls.all()) - set(cls._writeable_statuses))

    @classmethod
    def major_editable_statuses(cls):
        return cls._major_editable_statuses

    @classmethod
    def caseworker_operable_statuses(cls):
        return cls._caseworker_operable_statuses

    @classmethod
    def caseworker_inoperable_statuses(cls):
        return list(set(CaseStatusEnum.all()) - set(cls._caseworker_operable_statuses))

    @classmethod
    def is_major_editable_status(cls, status):
        return status in cls._major_editable_statuses

    @classmethod
    def can_invoke_major_edit_statuses(cls):
        return cls._can_invoke_major_edit_statuses

    @classmethod
    def can_not_invoke_major_edit_statuses(cls):
        return list(set(cls.all()) - set(cls._can_invoke_major_edit_statuses))

    @classmethod
    def can_invoke_major_edit(cls, status):
        return status in cls._can_invoke_major_edit_statuses

    @classmethod
    def terminal_statuses(cls):
        return cls._terminal_statuses

    @classmethod
    def as_list(cls):
        from api.staticdata.statuses.models import CaseStatus
        from api.staticdata.statuses.serializers import CaseStatusSerializer

        # Exclude the 'Draft' system status
        statuses = CaseStatus.objects.all().order_by("priority").exclude(status="draft")
        return CaseStatusSerializer(statuses, many=True).data

    @classmethod
    def all(cls):
        return [getattr(cls, param) for param in dir(cls) if param.isupper()]


class CaseStatusIdEnum:
    APPEAL_FINAL_REVIEW = UUID("00000000-0000-0000-0000-000000000013")
    APPEAL_REVIEW = UUID("00000000-0000-0000-0000-000000000012")
    APPLICANT_EDITING = UUID("00000000-0000-0000-0000-000000000002")
    CHANGE_INTIAL_REVIEW = UUID("00000000-0000-0000-0000-000000000015")
    CHANGE_UNDER_FINAL_REVIEW = UUID("00000000-0000-0000-0000-000000000017")
    CHANGE_UNDER_REVIEW = UUID("00000000-0000-0000-0000-000000000016")
    CLC = UUID("00000000-0000-0000-0000-000000000023")
    OPEN = UUID("00000000-0000-0000-0000-000000000027")
    UNDER_INTERNAL_REVIEW = UUID("00000000-0000-0000-0000-000000000028")
    RETURN_TO_INSPECTOR = UUID("00000000-0000-0000-0000-000000000029")
    AWAITING_EXPORTER_RESPONSE = UUID("00000000-0000-0000-0000-000000000030")
    CLOSED = UUID("00000000-0000-0000-0000-000000000009")
    DEREGISTERED = UUID("00000000-0000-0000-0000-000000000022")
    DRAFT = UUID("00000000-0000-0000-0000-000000000000")
    FINALISED = UUID("00000000-0000-0000-0000-000000000007")
    INITIAL_CHECKS = UUID("00000000-0000-0000-0000-000000000004")
    PV = UUID("00000000-0000-0000-0000-000000000024")
    REGISTERED = UUID("00000000-0000-0000-0000-000000000010")
    REOPENED_FOR_CHANGES = UUID("00000000-0000-0000-0000-000000000014")
    REOPENED_DUE_TO_ORG_CHANGES = UUID("00000000-0000-0000-0000-000000000025")
    RESUBMITTED = UUID("00000000-0000-0000-0000-000000000003")
    REVOKED = UUID("00000000-0000-0000-0000-000000000019")
    OGD_ADVICE = UUID("00000000-0000-0000-0000-000000000026")
    SUBMITTED = UUID("00000000-0000-0000-0000-000000000001")
    SURRENDERED = UUID("00000000-0000-0000-0000-000000000021")
    SUSPENDED = UUID("00000000-0000-0000-0000-000000000020")
    UNDER_APPEAL = UUID("00000000-0000-0000-0000-000000000011")
    UNDER_ECJU_REVIEW = UUID("00000000-0000-0000-0000-000000000018")
    UNDER_FINAL_REVIEW = UUID("00000000-0000-0000-0000-000000000006")
    UNDER_REVIEW = UUID("00000000-0000-0000-0000-000000000005")
    WITHDRAWN = UUID("00000000-0000-0000-0000-000000000008")
    OGD_CONSOLIDATION = UUID("00000000-0000-0000-0000-000000000031")
    FINAL_REVIEW_COUNTERSIGN = UUID("00000000-0000-0000-0000-000000000032")
    FINAL_REVIEW_SECOND_COUNTERSIGN = UUID("00000000-0000-0000-0000-000000000033")
    SUPERSEDED_BY_EXPORTER_EDIT = UUID("00000000-0000-0000-0000-000000000034")


class CaseSubStatusIdEnum:
    UNDER_FINAL_REVIEW__INFORM_LETTER_SENT = "00000000-0000-0000-0000-000000000001"
    FINALISED__REFUSED = "00000000-0000-0000-0000-000000000002"
    FINALISED__APPROVED = "00000000-0000-0000-0000-000000000003"
    FINALISED__APPEAL_REJECTED = "00000000-0000-0000-0000-000000000004"
    FINALISED__APPEAL_REFUSED = "00000000-0000-0000-0000-000000000005"
    FINALISED__APPEAL_APPROVED = "00000000-0000-0000-0000-000000000006"
    UNDER_APPEAL__APPEAL_RECEIVED = "00000000-0000-0000-0000-000000000007"
    UNDER_APPEAL__SENIOR_MANAGER_INSTRUCTIONS = "00000000-0000-0000-0000-000000000008"
    UNDER_APPEAL__PRE_CIRCULATION = "00000000-0000-0000-0000-000000000009"
    UNDER_APPEAL__OGD_ADVICE = "00000000-0000-0000-0000-000000000010"
    UNDER_APPEAL__FINAL_DECISION = "00000000-0000-0000-0000-000000000011"
    UNDER_APPEAL__DRAFT_REJECTION_LETTER = "00000000-0000-0000-0000-000000000012"
