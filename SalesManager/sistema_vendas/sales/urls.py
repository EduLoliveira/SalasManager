from django.urls import path
from . import views

app_name = 'sales'  

urlpatterns = [
    # Autenticação
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    #CheckVenda
    path('check_venda_session/', views.check_venda_session, name='check_venda_session'),
    path('clear_venda_session/', views.clear_venda_session, name='clear_venda_session'),

    # Vendas
    path('cadastrar-venda/', views.cadastrar_venda, name='cadastrar_venda'),
    path('listagem-venda/', views.lista_vendas, name='lista_vendas'),
    path('baixar-venda/<int:venda_id>/', views.baixar_venda, name='baixar_venda'),
    path('exportar-vendas/', views.exportar_vendas_csv, name='exportar_vendas'),
]
