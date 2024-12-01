from django.apps import apps
from django.db import connection
from django.db.models import Model, Field
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
from django.db.models.fields.reverse_related import ForeignObjectRel, OneToOneRel, ManyToOneRel, ManyToManyRel


def parse_django_models(project_name: str, store_name: str) -> list:
    store_row = f'{project_name}.stores.relation.{store_name}'
    operations = [
        [1, project_name],
        [1, store_row],
    ]
    parsed_models: set[str] = set()
    m2m_model_names = set()
    m2m_models = []

    def _parse_model(django_model: Model, is_m2m_model: bool = False):
        if django_model.__name__ in parsed_models:
            return

        for field in django_model._meta.get_fields():
            field: Field
            if (
                isinstance(field, (ForeignKey, OneToOneField))
                and django_model != field.related_model
                and field.related_model.__name__ not in parsed_models
                and not is_m2m_model
            ):
                _parse_model(django_model=field.related_model)

        operations.append([1, f'{store_row}.{django_model.__name__}'])
        for field in django_model._meta.get_fields():
            field: Field
            if isinstance(field, (ForeignObjectRel, OneToOneRel, ManyToOneRel, ManyToManyRel)):
                continue
            elif isinstance(field, (ForeignKey, OneToOneField)):
                related_field_row = (
                    f'{project_name}.{store_name}.{field.related_model.__name__}.{field.target_field.attname}'
                )
                operations.append(
                    [
                        1,
                        f'{store_row}.{django_model.__name__}.{field.attname}',
                        {'type': field.db_type(connection), 'field': related_field_row},
                    ]
                )
            elif isinstance(field, ManyToManyField) and not is_m2m_model:
                through_model = field.remote_field.through
                if through_model.__name__ not in m2m_model_names:
                    m2m_model_names.add(through_model.__name__)
                    m2m_models.append(through_model)
            else:
                operations.append(
                    [1, f'{store_row}.{django_model.__name__}.{field.attname}', {'type': field.db_type(connection)}]
                )

        parsed_models.add(django_model.__name__)

    for model in apps.get_models():
        _parse_model(django_model=model)

    for m2m_model in m2m_models:
        _parse_model(django_model=m2m_model, is_m2m_model=True)

    return operations
