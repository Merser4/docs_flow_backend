from pathlib import Path

from django.conf import settings
from django.db import models


class Project(models.Model):

    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Store(models.Model):

    RELATION_STORE = 'relation'

    TYPES = (
        (RELATION_STORE, RELATION_STORE),
    )

    name = models.CharField(max_length=128)
    type = models.CharField(max_length=32, choices=TYPES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'project'], name='store_unique_name_project'),
        ]

    def __str__(self):
        return self.name


class RelationTable(models.Model):

    name = models.CharField(max_length=128)
    snapshot = models.FilePathField(
        path=str(Path(settings.MEDIA_ROOT, 'snapshots', 'relation_table')),
        blank=True,
        null=True,
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'store'], name='relation_table_unique_name_store'),
        ]

    def __str__(self):
        return self.name


class RelationTableField(models.Model):

    name = models.CharField(max_length=128)
    type = models.CharField(max_length=128)
    field = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, default=0)
    relation_table = models.ForeignKey(RelationTable, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'relation_table'],
                name='relation_table_field_unique_name_relation_table',
            ),
        ]

    def __str__(self):
        return self.name
