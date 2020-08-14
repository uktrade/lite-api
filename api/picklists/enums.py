class PicklistType:
    PROVISO = "proviso"
    ECJU = "ecju_query"
    LETTER_PARAGRAPH = "letter_paragraph"
    REPORT_SUMMARY = "report_summary"
    STANDARD_ADVICE = "standard_advice"
    FOOTNOTES = "footnotes"
    PRE_VISIT_QUESTIONNAIRE = "pre_visit_questionnaire"
    COMPLIANCE_ACTIONS = "compliance_actions"

    choices = [
        (PROVISO, "Proviso"),
        (ECJU, "Standard ECJU Query"),
        (LETTER_PARAGRAPH, "Letter Paragraph"),
        (REPORT_SUMMARY, "Report Summary"),
        (STANDARD_ADVICE, "Standard Advice"),
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
