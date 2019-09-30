class BaseActivityType:
    choices = []

    @classmethod
    def get_text(cls, choice):
        return [x for x in cls.choices if x[0] == choice][0][1]


class CaseActivityType(BaseActivityType):
    ADD_FLAGS = 'add_flags'
    REMOVE_FLAGS = 'remove_flags'
    ADD_REMOVE_FLAGS = 'add_remove_flags'

    GOOD_ADD_FLAGS = 'good_add_flags'
    GOOD_REMOVE_FLAGS = 'good_remove_flags'
    GOOD_ADD_REMOVE_FLAGS = 'good_add_remove_flags'

    MOVE_CASE = 'move_case'
    REMOVE_CASE = 'remove_case'

    CLC_RESPONSE = 'clc_response'
    CASE_NOTE = 'case_note'

    ECJU_QUERY = 'ecju_query'

    UPDATED_STATUS = 'update_status'

    CREATED_FINAL_ADVICE = 'created_final_advice'
    CLEARED_FINAL_ADVICE = 'cleared_final_advice'
    CREATED_TEAM_ADVICE = 'created_team_advice'
    CLEARED_TEAM_ADVICE = 'cleared_team_advice'

    BaseActivityType.choices.extend(
        [
            (ADD_FLAGS, 'added flags: {added_flags}'),
            (REMOVE_FLAGS, 'removed flags: {removed_flags}'),
            (ADD_REMOVE_FLAGS, 'added flags: {added_flags}, and removed: {removed_flags}'),

            (GOOD_ADD_FLAGS, 'added flags: {added_flags} to good: {good_name}'),
            (GOOD_REMOVE_FLAGS, 'removed flags: {removed_flags} to good: {good_name}'),
            (GOOD_ADD_REMOVE_FLAGS, 'added flags: {added_flags}, and removed: {removed_flags} to good: {good_name}'),

            (MOVE_CASE, 'moved the case to: {queues}'),
            (REMOVE_CASE, 'removed case from queues: {queues}'),

            (CLC_RESPONSE, 'responded to the case'),
            (CASE_NOTE, 'added a case note:'),

            (ECJU_QUERY, ' added an ECJU Query: {ecju_query}'),

            (UPDATED_STATUS, 'updated the status to {status}'),

            (CREATED_FINAL_ADVICE, 'created final advice'),
            (CLEARED_FINAL_ADVICE, 'cleared final advice'),
            (CREATED_TEAM_ADVICE, 'created team advice'),
            (CLEARED_TEAM_ADVICE, 'cleared team advice'),

        ]
    )
