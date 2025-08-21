from django.contrib import admin
from . models import Host, SystemInfo, ProcessInfo, Process

admin.site.register(Host)
admin.site.register(SystemInfo)
admin.site.register(ProcessInfo)
admin.site.register(Process)
