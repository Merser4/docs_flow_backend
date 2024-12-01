from pathlib import Path
import json

from django.conf import settings
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from apps.instance.models import Project, Store, RelationTable, RelationTableField
from apps.instance.serializers import (
    ProjectsListAPIResponseSerializer,
    StoresListAPIResponseSerializer,
    RelationTablesListAPIResponseSerializer,
    RelationTableGraphAPIResponseSerializer,
    RelationTableSaveSnapshotAPIRequestSerializer,
)
from apps.instance.utils.graph import RelationTableGraphUtil
from apps.instance.utils.snapshot import make_snapshot_file_name
from apps.instance.utils.instance_tree import InstanceError
from apps.instance.utils.instance_processor import InstanceProcessor, OperationError


class ProjectsListAPI(APIView):

    response_serializer = ProjectsListAPIResponseSerializer

    def get(self, request):
        projects_qs = Project.objects.all()
        return Response(status=HTTP_200_OK, data=self.response_serializer(instance=projects_qs, many=True).data)


class StoresListAPI(APIView):

    response_serializer = StoresListAPIResponseSerializer

    def get(self, request, project_id: int):
        stores_qs = Store.objects.filter(project_id=project_id)
        return Response(status=HTTP_200_OK, data=self.response_serializer(instance=stores_qs, many=True).data)


class RelationTablesListAPI(APIView):

    response_serializer = RelationTablesListAPIResponseSerializer

    def get(self, request, store_id: int):
        relation_tables_qs = RelationTable.objects.filter(store_id=store_id)
        return Response(status=HTTP_200_OK, data=self.response_serializer(instance=relation_tables_qs, many=True).data)


class RelationTableGraphAPI(APIView):

    response_serializer = RelationTableGraphAPIResponseSerializer

    def get(self, request, relation_table_id: int):
        graph = RelationTableGraphUtil.get_graph(relation_table_id=relation_table_id)
        relation_table_fields_qs = (
            RelationTableField.objects.filter(relation_table_id__in=graph)
            .annotate(
                table_id=F('relation_table_id'),
                table_name=F('relation_table__name'),
                store_id=F('relation_table__store_id'),
                store_name=F('relation_table__store__name'),
            )
            .order_by('table_name', 'order')
        )
        return Response(
            status=HTTP_200_OK,
            data=self.response_serializer(instance=relation_table_fields_qs, many=True).data,
        )


class RelationTableLoadSnapshotAPI(APIView):

    def get(self, request, relation_table_id: int):
        relation_table = RelationTable.objects.filter(id=relation_table_id).first()
        if not relation_table or not relation_table.snapshot:
            return Response(status=HTTP_404_NOT_FOUND)

        with open(relation_table.snapshot) as json_file:
            snapshot_data = json.load(json_file)

        return Response(status=HTTP_200_OK, data=snapshot_data)


class RelationTableSaveSnapshotAPI(APIView):

    request_serializer = RelationTableSaveSnapshotAPIRequestSerializer

    def post(self, request, relation_table_id: int):
        if not RelationTable.objects.filter(id=relation_table_id).exists():
            return Response(status=HTTP_404_NOT_FOUND)

        serializer = self.request_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filename = make_snapshot_file_name(body=serializer.validated_data)
        full_file_path = Path(settings.RELATION_TABLE_SNAPSHOTS_DIR, filename)
        with full_file_path.open(mode='w') as json_file:
            json.dump(serializer.validated_data, json_file)

        graph = RelationTableGraphUtil.get_graph(relation_table_id=relation_table_id)
        RelationTable.objects.filter(id__in=graph).update(snapshot=str(full_file_path))
        return Response(status=HTTP_204_NO_CONTENT)


class SyncAPI(APIView):

    def post(self, request):
        RelationTable.objects.update(snapshot=None)
        for snapshot_file in settings.RELATION_TABLE_SNAPSHOTS_DIR.iterdir():
            snapshot_file.unlink(missing_ok=True)

        with settings.STASH_FILE_PATH.open() as json_file:
            data = json.load(json_file)

        data['relation_table_graphs'] = [list(graph) for graph in RelationTableGraphUtil.get_actual_graphs()]
        data['is_actual'] = True
        with settings.STASH_FILE_PATH.open(mode='w') as json_file:
            json.dump(data, json_file)

        return Response(status=HTTP_204_NO_CONTENT)
