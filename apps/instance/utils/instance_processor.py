from copy import copy
from typing import Optional

from apps.instance.models import Project, Store, RelationTable, RelationTableField
from apps.instance.utils.instance_tree import (
    instance_tree,
    PROJECT_MODEL,
    RELATION_STORE_MODEL,
    RELATION_TABLE_MODEL,
    RELATION_TABLE_FIELD_MODEL,
    InstanceType,
)


_CREATE_OPERATION = 1
_DELETE_OPERATION = 2


class Operation:

    def __init__(self, order: int, op_code: int, instance_type: InstanceType):
        self.order = order
        self.op_code = op_code
        self.model = instance_type.model
        self.attrs = instance_type.attrs

    def __str__(self):
        return f'{self.order}:{self.op_code}:{self.model}:{self.attrs}'


class OperationError(Exception):

    def __init__(self, operation: Operation, message: str):
        self.message = (
            f'operation_order: {operation.order}, model: {operation.model}, message: {message}'
        )
        super().__init__(self.message)


class InstanceProcessor:

    def process(self, operations: list[list[int, str, Optional[None | dict]]], stages: Optional[int] = 3):
        parsed_operations = self.parse(operations=operations)
        self.check_operations(operations=parsed_operations)
        self.execute(operations=parsed_operations)

    @staticmethod
    def parse(operations: list[list[int, str, Optional[None | dict]]]) -> list[Operation]:
        parsed_operations: list[Operation] = []
        for order, op in enumerate(operations, start=1):
            if len(op) < 2 or len(op) > 3:
                raise

            if op[0] != _CREATE_OPERATION and op[0] != _DELETE_OPERATION:
                raise

            attrs = op[2] if len(op) == 3 else None
            operation = Operation(
                order=order,
                op_code=op[0],
                instance_type=instance_tree.parse(row=op[1], attrs=attrs),
            )
            parsed_operations.append(operation)

        return parsed_operations

    @property
    def exist_project_names(self):
        if not hasattr(self, '_exist_project_names'):
            self._exist_project_names = set(Project.objects.values_list('name', flat=True))

        return self._exist_project_names

    @property
    def exist_store_names(self):
        if not hasattr(self, '_exist_store_names'):
            queryset = Store.objects.values('name', 'project__name')
            self._exist_store_names = {f'{store["project__name"]}.{store["name"]}' for store in queryset}

        return self._exist_store_names

    @property
    def exist_relation_table_names(self):
        if not hasattr(self, '_exist_relation_table_names'):
            queryset = RelationTable.objects.values('name', 'store__name', 'store__project__name')
            self._exist_relation_table_names = {
                f'{table["store__project__name"]}.{table["store__name"]}.{table["name"]}'
                for table in queryset
            }

        return self._exist_relation_table_names

    @property
    def exist_relation_table_field_names(self):
        if not hasattr(self, '_exist_relation_table_field_names'):
            queryset = RelationTableField.objects.values(
                'name',
                'relation_table__name',
                'relation_table__store__name',
                'relation_table__store__project__name',
            )
            self._exist_relation_table_field_names = {
                (
                    f'{field["relation_table__store__project__name"]}.{field["relation_table__store__name"]}.'
                    f'{field["relation_table__name"]}.{field["name"]}'
                )
                for field in queryset
            }

        return self._exist_relation_table_field_names

    def _delete_project_name(self, project_name: str):
        for store_name in copy(self.exist_store_names):
            if store_name.startswith(project_name):
                self._delete_store_name(store_name=store_name)

        self.exist_project_names.remove(project_name)

    def _delete_store_name(self, store_name: str):
        for relation_table_name in copy(self.exist_relation_table_names):
            if relation_table_name.startswith(store_name):
                self._delete_relation_table_name(relation_table_name=relation_table_name)

        self.exist_store_names.remove(store_name)

    def _delete_relation_table_name(self, relation_table_name: str):
        for relation_table_field_name in copy(self.exist_relation_table_field_names):
            if relation_table_field_name.startswith(relation_table_name):
                self._delete_relation_table_field_name(relation_table_field_name=relation_table_field_name)

        self.exist_relation_table_names.remove(relation_table_name)

    def _delete_relation_table_field_name(self, relation_table_field_name: str):
        self.exist_relation_table_field_names.remove(relation_table_field_name)

    def _check_project_operation(self, operation: Operation):
        project_name = operation.attrs['name']
        if operation.op_code == _CREATE_OPERATION:
            if project_name in self.exist_project_names:
                raise OperationError(
                    operation=operation,
                    message=f'project with name {project_name} already exists',
                )

            self.exist_project_names.add(project_name)
        else:
            if project_name not in self.exist_project_names:
                raise OperationError(operation=operation, message=f'project with name {project_name} not exists')

            self._delete_project_name(project_name=project_name)

    def _check_relation_store_operation(self, operation: Operation) -> None:
        store_name = operation.attrs['name']
        project_name = store_name.split('.')[0]
        if project_name not in self.exist_project_names:
            raise OperationError(operation=operation, message=f'project with name {project_name} not exists')

        if operation.op_code == _CREATE_OPERATION:
            if store_name in self.exist_store_names:
                raise OperationError(operation=operation, message=f'store with name {store_name} already exists')

            self.exist_store_names.add(store_name)
        else:
            if store_name not in self.exist_store_names:
                raise OperationError(operation=operation, message=f'store with name {store_name} not exists')

            self._delete_store_name(store_name=store_name)

    def _check_relation_table_operation(self, operation: Operation) -> None:
        relation_table_name = operation.attrs['name']
        parts = relation_table_name.split('.')
        project_name, store_name = parts[0], f'{parts[0]}.{parts[1]}'
        if store_name not in self.exist_store_names:
            raise OperationError(operation=operation, message=f'store with name {store_name} not exists')

        if project_name not in self.exist_project_names:
            raise OperationError(operation=operation, message=f'project with name {project_name} not exists')

        if operation.op_code == _CREATE_OPERATION:
            if relation_table_name in self.exist_relation_table_names:
                raise OperationError(
                    operation=operation,
                    message=f'relation_table with name {relation_table_name} already exists',
                )

            self.exist_relation_table_names.add(relation_table_name)
        else:
            if relation_table_name not in self.exist_relation_table_names:
                raise OperationError(
                    operation=operation,
                    message=f'relation_table with name {relation_table_name} not exists',
                )

            self._delete_relation_table_name(relation_table_name=relation_table_name)

    def _check_relation_table_field_operation(self, operation: Operation) -> None:
        relation_table_field_name = operation.attrs['name']
        parts = relation_table_field_name.split('.')
        project_name, store_name, relation_table_name = (
            parts[0],
            f'{parts[0]}.{parts[1]}',
            f'{parts[0]}.{parts[1]}.{parts[2]}',
        )
        if relation_table_name not in self.exist_relation_table_names:
            raise OperationError(
                operation=operation,
                message=f'relation_table with name {relation_table_name} not exists',
            )

        if store_name not in self.exist_store_names:
            raise OperationError(operation=operation, message=f'store with name {store_name} not exists')

        if project_name not in self.exist_project_names:
            raise OperationError(operation=operation, message=f'project with name {project_name} not exists')

        if operation.op_code == _CREATE_OPERATION:
            if relation_table_field_name in self.exist_relation_table_field_names:
                raise OperationError(
                    operation=operation,
                    message=f'relation_table_field with name {relation_table_field_name} already exists',
                )

            self.exist_relation_table_field_names.add(relation_table_field_name)
        else:
            self._delete_relation_table_field_name(relation_table_field_name=relation_table_field_name)

    def check_operations(self, operations: list[Operation]) -> None:
        for operation in operations:
            if operation.model == PROJECT_MODEL:
                self._check_project_operation(operation=operation)
            elif operation.model == RELATION_STORE_MODEL:
                self._check_relation_store_operation(operation=operation)
            elif operation.model == RELATION_TABLE_MODEL:
                self._check_relation_table_operation(operation=operation)
            elif operation.model == RELATION_TABLE_FIELD_MODEL:
                self._check_relation_table_field_operation(operation=operation)

        for operation in operations:
            if operation.model == RELATION_TABLE_FIELD_MODEL and operation.attrs.get('field'):
                field = operation.attrs['field']
                if field not in self.exist_relation_table_field_names:
                    raise OperationError(
                        operation=operation,
                        message=f'field with name {operation.attrs["field"]} not exists',
                    )

    @staticmethod
    def _execute_project(operation: Operation) -> None:
        if operation.op_code == _CREATE_OPERATION:
            Project.objects.create(**operation.attrs)
        else:
            Project.objects.filter(name=operation.attrs['name']).delete()

    @staticmethod
    def _execute_relation_store(operation: Operation) -> None:
        project_name, store_name = operation.attrs['name'].split('.')
        operation.attrs['name'] = store_name
        if operation.op_code == _CREATE_OPERATION:
            operation.attrs['project_id'] = Project.objects.get(name=project_name).id
            Store.objects.create(**operation.attrs)
        else:
            Store.objects.filter(name=store_name, project__name=project_name).delete()

    @staticmethod
    def _execute_relation_table(operation: Operation) -> None:
        project_name, store_name, relation_table_name = operation.attrs['name'].split('.')
        operation.attrs['name'] = relation_table_name
        if operation.op_code == _CREATE_OPERATION:
            operation.attrs['store_id'] = Store.objects.get(
                name=store_name,
                project__name=project_name,
                type=Store.RELATION_STORE,
            ).id
            RelationTable.objects.create(**operation.attrs)
        else:
            RelationTable.objects.filter(
                name=relation_table_name,
                store__name=store_name,
                store__project__name=project_name,
            ).delete()

    @staticmethod
    def _execute_relation_table_field(operation: Operation) -> None:
        project_name, store_name, relation_table_name, relation_table_field_name = operation.attrs['name'].split('.')
        operation.attrs['name'] = relation_table_field_name
        if operation.op_code == _CREATE_OPERATION:
            operation.attrs['relation_table_id'] = RelationTable.objects.get(
                name=relation_table_name,
                store__name=store_name,
                store__project__name=project_name,
            ).id
            fk_field = operation.attrs.pop('field') if operation.attrs.get('field') else None
            if fk_field is not None:
                fk_project_name, fk_store_name, fk_relation_table_name, fk_relation_table_field_name = fk_field.split(
                    '.',
                )
                operation.attrs['field_id'] = RelationTableField.objects.get(
                    name=fk_relation_table_field_name,
                    relation_table__name=fk_relation_table_name,
                    relation_table__store__name=fk_store_name,
                    relation_table__store__project__name=fk_project_name,
                ).id

            RelationTableField.objects.create(**operation.attrs)
        else:
            RelationTableField.objects.filter(
                relation_table__name=relation_table_name,
                relation_table__store__name=store_name,
                relation_table__store__project__name=project_name,
            ).delete()

    def execute(self, operations: list[Operation]):
        for operation in operations:
            if operation.model == PROJECT_MODEL:
                self._execute_project(operation=operation)
            elif operation.model == RELATION_STORE_MODEL:
                self._execute_relation_store(operation=operation)
            elif operation.model == RELATION_TABLE_MODEL:
                self._execute_relation_table(operation=operation)
            elif operation.model == RELATION_TABLE_FIELD_MODEL:
                self._execute_relation_table_field(operation=operation)
