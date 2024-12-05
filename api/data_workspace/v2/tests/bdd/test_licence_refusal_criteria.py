import uuid

from pytest_bdd import parsers, scenarios, when

scenarios("./scenarios/licence_refusal_criteria.feature")


@when(parsers.parse("the application is refused with criteria:{criteria}"))
def when_the_application_is_refused_with_criteria(
    submitted_standard_application, refuse_application, parse_table, criteria
):
    criteria = [c[0] for c in parse_table(criteria)]
    refuse_application(submitted_standard_application, criteria)
    refused_application = submitted_standard_application
    licence_decision = refused_application.licence_decisions.get()
    old_pk = licence_decision.pk
    licence_decision.pk = uuid.UUID("03fb08eb-1564-4b68-9336-3ca8906543f9")  # /PS-IGNORE
    licence_decision.save()
    licence_decision.denial_reasons.through.objects.filter(licencedecision_id=old_pk).update(
        licencedecision_id=licence_decision.pk
    )


@when("the application is issued")
def when_the_application_is_issued(
    issue_licence,
    submitted_standard_application,
):
    issue_licence(submitted_standard_application)

    submitted_standard_application.refresh_from_db()
    issued_application = submitted_standard_application

    return issued_application
