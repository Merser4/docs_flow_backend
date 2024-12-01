from rest_framework import serializers


class ProjectsListAPIResponseSerializer(serializers.Serializer):

    id = serializers.IntegerField(min_value=1)
    name = serializers.CharField()


class StoresListAPIResponseSerializer(serializers.Serializer):

    id = serializers.IntegerField(min_value=1)
    name = serializers.CharField()
    type = serializers.CharField()
    project_id = serializers.IntegerField(min_value=1)


class RelationTablesListAPIResponseSerializer(serializers.Serializer):

    id = serializers.IntegerField(min_value=1)
    name = serializers.CharField()
    store_id = serializers.IntegerField(min_value=1)


class RelationTableGraphAPIResponseSerializer(serializers.Serializer):

    id = serializers.IntegerField(min_value=1)
    name = serializers.CharField()
    type = serializers.CharField()
    order = serializers.IntegerField(min_value=1)
    field_id = serializers.IntegerField(min_value=1, allow_null=True)
    table_id = serializers.IntegerField(min_value=1)
    table_name = serializers.CharField()
    store_id = serializers.IntegerField(min_value=1)
    store_name = serializers.CharField()


class RelationTableSaveSnapshotAPIRequestSerializer(serializers.Serializer):

    nodes = serializers.JSONField()
    edges = serializers.JSONField(default=[])
