from rest_framework import serializers
from . models import Host, SystemInfo, ProcessInfo, Process

class ProcessSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Process
        fields = ['id','name','parent_pid','parent_name','pid', 'cpu_percent', 'memory_mb', 'status', 'command_line', 'children']

    def get_children(self, obj):
        children = obj.children
        return ProcessSerializer(obj.children, many=True).data
    
    def get_parent_name(self, obj):
        parent = obj.parent
        return parent.name if parent else None
    
class ProcessInfoSerializer(serializers.ModelSerializer):
    processes = serializers.SerializerMethodField()

    class Meta:
        model = ProcessInfo
        fields = ['id','timestamp','processes']
    
    def get_processes(self, obj):
        root_processes = obj.processes.filter(
            models.Q(parent_pid__isnull=True) | 
            ~models.Q(parent_pid__in=obj.processes.values_list('pid', flat=True))
        )
        return ProcessSerializer(root_processes, many=True).data

class SystemInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemInfo
        fields = [
            'id', 'timestamp', 'operating_system', 'processor', 
            'processor_cores', 'processor_threads', 'ram_total_gb', 
            'ram_used_gb', 'ram_available_gb', 'storage_total_gb', 
            'storage_used_gb', 'storage_free_gb'
        ]
class HostSerializer(serializers.ModelSerializer):
    latest_system_snapshot = serializers.SerializerMethodField()
    latest_process_snapshot = serializers.SerializerMethodField()
    
    class Meta:
        model = Host
        fields = [
            'id', 'hostname', 'ip_address', 'first_seen', 'last_seen', 
            'latest_system_snapshot', 'latest_process_snapshot'
        ]
    
    def get_latest_system_snapshot(self, obj):
        latest = obj.system_snapshots.first()
        if latest:
            return SystemSnapshotSerializer(latest).data
        return None
    
    def get_latest_process_snapshot(self, obj):
        latest = obj.process_snapshots.first()
        if latest:
            return ProcessSnapshotSerializer(latest).data
        return None



        