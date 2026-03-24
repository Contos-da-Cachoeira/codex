from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='register'),
    path('area-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('area-usuario/', views.user_dashboard, name='user_dashboard'),
    path('minha-conta/', views.account_personal_data, name='account_personal_data'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
