GOODS_AND_RATINGS = {
    "applications": """
    select 
        cc.reference_code
        , cc.id as "case_id"
        , sa.export_type
        , reference_number_on_information_form
        , have_you_been_informed
        , is_shipped_waybill_or_lading
        , non_waybill_or_lading_route_details
        , is_temp_direct_control
        , proposed_return_date
        , temp_direct_control_details
        , temp_export_details
        , trade_control_activity
        , trade_control_activity_other
        , trade_control_product_categories
        , ab.name
        , activity
        , ab.usage
        , clearance_level
        , compliant_limitations_eu_ref
        , informed_wmd_ref
        , is_compliant_limitations_eu
        , is_eu_military
        , is_informed_wmd
        , is_military_end_use_controls
        , is_suspected_wmd
        , military_end_use_controls_ref
        , suspected_wmd_ref
        , intended_end_use
        , agreed_to_foi
        , cc.created_at
        , cc.updated_at
        , submitted_at
        , case_officer_id
        , organisation_id
        , o.name
        , o.vat_number
        , o.eori_number
        , cs.status
        , case_type_id
        , copy_of_id
        , last_closed_at
        , sla_days
        , sla_remaining_days
        , sla_updated_at
        , submitted_by_id
    from applications_standardapplication sa 
    join applications_baseapplication ab on sa.baseapplication_ptr_id = ab.case_ptr_id
    join cases_case cc on ab.case_ptr_id = cc.id
    join statuses_casestatus cs on cc.status_id = cs.id
    join organisation o on cc.organisation_id = o.id
    where
         cc.created_at between %(start_date)s::date and %(end_date)s::date
         and cs.status != 'draft'
    """,
    "licence": """
    select
        ll.reference_code "reference_code"
        , ll.created_at "created_at"
        , ll.updated_at "updated_at"
        , ll.id "licence_id"
        , start_date
        , duration
        , case_id
        , hmrc_integration_sent_at
        , status
        , end_date 
    from licences_licence ll
    join cases_case cc on ll.case_id = cc.id
    join applications_baseapplication ab on cc.id = ab.case_ptr_id
    join applications_standardapplication "as" on ab.case_ptr_id = "as".baseapplication_ptr_id
    WHERE 
        ll.created_at between %(start_date)s::date and %(end_date)s::date
        and status != 'draft'
    """,
    "parties": """
    select reference_code         "licence_ref"
         , ap.id
         , ap.created_at
         , ap.updated_at
         , deleted_at
         , application_id
         , party_id
         , pp.created_at
         , pp.updated_at
         , pp.name
         , address
         , website
         , pp.type
         , sub_type
         , role
         , country.id
         , country.name
         , country.type
         , is_eu
         , pp.copy_of_id
         , pp.organisation_id
         , pp.clearance_level
         , descriptors
         , details
         , email
         , phone_number
         , role_other
         , sub_type_other
    from applications_standardapplication sa
            join applications_baseapplication ab
                  on sa.baseapplication_ptr_id = ab.case_ptr_id
            join applications_partyonapplication ap
                              on ab.case_ptr_id = ap.application_id
            join cases_case cc on ab.case_ptr_id = cc.id
            join statuses_casestatus cs on cc.status_id = cs.id
            join parties_party pp on ap.party_id = pp.id
            join countries_country country on pp.country_id = country.id
    where cc.created_at between %(start_date)s::date and %(end_date)s::date
    and cs.status != 'draft'
    """,
    "goods_control_list_entries": """
WITH goods as (
    select cc.reference_code         "licence_ref"
         , sa.baseapplication_ptr_id "application_id"
         , g.id                      "good_id"
         , cc.id                     "case_id"
         , g.part_number             "good_part_no"
         , g.description             "good_desc"
         , ct.reference              "case_type"
         , cs.status
         , ag.is_good_incorporated
         , COALESCE(ag.is_good_controlled, g.is_good_controlled) "is_good_controlled"
         , sa.export_type
         , g.is_military_use
         , ag.value
         , ag.quantity
         , (
                with 
                _good as (
                 select good_id
                ),
                application_rating as (
                    select 
                    ag.good_id
                    , c.rating "rating"
                    from control_list_entry c 
                    join applications_goodonapplication_control_list_entries agcle  on agcle.controllistentry_id = c.id 
                    where agcle.goodonapplication_id = ag.id
                ), good_rating as (
                    select 
                    gcle.good_id
                    , c.rating "rating"
                    from good_control_list_entries gcle 
                    join control_list_entry c on gcle.controllistentry_id = c.id 
                    where gcle.good_id = g.id
                    
                ) select string_agg(coalesce(ar.rating, gr.rating), ',' order by coalesce(ar.rating, gr.rating))
                    from _good
                    left outer join good_rating gr 
                        on _good.good_id = gr.good_id
                    left outer join application_rating ar 
                        on _good.good_id = gr.good_id
           ) "ratings"

    from applications_standardapplication sa
             join applications_baseapplication ab
                  on sa.baseapplication_ptr_id = ab.case_ptr_id
             join cases_case cc on ab.case_ptr_id = cc.id
             join statuses_casestatus cs on cc.status_id = cs.id
             join applications_goodonapplication ag
                  on ab.case_ptr_id = ag.application_id
             join good g on ag.good_id = g.id
             join cases_casetype ct on cc.case_type_id = ct.id
             left outer join licences_licence ll on cc.id = ll.case_id
    where cc.created_at between %(start_date)s::date and %(end_date)s::date
    and cs.status != 'draft'
)
select * from goods
order by licence_ref;
""",
}

LICENCES_WITH_GOOD_AMENDMENTS = """

with changes as (
    select ll.created_at "licence_created_at",
           ll.updated_at,
           ll.id,
           start_date,
           duration,
           case_id,
           ll.reference_code,
           hmrc_integration_sent_at,
           ll.status,
           end_date,
           cc.created_at,
           cc.updated_at,
           cc.id,
           cc.reference_code "case_ref",
           submitted_at,
           case_officer_id,
           cc.organisation_id,
           status_id,
           case_type_id,
           cc.copy_of_id,
           last_closed_at,
           sla_days,
           sla_remaining_days,
           sla_updated_at,
           submitted_by_id,
           case_ptr_id,
           ab.name,
           activity,
           usage,
           ab.clearance_level,
           compliant_limitations_eu_ref,
           informed_wmd_ref,
           is_compliant_limitations_eu,
           is_eu_military,
           is_informed_wmd,
           is_military_end_use_controls,
           is_suspected_wmd,
           military_end_use_controls_ref,
           suspected_wmd_ref,
           intended_end_use,
           agreed_to_foi,
           reference,
           ct.sub_type,
           ct.type,
           ct.id,
           ag.created_at,
           ag.updated_at,
           ag.id,
           quantity,
           unit,
           value,
           is_good_incorporated,
           ag.application_id,
           ag.good_id,
           item_type,
           other_item_type,
           g.created_at,
           g.updated_at,
           g.id              "g_id",
           g.description,
           g.is_good_controlled
                             is_pv_graded,
           part_number,
           g.status,
           missing_document_reason,
           g.comment,
           grading_comment,
           g.report_summary,
           g.organisation_id,
           pv_grading_details_id,
           component_details,
           information_security_details,
           is_component,
           is_military_use,
           item_category,
           modified_military_use_details,
           uses_information_security,
           software_or_technology_details,
           coalesce(ag.firearm_details_id, g.firearm_details_id),
           gcle.id,
           gcle.good_id,
           controllistentry_id,
           cle.id,
           rating,
           text,
           parent_id,
           category,
           ap.id,
           ap.created_at,
           ap.updated_at,
           deleted_at,
           ap.application_id,
           party_id,
           pp.created_at,
           pp.updated_at,
           pp.id,
           pp.name,
           address,
           website,
           pp.type,
           pp.sub_type,
           role,
           pp.copy_of_id,
           country_id,
           pp.organisation_id,
           pp.clearance_level,
           descriptors,
           details,
           email,
           phone_number,
           role_other,
           sub_type_other,
           c.id,
           c.name "country_name",
           c.type,
           is_eu,
           good_ata.id "good_audit_id",
           good_ata.verb,
           good_ata.payload,
           good_ata.created_at "audit_created_at"
    from licences_licence ll
             join cases_case cc on ll.case_id = cc.id
             join audit_trail_audit good_ata
                       on cc.id::varchar = good_ata.target_object_id
             join applications_baseapplication ab on cc.id = ab.case_ptr_id
             join cases_casetype ct on cc.case_type_id = ct.id
             join applications_goodonapplication ag
                  on ab.case_ptr_id = ag.application_id
             join good g on ag.good_id = g.id
             left outer join good_control_list_entries gcle on g.id = gcle.good_id
             left outer join control_list_entry cle on gcle.controllistentry_id = cle.id
             left outer join applications_partyonapplication ap
                       on ab.case_ptr_id = ap.application_id
             left join parties_party pp on ap.party_id = pp.id
             left join countries_country c on pp.country_id = c.id
)
select
       good_audit_id,
       changes.case_ref,
       start_date,
       licence_created_at,
       changes.reference,
       changes.is_good_incorporated,
       changes.rating,
       changes.country_name,
       changes.quantity,
       changes.unit,
       changes.value,
       changes.verb,
    changes.audit_created_at
from changes where
                   licence_created_at between %(start_date)s::date and %(end_date)s::date
                   or audit_created_at between %(start_date)s::date and %(end_date)s::date
order by audit_created_at desc;
"""
