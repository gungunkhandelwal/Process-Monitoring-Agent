from django.db import models
from django.utils import timezone

class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.hostname

class SystemSnapshot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='system_snapshots')
    timestamp = models.DateTimeField(default=timezone.now)
    operating_system = models.CharField(max_length=255)
    processor = models.CharField(max_length=255)
    processor_cores = models.IntegerField()
    processor_threads = models.IntegerField()
    ram_total_gb = models.FloatField()
    ram_used_gb = models.FloatField()
    ram_available_gb = models.FloatField()
    storage_total_gb = models.FloatField()
    storage_used_gb = models.FloatField()
    storage_free_gb = models.FloatField()
    
    class Meta:
        # db_table = 'system_snapshots'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.host.hostname} - {self.timestamp}"

class ProcessSnapshot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='snapshots')
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.host.hostname} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']

class Process(models.Model):
    info = models.ForeignKey(ProcessSnapshot, on_delete=models.CASCADE, related_name='processes')
    name = models.CharField(max_length=255)
    pid = models.IntegerField()
    parent_pid = models.IntegerField(null=True, blank=True)
    cpu_percent = models.FloatField(default=0.0)
    memory_percent = models.FloatField(default=0.0)
    memory_mb = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default='running')
    username = models.CharField(max_length=255, null=True, blank=True)
    command_line = models.TextField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} (PID - {self.pid})"
    
    class Meta:
        indexes = [
            models.Index(fields=['pid']),
            models.Index(fields=['parent_pid']),
            models.Index(fields=['info']),
        ]
    
    @property
    def children(self):
        return self.info.processes.filter(parent_pid=self.pid)
    
    @property
    def parent(self):
        if self.parent_pid:
            return self.info.processes.filter(pid=self.parent_pid).first()
        return None

class APIKey(models.Model):
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."
    