GOODS_AND_RATINGS = """
WITH goods as (
    select ll.reference_code         "licence_ref"
         , sa.baseapplication_ptr_id "application_id"
         , ll.id "licence_pk"
         , g.id                      "good_id"
         , cc.id                     "case_id"
         , pp.id                     "party_id"
         , cle.rating
         , g.part_number             "good_part_no"
         , g.description             "good_desc"
         , ct.reference              "case_type"
         , c.name                    "country_name"
         , ll.status                 "licence_status"
         , ag.is_good_incorporated
         , sa.export_type
         , g.is_military_use
         , cle.category
         , pp.type
         , ag.value
         , ag.quantity

    from applications_standardapplication sa
             join applications_baseapplication ab
                  on sa.baseapplication_ptr_id = ab.case_ptr_id
             join cases_case cc on ab.case_ptr_id = cc.id
             join applications_goodonapplication ag
                  on ab.case_ptr_id = ag.application_id
             join good g on ag.good_id = g.id
             left outer join good_control_list_entries gcle on g.id = gcle.good_id
             left outer join control_list_entry cle on gcle.controllistentry_id = cle.id
             left outer join applications_partyonapplication ap
                             on ab.case_ptr_id = ap.application_id
             left outer join parties_party pp on ap.party_id = pp.id
             left outer join countries_country c on pp.country_id = c.id
             join cases_casetype ct on cc.case_type_id = ct.id
             join licences_licence ll on cc.id = ll.case_id
    where pp.type = 'end_user' 
    and ll.created_at between %(start_date)s::date and %(end_date)s::date
)
select * from goods
order by licence_ref;
-- select
--        case_type
--        , is_good_incorporated
--        ,  rating
--        , sum(value) "sum_value"
--        , sum(quantity) "sum_quantity"
-- from goods
-- group by
--     rollup(case_type, is_good_incorporated, rating);
"""
