from django.urls import path

from . import views

urlpatterns = [
    path('', views.listar_larps, name='listar_larps'),
    path('<slug:slug>/', views.detalhe_larp, name='detalhe_larp'),
    path('<slug:slug>/personagens/', views.personagens_larp, name='personagens_larp'),
    path('<slug:slug>/inscricao/<str:token>/', views.inscricao_larp, name='inscricao_larp'),
]
