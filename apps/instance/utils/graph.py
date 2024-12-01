import json

from django.conf import settings


class RelationTableGraphUtil:

    @staticmethod
    def get_actual_graphs() -> list[set[int]]:
        from apps.instance.models import RelationTableField

        relations = RelationTableField.objects.values_list('relation_table_id', 'field__relation_table_id')
        table_id_pairs = set()
        for source_table_id, destination_table_id in relations:
            if destination_table_id is None:
                destination_table_id = source_table_id

            table_id_pairs.add((source_table_id, destination_table_id))

        vertexes: dict[int, set[int]] = {}
        for source_table_id, destination_table_id in table_id_pairs:
            vertexes.setdefault(source_table_id, {source_table_id}).add(destination_table_id)
            vertexes.setdefault(destination_table_id, {destination_table_id}).add(source_table_id)

        graphs = []
        for dependencies in vertexes.values():
            if not graphs:
                graphs.append(dependencies)
                continue

            need_new_graph = True
            for graph in graphs:
                if graph.intersection(dependencies):
                    graph.update(dependencies)
                    need_new_graph = False
                    break

            if need_new_graph:
                graphs.append(dependencies)

        return graphs

    @staticmethod
    def get_graphs() -> list[set[int]]:
        with settings.STASH_FILE_PATH.open() as json_file:
            graphs = json.load(json_file)

        return [set(graph) for graph in graphs['relation_table_graphs']]

    @classmethod
    def get_graph(cls, relation_table_id: int) -> set[int]:
        for graph in cls.get_graphs():
            if relation_table_id in graph:
                return graph

        return set()
