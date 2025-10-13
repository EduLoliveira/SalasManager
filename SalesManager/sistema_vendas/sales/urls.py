from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # =========================================================================
    # URLs DE AUTENTICAÇÃO
    # =========================================================================
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # =========================================================================
    # URLs PRINCIPAIS (DASHBOARD E RELATÓRIOS)
    # =========================================================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('relatorio-vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    
    # =========================================================================
    # URLs DE VENDAS (STAFF REQUIRED)
    # =========================================================================
    path('vendas/cadastrar/', views.cadastrar_venda, name='cadastrar_venda'),
    path('vendas/lista/', views.lista_vendas, name='lista_vendas'),
    path('vendas/<int:venda_id>/baixar/', views.baixar_venda, name='baixar_venda'),
    path('vendas/exportar-csv/', views.exportar_vendas_csv, name='exportar_vendas_csv'),
    
    # =========================================================================
    # URLs DE PERFIL DO USUÁRIO
    # =========================================================================
    path('perfil/', views.user_profile, name='user_profile'),
    path('configuracoes/', views.user_settings, name='user_settings'),
    path('alterar-senha/', views.change_password, name='change_password'),
    
    # =========================================================================
    # URLs ADMINISTRATIVAS (ADMIN REQUIRED) - CORRIGIDAS
    # =========================================================================
    path('administracao/usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
   

    # =========================================================================
    # URLs DE CONFIGURAÇÕES STAFF
    # =========================================================================
    path('ativar-staff/', views.ativar_modo_staff, name='ativar_modo_staff'),
    path('desativar-staff/', views.desativar_modo_staff, name='desativar_modo_staff'),
    
    # =========================================================================
    # APIs E UTILITÁRIOS
    # =========================================================================
    path('check_venda_session/', views.check_venda_session, name='check_venda_session'),
    path('clear_venda_session/', views.clear_venda_session, name='clear_venda_session'),
    path('api/cliente-compras/', views.cliente_compras_api, name='cliente_compras_api'),
    path('api/exportar-relatorio-csv/', views.exportar_relatorio_csv, name='exportar_relatorio_csv'),
    path('api/enviar-relatorio-email/', views.enviar_relatorio_email, name='enviar_relatorio_email'),
]