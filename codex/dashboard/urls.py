from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('area-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('area-admin/larps/<int:evento_id>/editar/', views.edit_larp_event, name='edit_larp_event'),
    path('area-usuario/', views.user_dashboard, name='user_dashboard'),
]
