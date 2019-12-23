from enum import Enum


class AuditType(Enum):
    ADD_FLAGS = "added flags: {added_flags}"
    REMOVE_FLAGS = "removed flags: {removed_flags}"
    GOOD_REVIEWED = (
        'good was reviewed: {good_name} control code changed from "{old_control_code}" to "{new_control_code}"'
    )
    GOOD_ADD_FLAGS = "added flags: {added_flags} to good: {good_name}"
    GOOD_REMOVE_FLAGS = "removed flags: {removed_flags} from good: {good_name}"
    GOOD_ADD_REMOVE_FLAGS = "added flags: {added_flags}, and removed: {removed_flags} from good: {good_name}"
    ADD_GOOD_TO_APPLICATION = "added good: {good_name}"
    REMOVE_GOOD_FROM_APPLICATION = "removed good: {good_name}"
    ADD_GOOD_TYPE_TO_APPLICATION = "added good type: {good_type_name}"
    REMOVE_GOOD_TYPE_FROM_APPLICATION = "removed good type: {good_type_name}"
    REMOVED_SITES_FROM_APPLICATION = "removed sites: {sites}"
    ADD_SITES_TO_APPLICATION = "added sites: {sites}"
    REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION = "removed external locations: {locations}"
    ADD_EXTERNAL_LOCATIONS_TO_APPLICATION = "added external locations: {locations}"
    REMOVED_COUNTRIES_FROM_APPLICATION = "removed countries: {countries}"
    ADD_COUNTRIES_TO_APPLICATION = "added countries: {countries}"
    MOVE_CASE = "moved the case to: {queues}"
    REMOVE_CASE = "removed case from queues: {queues}"
    CLC_RESPONSE = "responded to the case"
    CREATED_CASE_NOTE = "added a case note: {case_note}"
    ECJU_QUERY = " added an ECJU Query: {ecju_query}"
    UPDATED_STATUS = "updated the status to: {status}"
    UPDATED_APPLICATION_NAME = 'updated the application name from "{old_name}" to "{new_name}"'
    UPDATED_APPLICATION_REFERENCE_NUMBER = (
        "updated the application reference number from " "{old_ref_number} to {new_ref_number}"
    )
    ASSIGNED_GOOD_TO_COUNTRY = "updated the good '{good_type_name}' destinations to {countries}"
    CREATED_FINAL_ADVICE = "created final advice"
    CLEARED_FINAL_ADVICE = "cleared final advice"
    CREATED_TEAM_ADVICE = "created team advice"
    CLEARED_TEAM_ADVICE = "cleared team advice"
    ADD_PARTY = "added the {party_type} {party_name}"
    REMOVE_PARTY = "removed the {party_type} {party_name}"
    UPLOAD_PARTY_DOCUMENT = "uploaded the document {file_name} for {party_type} {party_name}"
    DELETE_PARTY_DOCUMENT = "deleted the document {file_name} for {party_type} {party_name}"
    UPLOAD_APPLICATION_DOCUMENT = "uploaded the application document {file_name}"
    DELETE_APPLICATION_DOCUMENT = "deleted the application document {file_name}"
    UPLOAD_CASE_DOCUMENT = "uploaded the case document {file_name}"
    GENERATE_CASE_DOCUMENT = "generated the case document {file_name} from template {template}"

    UPDATED_LETTER_TEMPLATE_NAME = "updated letter template name from {old_name} to {new_name}"
    UPDATED_LETTER_TEMPLATE_CASE_TYPES = "updated letter template types from {old_case_types} to {new_case_types}"
    UPDATED_LETTER_TEMPLATE_PARAGRAPHS = "updated letter paragraphs from {old_paragraphs} to {new_paragraphs}"
    UPDATED_LETTER_TEMPLATE_LAYOUT = "updated letter layout from {old_layout} to {new_layout}"
    UPDATED_LETTER_TEMPLATE_PARAGRAPHS_ORDERING = "updated letter paragraphs ordering"

    def format(self, payload):
        text = self.value.format(**payload)
        if text[-1] not in [":", ".", "?"]:
            return f"{text}."

        return text
