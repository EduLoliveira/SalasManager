from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """Decorator que requer que o usuário seja superusuário"""
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='/login/',
        redirect_field_name=None
    )(view_func)

def staff_required(view_func):
    """Decorator que requer que o usuário seja staff"""
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='/login/',
        redirect_field_name=None
    )(view_func)

# Versão com mensagem de erro
def admin_required_with_message(view_func):
    """Decorator que requer superusuário e mostra mensagem de erro"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '❌ Você precisa estar logado para acessar esta página.')
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, '❌ Acesso negado. Apenas administradores podem acessar esta área.')
            return redirect('home')  # ou outra página
        return view_func(request, *args, **kwargs)
    return wrapper