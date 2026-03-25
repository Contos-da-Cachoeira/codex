from django.urls import path

from . import views

urlpatterns = [
    path('', views.meus_personagens, name='meus_personagens'),
    path('novo/', views.criar_personagem, name='criar_personagem'),
    path('<slug:slug>/', views.detalhe_personagem, name='detalhe_personagem'),
    path('<slug:slug>/editar/', views.editar_personagem, name='editar_personagem'),
]
