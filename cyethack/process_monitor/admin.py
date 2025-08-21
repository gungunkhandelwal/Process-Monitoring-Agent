from django.contrib import admin
from .models import Host, ProcessSnapshot, Process, APIKey,SystemSnapshot

admin.site.register(Host)
admin.site.register(ProcessSnapshot)
admin.site.register(Process)
admin.site.register(APIKey)
admin.site.register(SystemSnapshot)