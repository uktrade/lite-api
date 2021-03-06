# Generated by Django 2.2.13 on 2020-06-12 11:08

from api import audit_trail
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit_trail", "0014_auto_20200604_0858"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audit",
            name="verb",
            field=models.CharField(
                choices=[
                    (audit_trail.enums.AuditType("created"), "created"),
                    (audit_trail.enums.AuditType("ogl_created"), "ogl_created"),
                    (audit_trail.enums.AuditType("ogl_field_edited"), "ogl_field_edited"),
                    (audit_trail.enums.AuditType("ogl_multi_field_edited"), "ogl_multi_field_edited"),
                    (audit_trail.enums.AuditType("add_flags"), "add_flags"),
                    (audit_trail.enums.AuditType("remove_flags"), "remove_flags"),
                    (audit_trail.enums.AuditType("good_reviewed"), "good_reviewed"),
                    (audit_trail.enums.AuditType("good_add_flags"), "good_add_flags"),
                    (audit_trail.enums.AuditType("good_remove_flags"), "good_remove_flags"),
                    (audit_trail.enums.AuditType("good_add_remove_flags"), "good_add_remove_flags"),
                    (audit_trail.enums.AuditType("destination_add_flags"), "destination_add_flags"),
                    (audit_trail.enums.AuditType("destination_remove_flags"), "destination_remove_flags"),
                    (audit_trail.enums.AuditType("add_good_to_application"), "add_good_to_application"),
                    (audit_trail.enums.AuditType("remove_good_from_application"), "remove_good_from_application"),
                    (audit_trail.enums.AuditType("add_good_type_to_application"), "add_good_type_to_application"),
                    (
                        audit_trail.enums.AuditType("remove_good_type_from_application"),
                        "remove_good_type_from_application",
                    ),
                    (
                        audit_trail.enums.AuditType("update_application_end_use_detail"),
                        "update_application_end_use_detail",
                    ),
                    (
                        audit_trail.enums.AuditType("update_application_temporary_export"),
                        "update_application_temporary_export",
                    ),
                    (audit_trail.enums.AuditType("removed_sites_from_application"), "removed_sites_from_application"),
                    (audit_trail.enums.AuditType("add_sites_to_application"), "add_sites_to_application"),
                    (
                        audit_trail.enums.AuditType("removed_external_locations_from_application"),
                        "removed_external_locations_from_application",
                    ),
                    (
                        audit_trail.enums.AuditType("add_external_locations_to_application"),
                        "add_external_locations_to_application",
                    ),
                    (
                        audit_trail.enums.AuditType("removed_countries_from_application"),
                        "removed_countries_from_application",
                    ),
                    (audit_trail.enums.AuditType("add_countries_to_application"), "add_countries_to_application"),
                    (audit_trail.enums.AuditType("add_additional_contact_to_case"), "add_additional_contact_to_case"),
                    (audit_trail.enums.AuditType("move_case"), "move_case"),
                    (audit_trail.enums.AuditType("assign_case"), "assign_case"),
                    (audit_trail.enums.AuditType("remove_case"), "remove_case"),
                    (audit_trail.enums.AuditType("remove_case_from_all_queues"), "remove_case_from_all_queues"),
                    (
                        audit_trail.enums.AuditType("remove_case_from_all_user_assignments"),
                        "remove_case_from_all_user_assignments",
                    ),
                    (audit_trail.enums.AuditType("clc_response"), "clc_response"),
                    (audit_trail.enums.AuditType("pv_grading_response"), "pv_grading_response"),
                    (audit_trail.enums.AuditType("created_case_note"), "created_case_note"),
                    (audit_trail.enums.AuditType("ecju_query"), "ecju_query"),
                    (audit_trail.enums.AuditType("updated_status"), "updated_status"),
                    (audit_trail.enums.AuditType("updated_application_name"), "updated_application_name"),
                    (
                        audit_trail.enums.AuditType("update_application_letter_reference"),
                        "update_application_letter_reference",
                    ),
                    (
                        audit_trail.enums.AuditType("update_application_f680_clearance_types"),
                        "update_application_f680_clearance_types",
                    ),
                    (
                        audit_trail.enums.AuditType("added_application_letter_reference"),
                        "added_application_letter_reference",
                    ),
                    (
                        audit_trail.enums.AuditType("removed_application_letter_reference"),
                        "removed_application_letter_reference",
                    ),
                    (audit_trail.enums.AuditType("assigned_countries_to_good"), "assigned_countries_to_good"),
                    (audit_trail.enums.AuditType("removed_countries_from_good"), "removed_countries_from_good"),
                    (audit_trail.enums.AuditType("created_final_advice"), "created_final_advice"),
                    (audit_trail.enums.AuditType("cleared_final_advice"), "cleared_final_advice"),
                    (audit_trail.enums.AuditType("created_team_advice"), "created_team_advice"),
                    (audit_trail.enums.AuditType("cleared_team_advice"), "cleared_team_advice"),
                    (audit_trail.enums.AuditType("created_user_advice"), "created_user_advice"),
                    (audit_trail.enums.AuditType("add_party"), "add_party"),
                    (audit_trail.enums.AuditType("remove_party"), "remove_party"),
                    (audit_trail.enums.AuditType("upload_party_document"), "upload_party_document"),
                    (audit_trail.enums.AuditType("delete_party_document"), "delete_party_document"),
                    (audit_trail.enums.AuditType("upload_application_document"), "upload_application_document"),
                    (audit_trail.enums.AuditType("delete_application_document"), "delete_application_document"),
                    (audit_trail.enums.AuditType("upload_case_document"), "upload_case_document"),
                    (audit_trail.enums.AuditType("generate_case_document"), "generate_case_document"),
                    (audit_trail.enums.AuditType("add_case_officer_to_case"), "add_case_officer_to_case"),
                    (audit_trail.enums.AuditType("remove_case_officer_from_case"), "remove_case_officer_from_case"),
                    (audit_trail.enums.AuditType("granted_application"), "granted_application"),
                    (audit_trail.enums.AuditType("finalised_application"), "finalised_application"),
                    (audit_trail.enums.AuditType("unassigned_queues"), "unassigned_queues"),
                    (audit_trail.enums.AuditType("unassigned"), "unassigned"),
                    (audit_trail.enums.AuditType("updated_letter_template_name"), "updated_letter_template_name"),
                    (
                        audit_trail.enums.AuditType("added_letter_template_case_types"),
                        "added_letter_template_case_types",
                    ),
                    (
                        audit_trail.enums.AuditType("updated_letter_template_case_types"),
                        "updated_letter_template_case_types",
                    ),
                    (
                        audit_trail.enums.AuditType("removed_letter_template_case_types"),
                        "removed_letter_template_case_types",
                    ),
                    (audit_trail.enums.AuditType("added_letter_template_decisions"), "added_letter_template_decisions"),
                    (
                        audit_trail.enums.AuditType("updated_letter_template_decisions"),
                        "updated_letter_template_decisions",
                    ),
                    (
                        audit_trail.enums.AuditType("removed_letter_template_decisions"),
                        "removed_letter_template_decisions",
                    ),
                    (
                        audit_trail.enums.AuditType("updated_letter_template_paragraphs"),
                        "updated_letter_template_paragraphs",
                    ),
                    (audit_trail.enums.AuditType("updated_letter_template_layout"), "updated_letter_template_layout"),
                    (
                        audit_trail.enums.AuditType("updated_letter_template_paragraphs_ordering"),
                        "updated_letter_template_paragraphs_ordering",
                    ),
                    (audit_trail.enums.AuditType("created_picklist"), "created_picklist"),
                    (audit_trail.enums.AuditType("updated_picklist_text"), "updated_picklist_text"),
                    (audit_trail.enums.AuditType("updated_picklist_name"), "updated_picklist_name"),
                    (audit_trail.enums.AuditType("deactivate_picklist"), "deactivate_picklist"),
                    (audit_trail.enums.AuditType("reactivate_picklist"), "reactivate_picklist"),
                    (
                        audit_trail.enums.AuditType("updated_exhibition_details_title"),
                        "updated_exhibition_details_title",
                    ),
                    (
                        audit_trail.enums.AuditType("updated_exhibition_details_start_date"),
                        "updated_exhibition_details_start_date",
                    ),
                    (
                        audit_trail.enums.AuditType("updated_exhibition_details_required_by_date"),
                        "updated_exhibition_details_required_by_date",
                    ),
                    (
                        audit_trail.enums.AuditType("updated_exhibition_details_reason_for_clearance"),
                        "updated_exhibition_details_reason_for_clearance",
                    ),
                    (audit_trail.enums.AuditType("updated_route_of_goods"), "updated_route_of_goods"),
                    (audit_trail.enums.AuditType("updated_organisation"), "updated_organisation"),
                    (audit_trail.enums.AuditType("created_organisation"), "created_organisation"),
                    (audit_trail.enums.AuditType("register_organisation"), "register_organisation"),
                    (audit_trail.enums.AuditType("rejected_organisation"), "rejected_organisation"),
                    (audit_trail.enums.AuditType("approved_organisation"), "approved_organisation"),
                    (audit_trail.enums.AuditType("removed_flag_on_organisation"), "removed_flag_on_organisation"),
                    (audit_trail.enums.AuditType("added_flag_on_organisation"), "added_flag_on_organisation"),
                    (audit_trail.enums.AuditType("rerun_routing_rules"), "rerun_routing_rules"),
                    (audit_trail.enums.AuditType("enforcement_check"), "enforcement_check"),
                    (audit_trail.enums.AuditType("updated_site"), "updated_site"),
                    (audit_trail.enums.AuditType("created_site"), "created_site"),
                    (audit_trail.enums.AuditType("updated_site_name"), "updated_site_name"),
                    (audit_trail.enums.AuditType("compliance_site_case_create"), "compliance_site_case_create"),
                    (
                        audit_trail.enums.AuditType("compliance_site_case_new_licence"),
                        "compliance_site_case_new_licence",
                    ),
                ],
                db_index=True,
                max_length=255,
            ),
        ),
    ]
