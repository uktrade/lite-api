class BaseActivityType:
    choices = []

    @classmethod
    def get_text(cls, choice):
        return [x for x in cls.choices if x[0] == choice][0][1]


class CaseActivityType(BaseActivityType):
    ADD_FLAGS = 'add_flags'
    REMOVE_FLAGS = 'remove_flags'
    ADD_REMOVE_FLAGS = 'add_remove_flags'

    GOOD_REVIEWED = 'good_reviewed'
    GOOD_ADD_FLAGS = 'good_add_flags'
    GOOD_REMOVE_FLAGS = 'good_remove_flags'
    GOOD_ADD_REMOVE_FLAGS = 'good_add_remove_flags'

    ADD_GOOD_TO_APPLICATION = 'add_good_to_application'
    REMOVE_GOOD_FROM_APPLICATION = 'remove_good_from_application'
    ADD_GOOD_TYPE_TO_APPLICATION = 'add_good_type_to_application'
    REMOVE_GOOD_TYPE_FROM_APPLICATION = 'remove_good_type_from_application'

    DELETE_ALL_SITES_FROM_APPLICATION = 'delete_all_sites_from_application'
    ADD_EXTERNAL_LOCATIONS_TO_APPLICATION = 'add_external_locations_to_application'

    DELETE_ALL_COUNTRIES_FROM_APPLICATION = 'delete_all_countries_from_application'
    ADD_COUNTRIES_TO_APPLICATION = 'add_countries_to_application'

    MOVE_CASE = 'move_case'
    REMOVE_CASE = 'remove_case'

    CLC_RESPONSE = 'clc_response'
    CASE_NOTE = 'case_note'

    ECJU_QUERY = 'ecju_query'

    UPDATED_STATUS = 'update_status'
    UPDATED_APPLICATION_NAME = 'update_application_name'
    UPDATED_APPLICATION_REFERENCE_NUMBER = 'update_application_reference_number'

    CREATED_FINAL_ADVICE = 'created_final_advice'
    CLEARED_FINAL_ADVICE = 'cleared_final_advice'
    CREATED_TEAM_ADVICE = 'created_team_advice'
    CLEARED_TEAM_ADVICE = 'cleared_team_advice'

    BaseActivityType.choices.extend(
        [
            (ADD_FLAGS, 'added flags: {added_flags}'),
            (REMOVE_FLAGS, 'removed flags: {removed_flags}'),
            (ADD_REMOVE_FLAGS, 'added flags: {added_flags}, and removed: {removed_flags}'),

            (GOOD_REVIEWED, 'good was reviewed: {good_name} control code was changed to \'{control_code}\''),
            (GOOD_ADD_FLAGS, 'added flags: {added_flags} to good: {good_name}'),
            (GOOD_REMOVE_FLAGS, 'removed flags: {removed_flags} to good: {good_name}'),
            (GOOD_ADD_REMOVE_FLAGS, 'added flags: {added_flags}, and removed: {removed_flags} to good: {good_name}'),

            (ADD_GOOD_TO_APPLICATION, 'added good {good_name} to the application'),
            (REMOVE_GOOD_FROM_APPLICATION, 'removed good {good_name} from the application'),
            (ADD_GOOD_TYPE_TO_APPLICATION, 'added good type {good_type_name} to the application'),
            (REMOVE_GOOD_TYPE_FROM_APPLICATION, 'removed good {good_type_name} from the application'),

            (DELETE_ALL_SITES_FROM_APPLICATION, 'removed all sites from the application'),
            (ADD_EXTERNAL_LOCATIONS_TO_APPLICATION, 'added external locations: {locations}'),

            (DELETE_ALL_COUNTRIES_FROM_APPLICATION, 'removed all countries from the application'),
            (ADD_COUNTRIES_TO_APPLICATION, 'added countries: {countries}'),

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

            (UPDATED_APPLICATION_NAME, 'updated the application name from "{old_name}" to "{new_name}"'),
            (UPDATED_APPLICATION_REFERENCE_NUMBER, 'updated the application reference number from '
                                                   '{old_ref_number} to {new_ref_number}'),
        ]
    )
