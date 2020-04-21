from rest_framework import serializers

from conf.helpers import str_to_bool
from conf.serializers import ControlListEntryField
from flags.enums import SystemFlags
from lite_content.lite_api import strings
from picklists.models import PicklistItem


def initialize_good_or_goods_type_control_list_entries_serializer(self):
    if str_to_bool(self.get_initial().get("is_good_controlled")):
        if not self.get_initial().get("control_list_entries"):
            raise serializers.ValidationError(
                {"control_list_entries": ["At least one control list entry must be set when the product is controlled"]}
            )
        self.fields["control_list_entries"] = ControlListEntryField(many=True)
        self.fields["report_summary"] = serializers.PrimaryKeyRelatedField(
            queryset=PicklistItem.objects.all(),
            required=True,
            error_messages={
                "required": strings.Picklists.REQUIRED_REPORT_SUMMARY,
                "null": strings.Picklists.REQUIRED_REPORT_SUMMARY,
            },
        )


def update_good_or_goods_type_control_list_entries_details(instance, validated_data):
    instance.comment = validated_data.get("comment")

    report_summary = validated_data.get("report_summary")
    instance.report_summary = report_summary.text if report_summary else ""

    if str_to_bool(instance.is_good_controlled):
        if not instance.control_list_entries:
            raise serializers.ValidationError(
                {"control_list_entries": ["At least one control list entry must be set when the product is controlled"]}
            )
        instance.control_list_entries.set(validated_data.get("control_list_entries"))
    else:
        instance.control_list_entries.clear()

    instance.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
    return instance
