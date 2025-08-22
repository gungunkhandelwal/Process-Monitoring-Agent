from django.urls import path
from . import views

urlpatterns = [
    path('hosts/', views.HostListView.as_view(), name='host_list'),
    path('hosts/<int:host_id>/system/latest/', views.host_system_info, name='host_system_info'),
    path('hosts/<int:host_id>/processes/latest/', views.host_processes_latest, name='host_processes_latest'),
    path('hosts/<str:hostname>/processes/', views.host_processes_by_name, name='host_processes_by_name'),
    path('hosts/<str:hostname>/system/', views.host_system_by_name, name='host_system_by_name'),
    path('status/', views.system_status, name='system_status'),
    path('submit/', views.submit_process_data, name='submit_process_data'),
]