from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UsuarioCustomizado, Venda
from django.core.validators import MinValueValidator
from decimal import Decimal
import datetime


class FormularioLogin(AuthenticationForm):
    username = forms.CharField(
        label='Username ou Email',
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Seu username',
            'id': 'id_username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Sua senha',
            'id': 'id_password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        label='Lembrar-me',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_remember_me'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = _(
            "Por favor, insira um username e senha corretos. "
            "Note que ambos os campos diferenciam maiúsculas e minúsculas."
        )

class FormularioRegistro(UserCreationForm):
    username = forms.CharField(
        required=True,
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Escolha um username único',
            'autocomplete': 'username'
        }),
        help_text="Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas."
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'seu@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        required=True,
        label='Nome',
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Seu nome'
        })
    )
    last_name = forms.CharField(
        required=True,
        label='Sobrenome',
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Seu sobrenome'
        })
    )
    telefone = forms.CharField(
        required=True,
        label='Telefone',
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': '(00) 00000-0000'
        })
    )
    
    # REMOVA as redefinições de password1 e password2 para usar as do UserCreationForm
    # O UserCreationForm já fornece esses campos com validações adequadas
    
    class Meta:
        model = UsuarioCustomizado
        fields = ('username', 'email', 'first_name', 'last_name', 'telefone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalize os campos de senha do UserCreationForm
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control with-icon',
            'placeholder': 'Digite sua senha',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control with-icon',
            'placeholder': 'Digite a mesma senha novamente',
            'autocomplete': 'new-password'
        })
        
        # Personalize outros campos
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if email:
            # Verifica se já existe um usuário com este email (excluindo o próprio usuário em caso de edição)
            if self.instance and self.instance.pk:
                if UsuarioCustomizado.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise ValidationError(_("Este email já está cadastrado."))
            else:
                if UsuarioCustomizado.objects.filter(email=email).exists():
                    raise ValidationError(_("Este email já está cadastrado."))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:
            # Verifica se já existe um usuário com este username
            if self.instance and self.instance.pk:
                if UsuarioCustomizado.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                    raise ValidationError(_("Este username já está em uso."))
            else:
                if UsuarioCustomizado.objects.filter(username=username).exists():
                    raise ValidationError(_("Este username já está em uso."))
        return username
    
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '')
        if telefone:
            # Remove caracteres não numéricos
            telefone = ''.join(filter(str.isdigit, telefone))
            if len(telefone) not in [10, 11]:
                raise ValidationError(_("Telefone deve ter 10 ou 11 dígitos."))
        return telefone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telefone = self.cleaned_data['telefone']
        user.is_active = True
        
        if commit:
            user.save()
        
        return user
    

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['cliente', 'quantidade', 'valor', 'data_venda']
        widgets = {
            'cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome do cliente',
                'autofocus': True
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantidade vendida',
                'min': 1
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': '0.01'
            }),
            'data_venda': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': datetime.date.today().strftime('%Y-%m-%d')
            }),
        }
        labels = {
            'cliente': 'Nome do Cliente',
            'quantidade': 'Quantidade',
            'valor': 'Valor (R$)',
            'data_venda': 'Data da Venda'
        }

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade < 1:
            raise forms.ValidationError("A quantidade deve ser pelo menos 1.")
        return quantidade

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return valor