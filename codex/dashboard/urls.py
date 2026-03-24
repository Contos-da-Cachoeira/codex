from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('area-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('area-usuario/', views.user_dashboard, name='user_dashboard'),
]
