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
    DESTINATION_ADD_FLAGS = "added flags: {added_flags} to destination: {destination_name}"
    DESTINATION_REMOVE_FLAGS = "removed flags: {removed_flags} from destination: {destination_name}"
    ADD_GOOD_TO_APPLICATION = "added good: {good_name}"
    REMOVE_GOOD_FROM_APPLICATION = "removed good: {good_name}"
    ADD_GOOD_TYPE_TO_APPLICATION = "added good type: {good_type_name}"
    REMOVE_GOOD_TYPE_FROM_APPLICATION = "removed good type: {good_type_name}"
    UPDATE_APPLICATION_END_USE_DETAIL = 'updated {end_use_detail} from "{old_end_use_detail}" to "{new_end_use_detail}"'
    UPDATE_APPLICATION_TEMPORARY_EXPORT = (
        'updated {temp_export_detail} from "{old_temp_export_detail}" to "{new_temp_export_detail}"'
    )
    REMOVED_SITES_FROM_APPLICATION = "removed sites: {sites}"
    ADD_SITES_TO_APPLICATION = "added sites: {sites}"
    REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION = "removed external locations: {locations}"
    ADD_EXTERNAL_LOCATIONS_TO_APPLICATION = "added external locations: {locations}"
    REMOVED_COUNTRIES_FROM_APPLICATION = "removed countries: {countries}"
    ADD_COUNTRIES_TO_APPLICATION = "added countries: {countries}"
    ADD_ADDITIONAL_CONTACT_TO_CASE = "added an additional contact: {contact}"
    MOVE_CASE = "moved the case to: {queues}"
    REMOVE_CASE = "removed case from queues: {queues}"
    CLC_RESPONSE = "responded to the case"
    PV_GRADING_RESPONSE = "responded to pv grading, grading set as {grading}"
    CREATED_CASE_NOTE = "added a case note: {case_note}"
    ECJU_QUERY = " added an ECJU Query: {ecju_query}"
    UPDATED_STATUS = "updated the status to: {status}"
    UPDATED_APPLICATION_NAME = 'updated the application name from "{old_name}" to "{new_name}"'
    UPDATE_APPLICATION_LETTER_REFERENCE = 'updated the letter reference from "{old_ref_number}" to "{new_ref_number}"'
    UPDATE_APPLICATION_F680_CLEARANCE_TYPES = 'updated the clearance types from "{old_types}" to "{new_types}"'
    ADDED_APPLICATION_LETTER_REFERENCE = "added the letter reference: {new_ref_number}"
    REMOVED_APPLICATION_LETTER_REFERENCE = "removed the letter reference: {old_ref_number}"
    ASSIGNED_COUNTRIES_TO_GOOD = "added the destinations {countries} to '{good_type_name}'"
    REMOVED_COUNTRIES_FROM_GOOD = "removed the destinations {countries} from '{good_type_name}'"
    CREATED_FINAL_ADVICE = "created final advice"
    CLEARED_FINAL_ADVICE = "cleared final advice"
    CREATED_TEAM_ADVICE = "created team advice"
    CLEARED_TEAM_ADVICE = "cleared team advice"
    CREATED_USER_ADVICE = "created user advice"
    ADD_PARTY = "added the {party_type} {party_name}"
    REMOVE_PARTY = "removed the {party_type} {party_name}"
    UPLOAD_PARTY_DOCUMENT = "uploaded the document {file_name} for {party_type} {party_name}"
    DELETE_PARTY_DOCUMENT = "deleted the document {file_name} for {party_type} {party_name}"
    UPLOAD_APPLICATION_DOCUMENT = "uploaded the application document {file_name}"
    DELETE_APPLICATION_DOCUMENT = "deleted the application document {file_name}"
    UPLOAD_CASE_DOCUMENT = "uploaded the case document {file_name}"
    GENERATE_CASE_DOCUMENT = "generated the case document {file_name} from template {template}"
    ADD_CASE_OFFICER_TO_CASE = "set {case_officer} as the Case Officer"
    REMOVE_CASE_OFFICER_FROM_CASE = "removed {case_officer} as the Case Officer"
    GRANTED_APPLICATION = "granted licence for {licence_duration} months starting from {start_date}"
    FINALISED_APPLICATION = "finalised the application"
    UNASSIGNED_QUEUES = "marked themselves as done for this case on the following queues: {queues}"
    UNASSIGNED = "marked themselves as done for this case"

    UPDATED_LETTER_TEMPLATE_NAME = "updated letter template name from {old_name} to {new_name}"
    ADDED_LETTER_TEMPLATE_CASE_TYPES = "added letter template types: {new_case_types}"
    UPDATED_LETTER_TEMPLATE_CASE_TYPES = "updated letter template types from {old_case_types} to {new_case_types}"
    REMOVED_LETTER_TEMPLATE_CASE_TYPES = "removed letter template types: {old_case_types}"
    ADDED_LETTER_TEMPLATE_DECISIONS = "added decisions: {new_decisions}"
    UPDATED_LETTER_TEMPLATE_DECISIONS = "updated decisions from {old_decisions} to {new_decisions}"
    REMOVED_LETTER_TEMPLATE_DECISIONS = "removed decisions: {old_decisions}"
    UPDATED_LETTER_TEMPLATE_PARAGRAPHS = "updated letter paragraphs from {old_paragraphs} to {new_paragraphs}"
    UPDATED_LETTER_TEMPLATE_LAYOUT = "updated letter layout from {old_layout} to {new_layout}"
    UPDATED_LETTER_TEMPLATE_PARAGRAPHS_ORDERING = "updated letter paragraphs ordering"

    CREATED_PICKLIST = "created the picklist item"
    UPDATED_PICKLIST_TEXT = 'updated picklist text from "{old_text}" to "{new_text}"'
    UPDATED_PICKLIST_NAME = 'updated picklist name from "{old_name}" to "{new_name}"'
    DEACTIVATE_PICKLIST = "deactivated the picklist item"
    REACTIVATE_PICKLIST = "reactivated the picklist item"

    UPDATED_EXHIBITION_DETAILS_TITLE = 'updated exhibition title from "{old_title}" to "{new_title}"'
    UPDATED_EXHIBITION_DETAILS_START_DATE = 'updated exhibition start date to "{new_first_exhibition_date}"'
    UPDATED_EXHIBITION_DETAILS_REQUIRED_BY_DATE = 'updated required by date to "{new_required_by_date}"'
    UPDATED_EXHIBITION_DETAILS_REASON_FOR_CLEARANCE = (
        'updated exhibition reason for clearance to "{new_reason_for_clearance}"'
    )
    UPDATED_ROUTE_OF_GOODS = 'updated {route_of_goods_field} from "{previous_value}" to "{new_value}"'

    def format(self, payload):
        text = self.value.format(**payload)
        if text[-1] not in [":", ".", "?"]:
            return f"{text}."

        return text
