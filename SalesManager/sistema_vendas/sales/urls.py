from django.urls import path
from . import views

app_name = 'sales'  

urlpatterns = [
    # Página de login (página inicial)
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]