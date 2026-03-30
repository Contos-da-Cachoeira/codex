from django.urls import path

from . import views

urlpatterns = [
    path('', views.wiki_home, name='wiki_home'),
    path('regras/', views.regras_lista, name='wiki_regras_lista'),
    path('regras/<slug:slug>/', views.regra_detalhe, name='wiki_regra_detalhe'),
    path('classes/', views.classes_lista, name='wiki_classes_lista'),
    path('classes/<slug:slug>/', views.classe_detalhe, name='wiki_classe_detalhe'),
    path('magias/', views.magias_lista, name='wiki_magias_lista'),
    path('magias/<slug:slug>/', views.magia_detalhe, name='wiki_magia_detalhe'),
    path('itens/', views.itens_lista, name='wiki_itens_lista'),
    path('itens/<slug:slug>/', views.item_detalhe, name='wiki_item_detalhe'),
    path('talentos/', views.talentos_lista, name='wiki_talentos_lista'),
    path('talentos/<slug:slug>/', views.talento_detalhe, name='wiki_talento_detalhe'),
]
