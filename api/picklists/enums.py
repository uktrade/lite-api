class PicklistType:
    PROVISO = "proviso"
    ECJU = "ecju_query"
    LETTER_PARAGRAPH = "__"
    REPORT_SUMMARY = "report_summary"
    STANDARD_ADVICE = "standard_advice"
    REFUSAL_REASON = "refusal_reason"
    FOOTNOTES = "footnotes"
    PRE_VISIT_QUESTIONNAIRE = "pre_visit_questionnaire"
    COMPLIANCE_ACTIONS = "compliance_actions"

    choices = [
        (PROVISO, "Proviso"),
        (ECJU, "Standard ECJU Query"),
        (LETTER_PARAGRAPH, "Letter Paragraph"),
        (REPORT_SUMMARY, "Report Summary"),
        (STANDARD_ADVICE, "Standard Advice"),
        (REFUSAL_REASON, "Refusal reason"),
        (FOOTNOTES, "Footnotes"),
        (PRE_VISIT_QUESTIONNAIRE, "Pre-Visit Questionnaire questions (ECJU Query)"),
        (COMPLIANCE_ACTIONS, "Compliance Actions (ECJU Query)"),
    ]


class PickListStatus:
    ACTIVE = "active"
    DEACTIVATED = "deactivated"

    choices = [
        (ACTIVE, "Active"),
        (DEACTIVATED, "Deactivated"),
    ]
