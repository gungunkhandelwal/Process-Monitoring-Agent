from rest_framework import status
from .models import Host, SystemInfo, ProcessInfo, Process
from rest_framework.response import Response
from rest_framework.decorators import api_view ,permission_classes
from django.utils import timezone
from .serializer import HostSerializer, SystemInfoSerializer, ProcessInfoSerializer, ProcessSerializer
from django.conf import settings
from rest_framework.permissions import AllowAny,IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class APIKeyAuthentication:
    def authenticate(self, request):
        api_key=request.headers.get('X-API-KEY')
        if api_key == settings.AGENT_API_KEY:
            return (None, None)
        return None
    
@api_view(['POST'])
@permission_classes([AllowAny])
def receive_system_data(request):
    try:
        auth = APIKeyAuthentication()
        user, auth = auth.authenticate(request)
        if not user and not auth:
            return Response(
                {'error': 'Invalid API key'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = SystemInfoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        with transaction.atomic():
            # Get or create host
            host, created = Host.objects.get_or_create(
                hostname=data['hostname']
            )
            host.last_seen = timezone.now()
            host.save()
            
            # Create system snapshot
            SystemSnapshot.objects.create(
                host=host,
                timestamp=data['timestamp'],
                operating_system=data['operating_system'],
                processor=data['processor'],
                processor_cores=data['processor_cores'],
                processor_threads=data['processor_threads'],
                ram_total_gb=data['ram_total_gb'],
                ram_used_gb=data['ram_used_gb'],
                ram_available_gb=data['ram_available_gb'],
                storage_total_gb=data['storage_total_gb'],
                storage_used_gb=data['storage_used_gb'],
                storage_free_gb=data['storage_free_gb']
            )
        
        return Response({
            'message': 'System data received successfully',
            'hostname': host.hostname
        })
    except Exception as e:
        logger.error(f"Error receiving system data: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

