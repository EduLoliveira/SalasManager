import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .forms import VendaForm
from .models import Venda
from django.db.models import Sum, Count, Max, Q
from django.http import HttpResponse
import csv
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.http import JsonResponse

logger = logging.getLogger(__name__)

@login_required
def check_venda_session(request):
    """Verifica se há dados de venda na sessão"""
    venda_data = request.session.get('venda_sucesso', None)
    has_data = venda_data is not None
    
    response_data = {
        'has_venda_data': has_data,
        'venda_data': venda_data or {}
    }
    
    return JsonResponse(response_data)

@login_required
@require_http_methods(["POST"])
def clear_venda_session(request):
    """Limpa os dados de venda da sessão"""
    if 'venda_sucesso' in request.session:
        del request.session['venda_sucesso']
    
    return JsonResponse({'status': 'success'})

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
        
        form = FormularioLogin(request, data=request.POST)
        
        print(f"🔍 FORM IS BOUND: {form.is_bound}")
        print(f"🔍 FORM IS VALID: {form.is_valid()}")
        
        if form.is_valid():
            print("✅ LOGIN BEM-SUCEDIDO")
            user = form.get_user()
            login(request, user)
            
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)
                print("🔍 Sessão: Não lembrar")
            else:
                request.session.set_expiry(1209600)
                print("🔍 Sessão: Lembrar por 2 semanas")
            
            redirect_url = request.POST.get('next', '') or next_url or '/dashboard/'
            print(f"🔍 Redirecionando para: {redirect_url}")
            
            messages.success(request, f'Bem-vindo, {user.username}!')
            return redirect(redirect_url)
            
        else:
            print(f"❌ ERROS DO FORMULÁRIO: {form.errors}")
            if '__all__' in form.errors:
                error_message = form.errors['__all__'][0]
            else:
                error_message = 'Credenciais inválidas. Verifique seu username and password.'
            
            messages.error(request, error_message)
            
            form = FormularioLogin(request, initial={
                'username': request.POST.get('username', ''),
                'remember_me': request.POST.get('remember_me', False)
            })
    
    else:
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
                
                print(f"📝 Dados do usuário antes do save:")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Password: {user.password}")
                print(f"Ativo: {user.is_active}")
                
                user.save()
                
                print(f"✅ Usuário salvo com ID: {user.id}")
                
                login(request, user)
                messages.success(request, 'Conta criada com sucesso!')
                return redirect('sales:dashboard')
                
            except Exception as e:
                print(f"❌ Erro ao salvar usuário: {str(e)}")
                messages.error(request, f'Erro ao criar conta: {str(e)}')
        else:
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
    hoje = timezone.now().date()
    usuario = request.user
    
    # Otimização: Executar todas as consultas em paralelo
    from concurrent.futures import ThreadPoolExecutor
    
    def get_vendas_hoje():
        return Venda.objects.filter(
            data_venda=hoje,
            usuario=usuario
        ).aggregate(total=Sum('valor'))
    
    def get_vendas_mes():
        primeiro_dia_mes = hoje.replace(day=1)
        return Venda.objects.filter(
            data_venda__gte=primeiro_dia_mes,
            data_venda__lte=hoje,
            usuario=usuario
        ).aggregate(total=Sum('valor'))
    
    def get_top_clientes():
        trinta_dias_atras = hoje - timedelta(days=30)
        return list(Venda.objects.filter(
            data_venda__gte=trinta_dias_atras,
            data_venda__lte=hoje,
            usuario=usuario
        ).values('cliente').annotate(
            total=Sum('valor'),
            ultima_compra=Max('data_venda')
        ).order_by('-ultima_compra', '-total')[:5])
    
    def get_dados_grafico():
        dados = {'labels': [], 'values': []}
        for i in range(6, -1, -1):
            data = hoje - timedelta(days=i)
            vendas_dia = Venda.objects.filter(
                data_venda=data,
                usuario=usuario
            ).aggregate(total=Sum('valor'))
            total_dia = vendas_dia['total'] or Decimal('0.00')
            
            dados['labels'].append(data.strftime('%d/%m'))
            dados['values'].append(float(total_dia))
        return dados
    
    # Executar consultas em paralelo para melhor performance
    with ThreadPoolExecutor() as executor:
        futuro_vendas_hoje = executor.submit(get_vendas_hoje)
        futuro_vendas_mes = executor.submit(get_vendas_mes)
        futuro_top_clientes = executor.submit(get_top_clientes)
        futuro_dados_grafico = executor.submit(get_dados_grafico)
        
        vendas_hoje = futuro_vendas_hoje.result()
        vendas_mes = futuro_vendas_mes.result()
        top_clientes = futuro_top_clientes.result()
        chart_data = futuro_dados_grafico.result()
    
    context = {
        'user': usuario,
        'vendas_hoje': vendas_hoje,
        'vendas_mes': vendas_mes,
        'top_clientes': top_clientes,
        'chart_data': chart_data
    }
    
    return render(request, 'subPage/Home/dashboard.html', context)

@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('sales:login')

@login_required
def cadastrar_venda(request):
    if request.method == 'POST':
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.usuario = request.user
            venda.save()
            
            # Armazenar dados da venda para exibir na notificação
            request.session['venda_sucesso'] = {
                'cliente': venda.cliente,
                'valor': str(venda.valor),
                'data_venda': venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else '',
                'quantidade': venda.quantidade
            }
            messages.success(request, 'Venda registrada com sucesso!')
            return redirect('sales:lista_vendas')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = VendaForm()

    return render(request, 'subPage/vendas/cadastro_venda.html', {'form': form})

@login_required
def lista_vendas(request):
    # Obter todos os parâmetros de filtro da URL
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', 'ativas')
    cliente = request.GET.get('cliente', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    ordenar_por = request.GET.get('ordenar_por', '-data_venda')
    
    # Iniciar com todas as vendas do usuário
    vendas = Venda.objects.filter(usuario=request.user)
    
    # Aplicar filtros baseados nos parâmetros da URL
    if busca:
        vendas = vendas.filter(
            Q(cliente__icontains=busca) |
            Q(descricao__icontains=busca)  # REMOVIDO: Q(produto__icontains=busca) - campo não existe
        )
    
    # Filtro de status (ativas/baixadas/todas)
    if status == 'baixadas':
        vendas = vendas.filter(baixada=True)
    elif status == 'ativas':
        vendas = vendas.filter(baixada=False)
    # Se status for 'todas' ou qualquer outro valor, mostra todas
    
    # Filtro por cliente específico
    if cliente:
        vendas = vendas.filter(cliente__icontains=cliente)
    
    # Filtro por período
    if data_inicio:
        try:
            data_inicio_obj = timezone.make_aware(
                datetime.strptime(data_inicio, '%Y-%m-%d')
            )
            vendas = vendas.filter(data_venda__gte=data_inicio_obj)
        except ValueError:
            logger.warning(f"Data início inválida: {data_inicio}")
            pass
    
    if data_fim:
        try:
            data_fim_obj = timezone.make_aware(
                datetime.strptime(data_fim, '%Y-%m-%d')
            ) + timedelta(days=1) - timedelta(seconds=1)
            vendas = vendas.filter(data_venda__lte=data_fim_obj)
        except ValueError:
            logger.warning(f"Data fim inválida: {data_fim}")
            pass
    
    # Ordenação
    if ordenar_por not in ['data_venda', '-data_venda', 'cliente', '-cliente', 'valor', '-valor']:
        ordenar_por = '-data_venda'
    
    vendas = vendas.order_by(ordenar_por)
    
    # Calcular totais
    total_vendas = vendas.count()
    total_valor = vendas.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Agrupar vendas por cliente para o resumo lateral
    vendas_por_cliente = Venda.objects.filter(usuario=request.user).values('cliente').annotate(
        total=Sum('valor'),
        quantidade=Count('id'),
        ultima_data=Max('data_venda')
    ).order_by('-total')[:10]
    
    # Obter lista única de clientes para o filtro
    clientes = Venda.objects.filter(usuario=request.user).values_list('cliente', flat=True).distinct()
    
    context = {
        'vendas': vendas,
        'total_vendas': total_vendas,
        'total_valor': total_valor,
        'busca': busca,
        'status': status,
        'cliente_filtro': cliente,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'ordenar_por': ordenar_por,
        'vendas_por_cliente': vendas_por_cliente,
        'clientes_lista': sorted(set(clientes)),
    }
    return render(request, 'subPage/vendas/lista_vendas.html', context)

@login_required
def baixar_venda(request, venda_id):
    try:
        venda = Venda.objects.get(id=venda_id, usuario=request.user)
        venda.baixada = not venda.baixada
        venda.data_baixa = timezone.now().date() if venda.baixada else None
        venda.save()
        
        messages.success(request, f'Venda {"baixada" if venda.baixada else "reativada"} com sucesso!')
    except Venda.DoesNotExist:
        messages.error(request, 'Venda não encontrada.')
    
    # Redirecionar de volta para a página de lista mantendo os filtros
    redirect_url = request.META.get('HTTP_REFERER', '/vendas/')
    return redirect(redirect_url)

@login_required
def exportar_vendas_csv(request):
    # Obter os mesmos filtros da lista
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', 'ativas')
    cliente = request.GET.get('cliente', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Aplicar os mesmos filtros
    vendas = Venda.objects.filter(usuario=request.user)
    
    if busca:
        vendas = vendas.filter(
            Q(cliente__icontains=busca) |
            Q(descricao__icontains=busca)  # REMOVIDO: Q(produto__icontains=busca) - campo não existe
        )
    
    if status == 'baixadas':
        vendas = vendas.filter(baixada=True)
    elif status == 'ativas':
        vendas = vendas.filter(baixada=False)
    
    if cliente:
        vendas = vendas.filter(cliente__icontains=cliente)
    
    if data_inicio:
        try:
            data_inicio_obj = timezone.make_aware(
                datetime.strptime(data_inicio, '%Y-%m-%d')
            )
            vendas = vendas.filter(data_venda__gte=data_inicio_obj)
        except ValueError:
            logger.warning(f"Data início inválida na exportação: {data_inicio}")
            pass
    
    if data_fim:
        try:
            data_fim_obj = timezone.make_aware(
                datetime.strptime(data_fim, '%Y-%m-%d')
            ) + timedelta(days=1) - timedelta(seconds=1)
            vendas = vendas.filter(data_venda__lte=data_fim_obj)
        except ValueError:
            logger.warning(f"Data fim inválida na exportação: {data_fim}")
            pass
    
    # Criar resposta HTTP com arquivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendas_exportadas.csv"'
    
    writer = csv.writer(response, delimiter=';')
    # REMOVIDO: 'Produto' da lista de colunas
    writer.writerow(['Data Venda', 'Cliente', 'Descrição', 'Valor', 'Status', 'Data Baixa'])
    
    for venda in vendas:
        writer.writerow([
            venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else '',
            venda.cliente,
            venda.descricao,  # REMOVIDO: venda.produto
            str(venda.valor).replace('.', ','),
            'Baixada' if venda.baixada else 'Ativa',
            venda.data_baixa.strftime('%d/%m/%Y') if venda.data_baixa else ''
        ])
    
    return response