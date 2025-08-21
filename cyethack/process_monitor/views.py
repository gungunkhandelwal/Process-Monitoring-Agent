from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Host, ProcessSnapshot, Process, SystemSnapshot
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class HostListView(APIView):
    # Returns all hosts with their latest process snapshot
    permission_classes = [AllowAny]
    
    def get(self, request):
        hosts = Host.objects.all()
        host_data = []
        for host in hosts:
            latest_snapshot = host.snapshots.first()
            host_info = {
                'id': host.id,
                'hostname': host.hostname,
                'ip_address': host.ip_address,
                'first_seen': host.created_at.isoformat(),
                'last_seen': host.last_seen.isoformat(),
                'latest_system_snapshot': None,
                'latest_process_snapshot': None
            }
            if latest_snapshot:
                processes = latest_snapshot.processes.all()
                process_data = []
                for proc in processes:
                    process_info = {
                        'id': proc.id,
                        'name': proc.name,
                        'pid': proc.pid,
                        'parent_pid': proc.parent_pid,
                        'cpu_percent': proc.cpu_percent,
                        'memory_mb': proc.memory_mb,
                        'status': proc.status,
                        'username': proc.username or '',
                        'command_line': proc.command_line or '',
                        'children': []
                    }
                    children = processes.filter(parent_pid=proc.pid)
                    for child in children:
                        process_info['children'].append({
                            'id': child.id,
                            'name': child.name,
                            'pid': child.pid,
                            'parent_pid': child.parent_pid,
                            'cpu_percent': child.cpu_percent,
                            'memory_mb': child.memory_mb,
                            'status': child.status,
                            'username': child.username or '',
                            'command_line': child.command_line or ''
                        })
                    process_data.append(process_info)
                host_info['latest_process_snapshot'] = {
                    'id': latest_snapshot.id,
                    'timestamp': latest_snapshot.timestamp.isoformat(),
                    'processes': process_data
                }
            host_data.append(host_info)
        return Response(host_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def host_system_info(request, host_id):
    # Returns system info for a specific host
    host = get_object_or_404(Host, id=host_id)
    latest_system = host.system_snapshots.first()
    if latest_system:
        system_info = {
            'id': host.id,
            'hostname': host.hostname,
            'timestamp': latest_system.timestamp.isoformat(),
            'operating_system': latest_system.operating_system,
            'processor': latest_system.processor,
            'processor_cores': latest_system.processor_cores,
            'processor_threads': latest_system.processor_threads,
            'ram_total_gb': latest_system.ram_total_gb,
            'ram_used_gb': latest_system.ram_used_gb,
            'ram_available_gb': latest_system.ram_available_gb,
            'storage_total_gb': latest_system.storage_total_gb,
            'storage_used_gb': latest_system.storage_used_gb,
            'storage_free_gb': latest_system.storage_free_gb
        }
    else:
        system_info = {
            'id': host.id,
            'hostname': host.hostname,
            'timestamp': host.last_seen.isoformat(),
            'operating_system': 'Unknown',
            'processor': 'Unknown',
            'processor_cores': 'Unknown',
            'processor_threads': 'Unknown',
            'ram_total_gb': 'Unknown',
            'ram_used_gb': 'Unknown',
            'ram_available_gb': 'Unknown',
            'storage_total_gb': 'Unknown',
            'storage_used_gb': 'Unknown',
            'storage_free_gb': 'Unknown'
        }
    return Response(system_info)

@api_view(['GET'])
@permission_classes([AllowAny])
def host_processes_latest(request, host_id):
    # Returns process snapshot for a specific host
    host = get_object_or_404(Host, id=host_id)
    latest_snapshot = host.snapshots.first()
    if not latest_snapshot:
        return Response({'error': 'No process data found'}, status=status.HTTP_404_NOT_FOUND)
    processes = latest_snapshot.processes.all()
    process_data = []
    for proc in processes:
        process_info = {
            'id': proc.id,
            'name': proc.name,
            'pid': proc.pid,
            'parent_pid': proc.parent_pid,
            'cpu_percent': proc.cpu_percent,
            'memory_mb': proc.memory_mb,
            'status': proc.status,
            'username': proc.username or '',
            'command_line': proc.command_line or '',
            'created_time': proc.created_time.isoformat() if proc.created_time else None,
            'children': []
        }
        children = processes.filter(parent_pid=proc.pid)
        for child in children:
            process_info['children'].append({
                'id': child.id,
                'name': child.name,
                'pid': child.pid,
                'parent_pid': child.parent_pid,
                'cpu_percent': child.cpu_percent,
                'memory_mb': child.memory_mb,
                'status': child.status,
                'username': child.username or '',
                'command_line': child.command_line or '',
                'created_time': child.created_time.isoformat() if child.created_time else None
            })
        process_data.append(process_info)
    response_data = {
        'id': latest_snapshot.id,
        'timestamp': latest_snapshot.timestamp.isoformat(),
        'processes': process_data
    }
    return Response(response_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def host_processes_by_name(request, hostname):
    # Returns process snapshot for a host by hostname
    host = get_object_or_404(Host, hostname=hostname)
    return host_processes_latest(request, host.id)

@api_view(['GET'])
@permission_classes([AllowAny])
def host_system_by_name(request, hostname):
    # Returns system info for a host by hostname
    host = get_object_or_404(Host, hostname=hostname)
    return host_system_info(request, host.id)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_process_data(request):
    # Receives and saves process and system data from agent
    data = request.data
    with transaction.atomic():
        host, _ = Host.objects.get_or_create(
            hostname=data.get('hostname', 'Unknown')
        )
        host.last_seen = timezone.now()
        host.save()
        if 'system_info' in data:
            system_info = data['system_info']
            SystemSnapshot.objects.create(
                host=host,
                timestamp=data.get('timestamp', timezone.now()),
                operating_system=system_info.get('operating_system', 'Unknown'),
                processor=system_info.get('processor', 'Unknown'),
                processor_cores=system_info.get('processor_cores', 0),
                processor_threads=system_info.get('processor_threads', 0),
                ram_total_gb=system_info.get('ram_total_gb', 0.0),
                ram_used_gb=system_info.get('ram_used_gb', 0.0),
                ram_available_gb=system_info.get('ram_available_gb', 0.0),
                storage_total_gb=system_info.get('storage_total_gb', 0.0),
                storage_used_gb=system_info.get('storage_used_gb', 0.0),
                storage_free_gb=system_info.get('storage_free_gb', 0.0)
            )
        snapshot = ProcessSnapshot.objects.create(
            host=host,
            timestamp=data.get('timestamp', timezone.now())
        )
        processes_data = data.get('processes', [])
        for proc_data in processes_data:
            Process.objects.create(
                info=snapshot,
                pid=proc_data.get('pid', 0),
                name=proc_data.get('name', 'Unknown'),
                parent_pid=proc_data.get('parent_pid'),
                cpu_percent=proc_data.get('cpu_percent', 0.0),
                memory_percent=proc_data.get('memory_percent', 0.0),
                memory_mb=proc_data.get('memory_mb', 0.0),
                status=proc_data.get('status', 'running'),
                username=proc_data.get('username'),
                command_line=proc_data.get('command_line', ''),
                created_time=proc_data.get('created_time')
            )
    return Response({
        'message': 'Process data received successfully',
        'hostname': host.hostname,
        'processes_count': len(processes_data)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    # Returns overall system status and counts
    total_hosts = Host.objects.count()
    total_snapshots = ProcessSnapshot.objects.count()
    total_processes = Process.objects.count()
    return Response({
        'total_hosts': total_hosts,
        'total_snapshots': total_snapshots,
        'total_processes': total_processes,
        'status': 'healthy'
    })