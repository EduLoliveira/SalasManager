from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal


class UsuarioCustomizado(AbstractUser):
    telefone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('telefone'),
        help_text=_('Número de telefone para contato')
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name=_('data de criação'))
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name=_('data de atualização'))

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

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ['-data_criacao']
        db_table = 'sales_usuariocustomizado'

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    @property
    def is_complete_profile(self):
        return all([self.first_name, self.last_name, self.email])

    @property
    def telefone_formatado(self):
        if not self.telefone or len(self.telefone) < 10:
            return self.telefone
        telefone = ''.join(filter(str.isdigit, self.telefone))
        if len(telefone) == 10:
            return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
        elif len(telefone) == 11:
            return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
        return self.telefone


class Venda(models.Model):
    cliente = models.CharField(max_length=100, verbose_name="Nome do Cliente")
    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantidade"
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valor (R$)"
    )
    data_venda = models.DateField(verbose_name="Data da Venda")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendas"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    baixada = models.BooleanField(default=False)
    data_baixa = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-data_venda', '-data_criacao']

    def __str__(self):
        return f"Venda para {self.cliente} - R$ {self.valor}"

    def valor_total(self):
        return self.quantidade * self.valor
