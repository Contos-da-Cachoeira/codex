from django.urls import path

from . import views

urlpatterns = [
    path('', views.listar_guildas, name='listar_guildas'),
    path('<slug:slug>/', views.detalhe_guilda, name='detalhe_guilda'),
]
