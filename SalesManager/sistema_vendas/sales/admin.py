from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioCustomizado

class UsuarioCustomizadoAdmin(UserAdmin):
    model = UsuarioCustomizado
    
    # Campos a serem exibidos na listagem
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    
    # Campos para edição
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email', 'telefone')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'data_criacao', 'data_atualizacao')}),
    )
    
    # Campos para criação de usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

# Registrar o modelo personalizado
admin.site.register(UsuarioCustomizado, UsuarioCustomizadoAdmin)