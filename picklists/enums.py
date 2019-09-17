class PicklistType:
    PROVISO = 'proviso'
    ECJU = 'ecju_query'
    LETTER_PARAGRAPH = 'letter_paragraph'
    REPORT_SUMMARY = 'report_summary'
    STANDARD_ADVICE = 'standard_advice'
    FOOTNOTES = 'footnotes'

    choices = [
        (PROVISO, 'Proviso'),
        (ECJU, 'ECJU Query'),
        (LETTER_PARAGRAPH, 'Letter Paragraph'),
        (REPORT_SUMMARY, 'Report Summary'),
        (STANDARD_ADVICE, 'Standard Advice'),
        (FOOTNOTES, 'Footnotes'),
    ]


class PickListStatus:
    ACTIVE = 'active'
    DEACTIVATED = 'deactivated'

    choices = [
        (ACTIVE, 'Active'),
        (DEACTIVATED, 'Deactivated'),
    ]
