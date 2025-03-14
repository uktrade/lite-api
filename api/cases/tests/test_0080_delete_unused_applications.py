from pytest_django.asserts import assertQuerysetEqual


def test_retain_siel_and_f680_applications(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0079_licencedecision_cases_licen_created_850df1_idx"))
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Case = old_state.apps.get_model("cases", "Case")
    CaseType = old_state.apps.get_model("cases", "CaseType")

    siel_case_type = CaseType.objects.get(
        type="application",
        sub_type="standard",
        reference="siel",
    )

    f680_case_type = CaseType.objects.get(
        type="application",
        sub_type="f680_clearance",
        reference="f680",
    )

    organisation = Organisation.objects.create(name="test")

    siel_case = Case.objects.create(
        case_type=siel_case_type,
        organisation=organisation,
    )
    f680_case = Case.objects.create(
        case_type=f680_case_type,
        organisation=organisation,
    )

    new_state = migrator.apply_tested_migration(("cases", "0080_delete_unused_applications"))
    Case = new_state.apps.get_model("cases", "Case")
    CaseType = new_state.apps.get_model("cases", "CaseType")

    assertQuerysetEqual(Case.objects.values_list("pk", flat=True), [f680_case.pk, siel_case.pk], ordered=False)


def test_remove_unused_applications(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0079_licencedecision_cases_licen_created_850df1_idx"))
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    CaseType = old_state.apps.get_model("cases", "CaseType")
    CaseStatus = old_state.apps.get_model("statuses", "CaseStatus")
    Flag = old_state.apps.get_model("flags", "Flag")
    GoodsQuery = old_state.apps.get_model("goods_query", "GoodsQuery")
    Good = old_state.apps.get_model("goods", "Good")
    Site = old_state.apps.get_model("organisations", "Site")
    Address = old_state.apps.get_model("addresses", "Address")
    Country = old_state.apps.get_model("countries", "Country")
    ComplianceSiteCase = old_state.apps.get_model("compliance", "ComplianceSiteCase")

    organisation = Organisation.objects.create(name="test")

    status = CaseStatus.objects.get(status="draft")

    good = Good.objects.create(organisation_id=organisation.pk)
    goods_query_case_type = CaseType.objects.get(
        type="query",
        sub_type="goods",
        reference="gqy",
    )
    goods_query = GoodsQuery.objects.create(
        status_id=status.pk, organisation_id=organisation.pk, case_type_id=goods_query_case_type.pk, good_id=good.pk
    )
    goods_query.flags.add(Flag.objects.get(name="PV grading query").pk)

    compliance_site_case_case_type = CaseType.objects.get(
        type="compliance",
        sub_type="compliance_site",
        reference="comp_c",
    )
    country = Country.objects.get(pk="GB")
    address = Address.objects.create(
        country_id=country.pk,
    )
    site = Site.objects.create(
        name="test",
        address=address,
    )
    ComplianceSiteCase.objects.create(
        status_id=status.pk,
        organisation_id=organisation.pk,
        case_type_id=compliance_site_case_case_type.pk,
        site_id=site.pk,
    )

    new_state = migrator.apply_tested_migration(("cases", "0080_delete_unused_applications"))
    GoodsQuery = new_state.apps.get_model("goods_query", "GoodsQuery")
    assert GoodsQuery.objects.count() == 0
    ComplianceSiteCase = new_state.apps.get_model("compliance", "ComplianceSiteCase")
    assert ComplianceSiteCase.objects.count() == 0
