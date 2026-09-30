from django.urls import path

from . import views

urlpatterns = [
    path('imagens/adicionar/', views.upload_image, name='upload_image'),
    path('', views.listar_larps, name='listar_larps'),
    path('<slug:slug>/', views.detalhe_larp, name='detalhe_larp'),
    path('<slug:slug>/planilha/', views.planilha_larp, name='planilha_larp'),
    path('<slug:slug>/inscricao/<str:token>/', views.inscricao_larp, name='inscricao_larp'),
]
