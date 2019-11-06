from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication, StandardApplication, \
    GoodOnApplication, ApplicationDenialReason, ApplicationDocument
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from documents.libraries.process_document import process_document
from goods.models import Good
from goods.serializers import GoodWithFlagsSerializer, GoodSerializer
from organisations.models import Site, ExternalLocation
from organisations.serializers import SiteViewSerializer
from static.denial_reasons.models import DenialReason
from static.units.enums import Units












