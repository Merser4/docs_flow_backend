from django.urls import path

from apps.instance.views import (
    ProjectsListAPI,
    StoresListAPI,
    RelationTablesListAPI,
    RelationTableGraphAPI,
    RelationTableLoadSnapshotAPI,
    RelationTableSaveSnapshotAPI,
    SyncAPI,
)

urlpatterns = [
    path('v1/projects/', ProjectsListAPI.as_view(), name='projects'),
    path('v1/projects/<int:project_id>/stores/', StoresListAPI.as_view(), name='stores'),
    path('v1/stores/<int:store_id>/relation_tables/', RelationTablesListAPI.as_view(), name='relation_tables'),
    path(
        'v1/relation_tables/<int:relation_table_id>/graph/',
        RelationTableGraphAPI.as_view(),
        name='relation_table_graph',
    ),
    path(
        'v1/relation_tables/<int:relation_table_id>/load_snapshot/',
        RelationTableLoadSnapshotAPI.as_view(),
        name='relation_table_load_snapshot',
    ),
    path(
        'v1/relation_tables/<int:relation_table_id>/save_snapshot/',
        RelationTableSaveSnapshotAPI.as_view(),
        name='relation_table_save_snapshot',
    ),
    path('v1/sync/', SyncAPI.as_view(), name='sync'),
]
