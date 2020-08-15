from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.applications.enums import GoodsTypeCategory, ContractType
from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.libraries.get_applications import get_application
from api.applications.models import CountryOnApplication
from api.applications.serializers.open_application import ContractTypeDataSerializer, CountryOnApplicationViewSerializer
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.models import Case
from api.conf.authentication import ExporterAuthentication
from api.conf.decorators import allowed_application_types, authorised_to_view_application, application_in_state
from api.conf.exceptions import BadRequestError
from api.flags.models import Flag
from api.static.countries.helpers import get_country
from api.static.countries.serializers import CountrySerializer
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.case_status_validate import is_case_status_draft
from api.users.models import ExporterUser


class ApplicationCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types([CaseTypeSubTypeEnum.OPEN])
    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        """
        View countries belonging to an open licence application
        """
        countries = CountryOnApplication.objects.select_related("country").filter(application_id=pk)
        countries_data = CountryOnApplicationViewSerializer(countries, many=True, read_only=True).data
        return JsonResponse(data={"countries": countries_data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @allowed_application_types([CaseTypeSubTypeEnum.OPEN])
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk):
        """ Add countries to an open licence application. """
        application = get_application(pk)
        if application.goodstype_category in GoodsTypeCategory.IMMUTABLE_DESTINATIONS:
            raise BadRequestError(detail="You cannot do this action for this type of open application")
        data = request.data
        country_ids = data.get("countries")

        # Validate that there are countries
        if not country_ids:
            return JsonResponse(
                data={"errors": {"countries": ["You have to pick at least one country"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_case_status_draft(application.status.status) and application.status.status in get_case_statuses(
            read_only=True
        ):
            return JsonResponse(
                data={
                    "errors": {"external_locations": [f"Application status {application.status.status} is read-only."]}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        else:
            previous_countries = CountryOnApplication.objects.filter(application=application)
            previous_country_ids = [
                str(previous_country_id)
                for previous_country_id in previous_countries.values_list("country__id", flat=True)
            ]
            new_countries = []

            if (
                is_case_status_draft(application.status.status)
                or application.status.status == CaseStatusEnum.APPLICANT_EDITING
            ):
                new_countries = [
                    get_country(country_id) for country_id in country_ids if country_id not in previous_country_ids
                ]
            else:
                for country_id in country_ids:
                    if previous_country_ids and country_id not in previous_country_ids:
                        return JsonResponse(
                            data={
                                "errors": {
                                    "countries": [
                                        "Go back and change your answer from ‘Change a site, or delete "
                                        "a good, third party or country’ to ’Change something else’."
                                    ]
                                }
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # Get countries to be removed
            removed_country_ids = list(set(previous_country_ids) - set(country_ids))
            removed_countries = previous_countries.filter(country__id__in=removed_country_ids)

            # Append new Countries to application (only in unsubmitted/applicant editing statuses)
            CountryOnApplication.objects.bulk_create(
                [CountryOnApplication(country=country, application=application) for country in new_countries]
            )

            countries_data = CountrySerializer(new_countries, many=True).data

            case = Case.objects.get(id=application.id)

            if new_countries:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_COUNTRIES_TO_APPLICATION,
                    target=case,
                    payload={"countries": [country.name for country in new_countries]},
                )

            if removed_countries:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.REMOVED_COUNTRIES_FROM_APPLICATION,
                    target=case,
                    payload={"countries": [country.country.name for country in removed_countries]},
                )

            removed_countries.delete()
            return JsonResponse(data={"countries": countries_data}, status=status.HTTP_201_CREATED)


class ApplicationContractTypes(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_in_state(is_major_editable=True)
    @allowed_application_types([CaseTypeSubTypeEnum.OPEN])
    def put(self, request, pk):
        application = get_application(pk)
        if application.goodstype_category in GoodsTypeCategory.IMMUTABLE_GOODS:
            raise BadRequestError(detail="You cannot do this action for this type of open application")

        data = request.data

        serialized_data, errors = self.validate_data(data)

        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        countries = data.get("countries")
        serialized_contract_types = serialized_data.get("contract_types")

        contract_types = [",".join(serialized_contract_types)]

        qs = CountryOnApplication.objects.filter(country__in=countries, application=application)

        qs.update(
            contract_types=contract_types, other_contract_type_text=serialized_data.get("other_contract_type_text")
        )

        [
            Flag.objects.get(name=ContractType.get_flag_name(contract_type)).countries_on_applications.set(qs)
            for contract_type in serialized_contract_types
        ]
        return JsonResponse(data={"countries_set": "success"}, status=status.HTTP_200_OK)

    @staticmethod
    def validate_data(data):
        serializer = ContractTypeDataSerializer(data=data)
        if serializer.is_valid():
            return serializer.data, None
        else:
            return None, serializer.errors


class LightCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types([CaseTypeSubTypeEnum.OPEN])
    def get(self, request, pk):
        application = get_application(pk)
        countries = [
            country
            for country in (
                CountryOnApplication.objects.filter(application_id=pk)
                .prefetch_related("country_id", "country__name")
                .values("contract_types", "other_contract_type_text", "country_id", "country__name")
            )
        ]
        return JsonResponse(
            data={"countries": countries, "status": application.status.status}, status=status.HTTP_200_OK
        )
