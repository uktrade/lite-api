class PicklistType:
    PROVISO = 'proviso'
    ECJU = 'ecju_query'
    LETTER_PARAGRAPH = 'letter_paragraph'
    ANNUAL_REPORT_SUMMARY = 'annual_report_summary'
    STANDARD_ADVICE = 'standard_advice'
    FOOTNOTES = 'footnotes'

    choices = [
        (PROVISO, 'Proviso'),
        (ECJU, 'ECJU Query'),
        (LETTER_PARAGRAPH, 'Letter Paragraph'),
        (ANNUAL_REPORT_SUMMARY, 'Annual Report Summary'),
        (STANDARD_ADVICE, 'Standard Advice'),
        (FOOTNOTES, 'Footnotes'),
    ]


class PickListStatus:
    ACTIVATE = 'active'
    DEACTIVATE = 'deactivated'

    choices = [
        (ACTIVATE, 'Active'),
        (DEACTIVATE, 'Deactivated'),
    ]
