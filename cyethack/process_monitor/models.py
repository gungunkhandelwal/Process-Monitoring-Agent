from django.db import models
from djando.utils import timezone

class Host(models.Model):
    hostname = models.CharField(max_length=255 , unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.hostname

class SystemInfo(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE,related_name='system_info')
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
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.host.hostname} - {self.timestamp}"

class ProcessInfo(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE,related_name='processes_info')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.host.hostname} - {self.timestamp}"

class Process(models.Model):
    info=models.ForeignKey(ProcessInfo, on_delete=models.CASCADE,related_name='processes')
    name = models.CharField(max_length=255)
    pid = models.IntegerField()
    parent_pid = models.IntegerField(null=True, blank=True)
    cpu_percent = models.FloatField(default=0.0)
    memory_mb = models.FloatField(default=0.0)
    status = models.CharField(max_length=50 , default='running')
    command_line = models.TextField(blank=True)

    class Meta:
        ordering = ['pid']
    
    def __str__(self):
        return f"{self.name} (PID - {self.pid})"
    
    @property
    def children(self):
        return self.info.processes.filter(parent_pid=self.pid)
    
    @property
    def parent(self):
        if self.parent_pid:
            return self.info.processes.filter(pid=self.parent_pid).first()
        return None
    
