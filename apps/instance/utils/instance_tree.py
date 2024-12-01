from abc import ABC, abstractmethod
from typing import Optional

from apps.instance.models import Store


PROJECT_MODEL = 'project'
RELATION_STORE_MODEL = 'relation_store'
RELATION_TABLE_MODEL = 'relation_table'
RELATION_TABLE_FIELD_MODEL = 'relation_table_field'


class InstanceType:

    def __init__(self, model: str, attrs: dict):
        self.model = model
        self.attrs = attrs

    def __str__(self):
        return f'{self.model}: {self.attrs}'


class InstanceError(Exception):
    pass


class Instance(ABC):

    @abstractmethod
    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        raise NotImplemented

    @abstractmethod
    def tree(self):
        raise NotImplemented


class ProjectInstance(Instance):

    def __init__(self):
        self._next_instance = StoresInstance()

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) == 1:
            if attrs:
                raise InstanceError('project instance: attrs must be empty or null')

            attrs['name'] = row[0]
            return InstanceType(model=PROJECT_MODEL, attrs=attrs)

        if row[1] == 'stores':
            return self._next_instance.parse(row=row, attrs=attrs)

        raise InstanceError('unexpected value at position 2')

    def tree(self):
        return {'<project_name>': self._next_instance.tree()}


class StoresInstance(Instance):

    def __init__(self):
        self._next_instance = RelationStoreTypeInstance()

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) > 2 and row[2] == 'relation':
            return self._next_instance.parse(row=row, attrs=attrs)

        raise InstanceError('unexpected value at position 3')

    def tree(self):
        return {'stores': self._next_instance.tree()}


class RelationStoreTypeInstance(Instance):

    def __init__(self):
        self._next_instance = RelationStoreInstance()

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) == 3:
            raise InstanceError('expected <store_name> at position 4')

        return self._next_instance.parse(row=row, attrs=attrs)

    def tree(self):
        return {'relation': self._next_instance.tree()}


class RelationStoreInstance(Instance):

    def __init__(self):
        self._next_instance = RelationTableInstance()

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) == 4:
            if attrs:
                raise InstanceError('relation_store instance: attrs must be empty or null')

            attrs['name'] = f'{row[0]}.{row[3]}'
            attrs['type'] = Store.RELATION_STORE
            return InstanceType(model=RELATION_STORE_MODEL, attrs=attrs)

        return self._next_instance.parse(row=row, attrs=attrs)

    def tree(self):
        return {'<store_name>': self._next_instance.tree()}


class RelationTableInstance(Instance):

    def __init__(self):
        self._next_instance = RelationTableFieldInstance()

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) == 5:
            attrs['name'] = f'{row[0]}.{row[3]}.{row[4]}'
            return InstanceType(model=RELATION_TABLE_MODEL, attrs=attrs)

        return self._next_instance.parse(row=row, attrs=attrs)

    def tree(self):
        return {'<relation_table_name>': self._next_instance.tree()}


class RelationTableFieldInstance(Instance):

    _available_attrs = (
        ('type', str, True, 'string'),
        ('field', str, False, 'string'),
        ('order', int, False, 'number'),
    )

    def parse(self, row: list[str], attrs: dict) -> InstanceType:
        if len(row) > 6:
            InstanceError('unexpected value at position 7')

        self._validate_attrs(attrs=attrs)
        attrs['name'] = f'{row[0]}.{row[3]}.{row[4]}.{row[5]}'
        return InstanceType(model=RELATION_TABLE_FIELD_MODEL, attrs=attrs)

    def _validate_attrs(self, attrs: dict):
        checked_attrs: int = 0
        for attr_name, attr_type, required, type_repr in self._available_attrs:
            attr = attrs.get(attr_name)
            if attr:
                if not isinstance(attr, attr_type):
                    raise InstanceError(f'relation_table_field instance: {attr_name} must be {type_repr} type')

                if attr_name == 'field' and len(attr.split('.')) != 4:
                    raise InstanceError(
                        f'relation_table_field instance: expected field format '
                        f'<project_name>.<store_name>.<table_name>.<field_name>',
                    )

                checked_attrs += 1

            if not attr and required:
                raise InstanceError('relation_table_field instance: available_attrs (type, field?, order?)')

        if checked_attrs < len(attrs):
            raise InstanceError('relation_table_field instance: available_attrs (type, field?, order?)')

    def tree(self):
        return {'<relation_table_field_name>': None}


class InstanceTree:

    def __init__(self):
        self._first_instance = ProjectInstance()

    def parse(self, row: str, attrs: Optional[dict] = None) -> InstanceType:
        if not row:
            raise InstanceError('value is empty')

        row = row.split('.')
        attrs = attrs or {}
        return self._first_instance.parse(row=row, attrs=attrs)

    def tree(self):
        return self._first_instance.tree()


instance_tree = InstanceTree()
