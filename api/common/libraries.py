from rest_framework import serializers

from api.conf.helpers import str_to_bool
from api.conf.serializers import ControlListEntryField
from api.flags.enums import SystemFlags
from lite_content.lite_api import strings


def initialize_good_or_goods_type_control_list_entries_serializer(self):
    if str_to_bool(self.get_initial().get("is_good_controlled")):
        if not self.get_initial().get("control_list_entries"):
            raise serializers.ValidationError(
                {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IF_CONTROLLED_ERROR]}
            )
        self.fields["control_list_entries"] = ControlListEntryField(many=True)
        self.fields["report_summary"] = serializers.CharField(
            required=True,
            allow_blank=False,
            allow_null=False,
            error_messages={
                "required": strings.Picklists.REQUIRED_REPORT_SUMMARY,
                "null": strings.Picklists.REQUIRED_REPORT_SUMMARY,
            },
        )


def update_good_or_goods_type_control_list_entries_details(instance, validated_data):
    instance.comment = validated_data.get("comment")
    instance.report_summary = validated_data.get("report_summary")

    if str_to_bool(instance.is_good_controlled):
        if not instance.control_list_entries:
            raise serializers.ValidationError(
                {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IF_CONTROLLED_ERROR]}
            )
        instance.control_list_entries.set(validated_data.get("control_list_entries"))
    else:
        instance.report_summary = ""
        instance.control_list_entries.clear()

    instance.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
    return instance
