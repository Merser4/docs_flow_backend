import json

from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not settings.STASH_FILE_PATH.exists():
            with settings.STASH_FILE_PATH.open(mode='w') as json_file:
                json.dump({}, json_file)

        need_actual_stash_file = False
        with settings.STASH_FILE_PATH.open() as json_file:
            data = json.load(json_file) or {}
            if data.get('relation_table_graphs') is None or data.get('is_actual') is None:
                need_actual_stash_file = True

        if need_actual_stash_file:
            from apps.instance.utils.graph import RelationTableGraphUtil

            with settings.STASH_FILE_PATH.open(mode='w') as json_file:
                stash_file_data = {
                    'relation_table_graphs': [list(graph) for graph in RelationTableGraphUtil.get_actual_graphs()],
                    'is_actual': True,
                }
                json.dump(stash_file_data, json_file)
