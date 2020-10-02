OGL_SUMMARY = """
with ogls as (
    select ogl.id                         "OGL Id",
           ogl.name                       "OGL Name",
           CASE
               WHEN ogl.status = 'deactivated'
                   THEN ogl.status END    "OGL Deactivated",
           CASE
               WHEN ogl.status = 'deactivated'
                   THEN aa.updated_at END "OGL Deactivated date"
    from open_general_licence ogl
             left outer join audit_trail_audit aa
                             on aa.action_object_object_id = ogl.id::varchar
                                 and lower(aa.payload ->> 'key') = 'status'
                                 and aa.payload ->> 'new' = 'deactivated'
),
     registrations as (
         select oglc.open_general_licence_id, cc.id, cc.created_at
         from cases_case cc
                  join licences_licence ll on cc.id = ll.case_id
                  join open_general_licence_case oglc
                       on cc.id = oglc.case_ptr_id
         WHERE ll.created_at between %(start_date)s::date and %(end_date)s::date
     ),
     suspensions as (
         select oglc.open_general_licence_id,
                cc.id                           "case_id",
                ll.id                           "licence_id",
                cc.created_at,
                aa.created_at,
                aa.payload,
                aa.verb,
                aa.payload -> 'status' -> 'new' "new_status"
         from cases_case cc
                  join licences_licence ll on cc.id = ll.case_id
                  join open_general_licence_case oglc
                       on cc.id = oglc.case_ptr_id
                  join audit_trail_audit aa
                       on cc.id::varchar = aa.target_object_id
         WHERE verb = 'updated_status'
           and lower(aa.payload -> 'status' ->> 'new') = 'suspended'
           and ll.created_at between %(start_date)s::date and %(end_date)s::date
     ),
     revocations as (
         select oglc.open_general_licence_id,
                cc.id                           "case_id",
                ll.id                           "licence_id",
                cc.created_at,
                aa.created_at,
                aa.payload,
                aa.verb,
                aa.payload -> 'status' -> 'new' "new_status"
         from cases_case cc
                  join licences_licence ll on cc.id = ll.case_id
                  join open_general_licence_case oglc
                       on cc.id = oglc.case_ptr_id
                  join audit_trail_audit aa
                       on cc.id::varchar = aa.target_object_id
         WHERE verb = 'updated_status'
           and lower(aa.payload -> 'status' ->> 'new') = 'revoked'
           and ll.created_at between %(start_date)s::date and %(end_date)s::date
     )
select "OGL Id",
       "OGL Name",
       (select count(registrations.id)
        from registrations
        where registrations.open_general_licence_id = "OGL Id") "Registrations",
       (select count(suspensions.open_general_licence_id)
        from suspensions
        where suspensions.open_general_licence_id = "OGL Id")   "Suspensions",
       (select count(revocations.open_general_licence_id)
        from revocations
        where revocations.open_general_licence_id = "OGL Id")   "Revocations",
       "OGL Deactivated",
       "OGL Deactivated date"
from ogls
group by "OGL Id", "OGL Name", "OGL Deactivated", "OGL Deactivated date"

"""
