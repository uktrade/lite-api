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
         , ap.id "party_on_application_id"
         , ap.created_at "party_on_application_created_at"
         , ap.updated_at "party_on_application_updated_at"
         , deleted_at "party_on_application_deleted_at"
         , application_id
         , party_id
         , pp.created_at "party_created_at"
         , pp.updated_at "party_updated_at"
         , pp.name
         , address
         , website
         , pp.type
         , sub_type
         , role
         , country.id "country_id"
         , country.name "country_name"
         , country.report_name "spire_country_name"
         , country.type "country_type"
         , is_eu "country_is_eu"
         , pp.copy_of_id "party_is_clone_of_party_id"
         , pp.organisation_id "party_organisation_id"
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
         , ag.report_summary
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
           c.report_name "spire_country_name",
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

SLA_CASES = """
select cases_case.reference_code
     , cases_case.submitted_at
     , sla_days
     , sla_remaining_days
     , sla_updated_at
     , statuses_casestatus.status "case_status"
     , ll.status                  "licence_status"
     , advice.type                "advice_type"
     , advice.created_at          "advice_created_at"
     , string_agg(DISTINCT advice_denial_reasons.denialreason_id,
                  ',')            "denial_reasons"
from cases_case
         join statuses_casestatus
              on cases_case.status_id = statuses_casestatus.id
         left outer join applications_baseapplication on cases_case.id =
                                                         applications_baseapplication.case_ptr_id
         left outer join advice on cases_case.id = advice.case_id
         left outer join advice_denial_reasons
                         on advice.id = advice_denial_reasons.advice_id
         left outer join licences_licence ll on cases_case.id = ll.case_id
where
    statuses_casestatus.status != 'draft'
    and advice.created_at between %(start_date)s::date and %(end_date)s::date
group by cases_case.reference_code, cases_case.submitted_at, sla_days,
         sla_remaining_days, sla_updated_at, statuses_casestatus.status,
         ll.status, advice.type, advice.created_at
;
"""

APPLICATIONS_FINALISED_SUMMARY = """
With applications as (
    select
        cc.reference_code
        , cs.status "case_status"
        , cc.id as "case_id"
        , ct.reference "case_type"
        , sa.export_type  "export_type"
        , intended_end_use
        , agreed_to_foi
        , foi_reason
        , submitted_at
        , o.name  "licensee"
        , last_closed_at
    from applications_standardapplication sa
    join applications_baseapplication ab on sa.baseapplication_ptr_id = ab.case_ptr_id
    join cases_case cc on ab.case_ptr_id = cc.id
    join cases_casetype ct on cc.case_type_id = ct.id
    join statuses_casestatus cs on cc.status_id = cs.id
    join organisation o on cc.organisation_id = o.id
    where cc.created_at between %(start_date)s::date and %(end_date)s::date
    and cs.status in ('closed', 'deregistered', 'suspended', 'revoked', 'surrendered', 'withdrawn', 'finalised')
    ),
advices as (
    select
        case_id    "case_id",
        type       "type",
        text       "text",
        denialreason_id    "dn_id"
    from advice
    left outer join advice_denial_reasons dn on dn.advice_id = advice.id
),
licences as (
    select
        ll.reference_code "reference_code"
        , case_id
        , status
    from licences_licence ll
),
goods as (
select cc.reference_code         "licence_ref"
        , sa.baseapplication_ptr_id "application_id"
        , g.id                      "good_id"
        , g.name                    "good_name"
        , g.description             "good_desc"
        , ct.reference              "case_type"
        , concat(ct.reference, ' ', '(', sa.export_type, ')') "application_type"
        , cs.status
        , ag.is_good_incorporated   "good_incorporated"
        , ag.report_summary
        , COALESCE(ag.is_good_controlled, g.is_good_controlled) "is_good_controlled"
        , ag.value                  "good_value"
        , ag.quantity               "good_quantity"
        , (
            select usage from licences_goodonlicence
            where good_id = ag.good_id
        ) "licence_usage"
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
and cs.status in ('closed', 'deregistered', 'suspended', 'revoked', 'surrendered', 'withdrawn', 'finalised')
), party as (
select reference_code         "licence_ref"
        , application_id
        , pp.name
        , pp.type
        , sub_type
        , country.name "country_name"
        , country.report_name "spire_country_name"
        , country.type "country_type"
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
and cs.status in ('closed', 'deregistered', 'suspended', 'revoked', 'surrendered', 'withdrawn', 'finalised')
) select
applications.case_type "Case type",
applications.export_type "Export type",
applications.licensee "Licensee",
applications.intended_end_use "End use",
not applications.agreed_to_foi "FOI Objection flag",
applications.foi_reason "FOI Objection",
applications.submitted_at "Submitted Datetime",
applications.case_status "Case closed reason",
applications.last_closed_at "Closed Datetime",
applications.reference_code "Licence reference",
applications.case_status "Case Status",
licences.status "Licence status",
(select string_agg(distinct advices.type, ',') from advices where advices.case_id = applications.case_id) "Outcome",
(select string_agg(distinct advices.dn_id, ',') from advices where advices.case_id = applications.case_id) "Reason for refusal",
(select string_agg(distinct goods.report_summary, ',') from goods where goods.application_id = applications.case_id) "Goods Ars",
(select string_agg(distinct goods.ratings, ',') from goods where goods.application_id = applications.case_id) "Goods Rating",
(select string_agg(cast((goods.good_quantity - goods.licence_usage) as text), ',') from goods where goods.application_id = applications.case_id) "Licence Remaining quantities",
(select sum(goods.good_value) from goods where goods.application_id = applications.case_id) "Total Goods value",
(select string_agg(distinct concat(goods.good_name, ': ', goods.good_desc), ',') from goods where goods.application_id = applications.case_id) "Description",
(select bool_or(goods.good_incorporated) from goods where goods.application_id = applications.case_id) "Incorporation",
(select string_agg(distinct party.name, ',') from party where party.licence_ref = applications.reference_code and type = 'end_user') "End Users",
(select string_agg(distinct party.country_name, ',') from party where party.licence_ref = applications.reference_code and type = 'end_user') "End User countries",
(select string_agg(distinct party.name, ',') from party where party.licence_ref = applications.reference_code and type = 'consignee') "Consignee",
(select string_agg(distinct party.country_name, ',') from party where party.licence_ref = applications.reference_code and type = 'consignee') "Consignee countries" ,
(select string_agg(distinct party.name, ',') from party where party.licence_ref = applications.reference_code and type = 'ultimate_end_user') "Ultimate End Users",
(select string_agg(distinct party.country_name, ',') from party where party.licence_ref = applications.reference_code and type = 'ultimate_end_user') "Ultimate End User countries",
(select string_agg(distinct party.name, ',') from party where party.licence_ref = applications.reference_code and type = 'third_party') "Third Party",
(select string_agg(distinct party.country_name, ',') from party where party.licence_ref = applications.reference_code and type = 'third_party') "Third Party Countries"
from
applications
left outer join licences on applications.case_id = licences.case_id
"""


MI_COMBINED_ALL_LIVE = """
with assignment as (
    select a.*, 
    ub.email,
    row_number() over (partition by a.case_id order by  a.id desc) as rn 
    from cases_caseassignment a 
    join users_govuser ug on a.user_id = ug.baseuser_ptr_id
    join users_baseuser ub on ug.baseuser_ptr_id = ub.id
), goods as (
select cc.reference_code         "licence_ref"
        , sa.baseapplication_ptr_id "application_id"
        , g.id                      "good_id"
        , g.name                    "good_name"
        , g.description             "good_desc"
        , ct.reference              "case_type"
        , concat(ct.reference, ' ', '(', sa.export_type, ')') "application_type"
        , cs.status
        , ag.is_good_incorporated   "good_incorporated"
        , ag.report_summary
        , COALESCE(ag.is_good_controlled, g.is_good_controlled) "is_good_controlled"
        , ag.value                  "good_value"
        , ag.quantity               "good_quantity"
        , (
            select usage from licences_goodonlicence
            where good_id = ag.good_id
        ) "licence_usage"
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
and cs.status not in ('draft', 'closed', 'deregistered', 'suspended', 'revoked', 'surrendered', 'withdrawn', 'finalised', 'applicant_editing')
)
select 
    cases_casetype.reference "APP"
    , cases_case.reference_code "APPLICATION_REF"
    , now() "DATE_REPORT_PUBLISHED"
    , string_agg(DISTINCT end_user_cc.id, ', ') "END_USER_COUNTRIES"
    , string_agg(DISTINCT end_user_cc.report_name, ', ') "END_USER_SPIRE_COUNTRIES"
    , null "DATE_SENT_TO_OGD"
    , assignment.created_at "DATE_SENT_TO_ADVISOR"
    , 'NOT IN LITE' "DATE_RETURNED_BY_OGD"
    , string_agg(DISTINCT t.name, ', ') "SHORT_NAME"
    , string_agg(DISTINCT aq.name, ', ') "LEVEL"
    , 'NOT IN LITE' "RESPONSE_DUE_DATE"
    , 'NOT IN LITE' "COMMUNITY_NAME"
    , assignment.email "ADVISOR_NAME"
    , COALESCE(cc_sla.sla_days, 0) "WORKING_DAYS_ELAPSED"
    , organisation.name "APPLICANT"
    , applications_baseapplication.intended_end_use "END_USE"
    , string_agg(DISTINCT concat(goods.good_name, goods.good_desc, ' '), ', ') "GOODS_DESCRIPTIONS"
    , string_agg(DISTINCT goods.ratings, ', ') "GOODS_RATINGS"
    , string_agg(DISTINCT consignee_pp.name, ', ') "CONSIGNEE"
    , string_agg(DISTINCT consignee_cc.id, ', ') "CONSIGNEE_COUNTRY"
    , string_agg(DISTINCT consignee_cc.report_name, ', ') "CONSIGNEE_SPIRE_COUNTRY"
    , string_agg(DISTINCT end_user_cc.id, ', ') "END_USER_COUNTRY"
    , string_agg(DISTINCT end_user_cc.report_name, ', ') "END_USER_SPIRE_COUNTRY"
    , string_agg(DISTINCT end_user_pp.name, ', ') "END_USER"
    , string_agg(DISTINCT ultimate_end_user_cc.id, ', ') "ULTIMATE_END_USER_COUNTRY"
    , string_agg(DISTINCT ultimate_end_user_cc.report_name, ', ') "ULTIMATE_END_USER_SPIRE_COUNTRY"
    , string_agg(DISTINCT ultimate_end_user_pp.name, ', ') "ULTIMATE_END_USER"
    , string_agg(DISTINCT third_party_cc.id, ', ') "THIRD_PARTY_COUNTRY"
    , string_agg(DISTINCT third_party_cc.report_name, ', ') "THIRD_PARTY_SPIRE_COUNTRY"
    , string_agg(DISTINCT third_party_pp.name, ', ') "THIRD_PARTY"
    , cases_case.sla_days "TOTAL_GOVERNMENT_DAYS"
     , sla_remaining_days "REMAINING_GOVERNMENT_DAYS"
     , statuses_casestatus.status "case_status"
     , ll.status                  "licence_status"
     , cases_case.id "case_id"
     , cases_case.submitted_at "case_submitted_at"
     , count(cecjuq.id) as "open_ecju_queries"
     , string_agg(DISTINCT edd.name, ', ') "DENIAL_MATCH"
from cases_case
         join statuses_casestatus
              on cases_case.status_id = statuses_casestatus.id
         join cases_casetype on cases_case.case_type_id = cases_casetype.id
         left outer join applications_baseapplication on cases_case.id =
                                                         applications_baseapplication.case_ptr_id
         left outer join licences_licence ll on cases_case.id = ll.case_id
         left outer join applications_partyonapplication ap on applications_baseapplication.case_ptr_id = ap.application_id
         left outer join parties_party end_user_pp on ap.party_id = end_user_pp.id and end_user_pp.type = 'end_user'
         left outer join countries_country end_user_cc on end_user_pp.country_id = end_user_cc.id
         left outer join parties_party consignee_pp on ap.party_id = consignee_pp.id and consignee_pp.type = 'consignee'
         left outer join countries_country consignee_cc on consignee_pp.country_id = consignee_cc.id
         left outer join parties_party ultimate_end_user_pp on ap.party_id = ultimate_end_user_pp.id and ultimate_end_user_pp.type = 'ultimate_end_user'
         left outer join countries_country ultimate_end_user_cc on ultimate_end_user_pp.country_id = ultimate_end_user_cc.id
         left outer join parties_party third_party_pp on ap.party_id = third_party_pp.id and third_party_pp.type = 'third_party'
         left outer join countries_country third_party_cc on third_party_pp.country_id = third_party_cc.id
         left outer join assignment on cases_case.id = assignment.case_id and assignment.rn = 1
         left outer join cases_case_queues on cases_case.id = cases_case_queues.case_id
         left outer join queue aq on cases_case_queues.queue_id = aq.id
         left outer join teams_team t on aq.team_id = t.id
         left outer join organisation on cases_case.organisation_id = organisation.id
         left outer join goods on cases_case.id = goods.application_id
         left outer join cases_ecjuquery cecjuq on cases_case.id = cecjuq.case_id and cecjuq.responded_at is NULL
         left outer join cases_caseassignmentsla cc_sla on aq.id = cc_sla.queue_id and cases_case.id = cc_sla.case_id
         left outer join applications_denialmatchonapplication ad on applications_baseapplication.case_ptr_id = ad.application_id
         left outer join external_data_denial edd on ad.denial_id = edd.id
where
    statuses_casestatus.status != 'draft'
    and
    statuses_casestatus.status not in ('closed', 'deregistered', 'suspended', 'revoked', 'surrendered', 'withdrawn', 'finalised', 'applicant_editing')
    and cases_case.created_at between %(start_date)s::date and %(end_date)s::date
group by cases_case.reference_code, cases_case.submitted_at, cases_case.sla_days, cc_sla.sla_days,
         sla_remaining_days, sla_updated_at, statuses_casestatus.status,
         ll.status, cases_casetype.reference, cases_case.id, assignment.email,
         assignment.created_at, organisation.name, applications_baseapplication.intended_end_use
order by submitted_at
;
"""


STRATEGIC_EXPORT_CONTROLS_YEAR_QTR = """
with changes as (
    select ll.created_at "licence_created_at",
           ll.updated_at,
           ll.id,
           start_date,
           duration,
           case_id,
           ll.reference_code  "licence_ref",
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
           extract(year from last_closed_at) as report_year,
           extract(quarter from last_closed_at) as report_quarter,
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
           agreed_to_foi,
           reference  "case_type",
           sa.export_type "case_sub_type",
           ct.sub_type,
           ct.type,
           ct.id,
           case is_good_incorporated
              when true then 'Incorporation' else ct.reference
           end as p_class,
           case is_good_incorporated
              when true then 'Incorporation' else sa.export_type
           end as p_class_subtype,
           case cle.category
              when 'Human Rights' then '1' else '0'
           end as torture_flag,
           cs.status  "s_class",
           ag.created_at,
           ag.updated_at,
           ag.id,
           quantity,
           unit,
           value,
           is_good_incorporated,
           is_military_end_use_controls,
           ag.application_id,
           ag.good_id,
           item_type,
           other_item_type,
           g.is_good_controlled
           is_pv_graded,
           g.status,
           g.report_summary,
           gcle.id,
           gcle.good_id,
           controllistentry_id,
           cle.id,
           cle.category  "cle_category",
           rating,
           text,
           parent_id,
           category,
           ap.id,
           ap.created_at,
           ap.updated_at,
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
           c.id  "dest_country_id",
           c.name "country_name",
           c.report_name "spire_country_name",
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
             join statuses_casestatus cs on cc.status_id = cs.id
             join applications_goodonapplication ag
                  on ab.case_ptr_id = ag.application_id
             join applications_standardapplication sa
                  on ab.case_ptr_id = sa.baseapplication_ptr_id
             join good g on ag.good_id = g.id
             left outer join good_control_list_entries gcle on g.id = gcle.good_id
             left outer join control_list_entry cle on gcle.controllistentry_id = cle.id
             left outer join applications_partyonapplication ap
                       on ab.case_ptr_id = ap.application_id
             left join parties_party pp on ap.party_id = pp.id
             left join countries_country c on pp.country_id = c.id
)
select
       good_audit_id  "Incident Id",
       concat(report_year, 'Q' , report_quarter) "Report Quarter",
       changes.case_ref  "Licence Ref",
       start_date,
       licence_created_at,
       changes.case_type,
       changes.case_sub_type,
       changes.is_good_incorporated  "Incorporation Flag",
       changes.torture_flag  "Torture Flag",
       changes.p_class  "P class",
       changes.p_class_subtype  "P class subtype",
       changes.s_class  "S class",
       changes.is_military_end_use_controls  "T class (is military end use controls)",
       'NOT IN LITE'  "Temp flag",
       changes.last_closed_at   "Report Date",
       changes.country_name  "Country name",
       changes.dest_country_id   "Destination Country Id",
       changes.rating  "Report rating",
       changes.quantity,
       changes.unit,
       changes.value,
       changes.audit_created_at,
       'NOT IN LITE'  "Country Map id"
from changes
where
    licence_created_at between %(start_date)s::date and %(end_date)s::date
    or audit_created_at between %(start_date)s::date and %(end_date)s::date
order by audit_created_at desc;
"""
