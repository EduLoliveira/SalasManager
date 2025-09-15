import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib import messages

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    from .forms import FormularioLogin
    
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        print(f"🔍 METHOD: POST")
        print(f"🔍 POST DATA: {dict(request.POST)}")
        
        # ✅ CORREÇÃO: Use 'request' como primeiro argumento
        form = FormularioLogin(request, data=request.POST)
        
        print(f"🔍 FORM IS BOUND: {form.is_bound}")
        print(f"🔍 FORM IS VALID: {form.is_valid()}")
        
        if form.is_valid():
            print("✅ LOGIN BEM-SUCEDIDO")
            user = form.get_user()
            login(request, user)
            
            # Configurar sessão para "Lembrar-me"
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)  # Sessão de browser
                print("🔍 Sessão: Não lembrar")
            else:
                request.session.set_expiry(1209600)  # 2 semanas
                print("🔍 Sessão: Lembrar por 2 semanas")
            
            # Redirecionar para 'next' ou dashboard
            redirect_url = request.POST.get('next', '') or next_url or '/dashboard/'
            print(f"🔍 Redirecionando para: {redirect_url}")
            
            messages.success(request, f'Bem-vindo, {user.username}!')
            return redirect(redirect_url)
            
        else:
            print(f"❌ ERROS DO FORMULÁRIO: {form.errors}")
            # ✅ Mensagem de erro específica baseada nos erros do formulário
            if '__all__' in form.errors:
                error_message = form.errors['__all__'][0]
            else:
                error_message = 'Credenciais inválidas. Verifique seu username e senha.'
            
            messages.error(request, error_message)
            
            # Manter os dados preenchidos no formulário
            form = FormularioLogin(request, initial={
                'username': request.POST.get('username', ''),
                'remember_me': request.POST.get('remember_me', False)
            })
    
    else:
        # Requisição GET - formulário vazio
        form = FormularioLogin(request)
        print(f"🔍 METHOD: GET")
    
    context = {
        'form': form,
        'next': next_url
    }
    
    return render(request, 'subPage/Login/acesso.html', context)

@require_http_methods(["GET", "POST"])
@csrf_protect
def registro_view(request):
    if request.user.is_authenticated:
        return redirect('sales:dashboard')
    
    from .forms import FormularioRegistro
    
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                
                # DEBUG: Verifique os dados antes de salvar
                print(f"📝 Dados do usuário antes do save:")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Senha: {user.password}")
                print(f"Ativo: {user.is_active}")
                
                user.save()  # Agora salva com commit=True
                
                # DEBUG: Verifique se o usuário foi salvo
                print(f"✅ Usuário salvo com ID: {user.id}")
                
                # Faça login automaticamente
                login(request, user)
                messages.success(request, 'Conta criada com sucesso!')
                return redirect('sales:dashboard')
                
            except Exception as e:
                print(f"❌ Erro ao salvar usuário: {str(e)}")
                messages.error(request, f'Erro ao criar conta: {str(e)}')
        else:
            # Mostre os erros do formulário no console
            print("❌ Erros de validação no formulário:")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"   {field}: {error}")
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = FormularioRegistro()
    
    return render(request, 'subPage/Login/registro.html', {'form': form})

@login_required
def dashboard_view(request):
    return render(request, 'subPage/Home/dashboard.html', {'user': request.user})

@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('sales:login')