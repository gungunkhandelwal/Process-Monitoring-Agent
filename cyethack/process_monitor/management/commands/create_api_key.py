from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from process_monitor.models import APIKey
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a new API key for agent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Default Agent',
            help='Name for the API key'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=32,
            help='Length of the API key (default: 32)'
        )

    def handle(self, *args, **options):
        name = options['name']
        length = options['length']
        api_key = get_random_string(length)
        
        key_obj = APIKey.objects.create(
            key=api_key,
            name=name,
            is_active=True
        )
        
        logger.info(f'Successfully created API key "{name}"')
