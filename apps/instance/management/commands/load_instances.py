from pathlib import Path
import json

from django.conf import settings
from django.core.management import BaseCommand

from apps.instance.utils.instance_processor import InstanceProcessor


class Command(BaseCommand):

    def handle(self, *args, **options):
        with Path(settings.BASE_DIR, 'operations.json').open() as json_file:
            data = json.load(json_file)

        processor = InstanceProcessor()
        processor.process(operations=data['operations'])
