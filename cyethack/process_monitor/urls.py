from django.urls import path
from . import views

urlpatterns = [
 path('system/receive/', views.receive_system_data, name='receive_system_data'),
]