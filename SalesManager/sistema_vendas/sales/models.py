from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

class UsuarioCustomizado(AbstractUser):
    # Campos padrão do AbstractUser já incluem:
    # username, first_name, last_name, email, password, is_active, is_staff, is_superuser
    # date_joined, last_login, groups, user_permissions
    
    # Telefone - campo adicional
    telefone = models.CharField(
        max_length=15, 
        blank=True,
        verbose_name=_('telefone'),
        help_text=_('Número de telefone para contato')
    )
    
    # Campos de data e hora
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name=_('data de criação'))
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name=_('data de atualização'))
    
    # SOBRESCREVA os related_name para groups e user_permissions para evitar conflitos
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="usuario_customizado_set",
        related_query_name="usuario_customizado",
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="usuario_customizado_permissions_set",
        related_query_name="usuario_customizado_permissions",
    )
    
    # Configurações de autenticação
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ['-data_criacao']
        db_table = 'sales_usuariocustomizado'
    
    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_full_name(self):
        """
        Retorna o nome completo do usuário.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.username
    
    def get_short_name(self):
        """
        Retorna o primeiro nome do usuário.
        """
        return self.first_name or self.username
    
    def save(self, *args, **kwargs):
        # Garante que o email seja sempre salvo em minúsculas
        if self.email:
            self.email = self.email.lower()
        
        # Se a senha foi modificada e não está hasheada, faz o hash
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        
        super().save(*args, **kwargs)
    
    @property
    def is_complete_profile(self):
        """
        Verifica se o perfil do usuário está completo.
        """
        return all([self.first_name, self.last_name, self.email])
    
    @property
    def telefone_formatado(self):
        """
        Retorna o telefone formatado.
        """
        if not self.telefone or len(self.telefone) < 10:
            return self.telefone
        
        telefone = ''.join(filter(str.isdigit, self.telefone))
        
        if len(telefone) == 10:
            return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
        elif len(telefone) == 11:
            return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
        
        return self.telefone