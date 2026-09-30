from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('area-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('area-admin/home/previa/', views.home_preview, name='home_preview'),
    path('area-admin/usuarios/<int:user_id>/', views.admin_user_profile, name='admin_user_profile'),
    path('area-usuario/', views.user_dashboard, name='user_dashboard'),
]
