from rest_framework import serializers
from .models import Host, ProcessSnapshot, Process

class ProcessSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Process
        fields = [
            'id', 'pid', 'name', 'parent_pid', 'cpu_percent', 
            'memory_percent', 'memory_mb', 'status', 'username', 
            'command_line', 'created_time', 'children'
        ]
    
    def get_children(self, obj):
        children = Process.objects.filter(
            snapshot=obj.snapshot,
            parent_pid=obj.pid
        ).order_by('name')
        return ProcessSerializer(children, many=True).data

class ProcessSnapshotSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source='host.hostname', read_only=True)
    process_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessSnapshot
        fields = ['id', 'host_name', 'timestamp', 'process_count']
    
    def get_process_count(self, obj):
        return obj.processes.count()

class HostSerializer(serializers.ModelSerializer):
    latest_snapshot = serializers.SerializerMethodField()
    
    class Meta:
        model = Host
        fields = ['id', 'hostname', 'ip_address', 'last_seen', 'latest_snapshot']
    
    def get_latest_snapshot(self, obj):
        latest = obj.snapshots.first()
        if latest:
            return ProcessSnapshotSerializer(latest).data
        return None

class ProcessDataSubmissionSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField()
    processes = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_processes(self, value):
        required_fields = ['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_mb']
        
        for process in value:
            for field in required_fields:
                if field not in process:
                    raise serializers.ValidationError(
                        f"Missing required field : '{field}' in process data"
                    )
        return value