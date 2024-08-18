from rest_framework import serializers


class CommaSeparatedListField(serializers.Field):
    def to_internal_value(self, data: str) -> list:
        result = data.split(",")
        return [item.strip() for item in result]

    def to_representation(self, value: list) -> str:
        return ",".join(value)
