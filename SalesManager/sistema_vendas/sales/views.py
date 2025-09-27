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
from datetime import datetime, date, timedelta
from django.utils import timezone
from decimal import Decimal
import json
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
            quantidade=Count('id'),
            ultima_compra=Max('data_venda')
        ).order_by('-total')[:10])
    
    def get_dados_grafico():
        dados = {
            'labels': [], 
            'quantidade': [],
            'lucro': []
        }
        
        # Mapeamento de dias da semana em português
        dias_semana_pt = {
            'Mon': 'Seg',
            'Tue': 'Ter',
            'Wed': 'Qua',
            'Thu': 'Qui',
            'Fri': 'Sex',
            'Sat': 'Sáb',
            'Sun': 'Dom'
        }
        
        for i in range(6, -1, -1):
            data = hoje - timedelta(days=i)
            dia_semana_en = data.strftime('%a')  # Retorna Mon, Tue, Wed, etc.
            dia_semana_pt = dias_semana_pt.get(dia_semana_en, dia_semana_en)
            
            # Buscar quantidade de vendas e valor total para o dia
            vendas_dia = Venda.objects.filter(
                data_venda=data,
                usuario=usuario
            ).aggregate(
                total=Sum('valor'),
                quantidade=Count('id')
            )
            
            dados['labels'].append(dia_semana_pt)
            dados['quantidade'].append(vendas_dia['quantidade'] or 0)
            dados['lucro'].append(float(vendas_dia['total'] or Decimal('0.00')))
        
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
    
    # Converter para JSON seguro para o template
    chart_data_json = {
        'labels': chart_data['labels'],
        'quantidade': chart_data['quantidade'],
        'lucro': chart_data['lucro']
    }
    
    context = {
        'user': usuario,
        'vendas_hoje': vendas_hoje,
        'vendas_mes': vendas_mes,
        'top_clientes': top_clientes,
        'chart_data': chart_data_json
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
            Q(cliente__icontains=busca)
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
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            vendas = vendas.filter(data_venda__gte=data_inicio_obj)
        except ValueError:
            logger.warning(f"Data início inválida: {data_inicio}")
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
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
    """Exportar lista de vendas como CSV (para a página de lista de vendas)"""
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
            Q(cliente__icontains=busca)
        )
    
    if status == 'baixadas':
        vendas = vendas.filter(baixada=True)
    elif status == 'ativas':
        vendas = vendas.filter(baixada=False)
    
    if cliente:
        vendas = vendas.filter(cliente__icontains=cliente)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            vendas = vendas.filter(data_venda__gte=data_inicio_obj)
        except ValueError:
            logger.warning(f"Data início inválida na exportação: {data_inicio}")
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            vendas = vendas.filter(data_venda__lte=data_fim_obj)
        except ValueError:
            logger.warning(f"Data fim inválida na exportação: {data_fim}")
            pass
    
    # Criar resposta HTTP com arquivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendas_exportadas.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Data Venda', 'Cliente', 'Quantidade', 'Valor', 'Status', 'Data Baixa'])
    
    for venda in vendas:
        writer.writerow([
            venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else '',
            venda.cliente,
            venda.quantidade,
            str(venda.valor).replace('.', ','),
            'Baixada' if venda.baixada else 'Ativa',
            venda.data_baixa.strftime('%d/%m/%Y') if venda.data_baixa else ''
        ])
    
    return response

@login_required
def relatorio_vendas(request):
    usuario = request.user
    hoje = timezone.now().date()

    # Filtros
    periodo = request.GET.get('periodo', '7_dias')
    status_filter = request.GET.get('status', 'todos')
    data_inicio_filtro = request.GET.get('data_inicio', '')
    data_fim_filtro = request.GET.get('data_fim', '')
    status_listagem = request.GET.get('status_listagem', 'todos')

    # Verificar se é uma requisição AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Base de consulta - TODAS as vendas do usuário para listagem
    vendas_listagem = Venda.objects.filter(usuario=usuario)

    # Base de consulta - Para gráfico e métricas (sem filtros de data específicos)
    vendas_grafico = Venda.objects.filter(usuario=usuario)

    # Aplicar filtro de status principal para ambas as consultas
    if status_filter == 'concluidas':
        vendas_listagem = vendas_listagem.filter(baixada=True)
        vendas_grafico = vendas_grafico.filter(baixada=True)
    elif status_filter == 'pendentes':
        vendas_listagem = vendas_listagem.filter(baixada=False)
        vendas_grafico = vendas_grafico.filter(baixada=False)

    # Aplicar filtros de data específicos apenas para listagem
    if data_inicio_filtro:
        try:
            data_inicio_obj = datetime.strptime(data_inicio_filtro, '%Y-%m-%d').date()
            vendas_listagem = vendas_listagem.filter(data_venda__gte=data_inicio_obj)
        except ValueError:
            logger.warning(f"Data início inválida: {data_inicio_filtro}")

    if data_fim_filtro:
        try:
            data_fim_obj = datetime.strptime(data_fim_filtro, '%Y-%m-%d').date()
            vendas_listagem = vendas_listagem.filter(data_venda__lte=data_fim_obj)
        except ValueError:
            logger.warning(f"Data fim inválida: {data_fim_filtro}")

    # Aplicar filtro de status da listagem apenas para listagem
    if status_listagem == 'concluidas':
        vendas_listagem = vendas_listagem.filter(baixada=True)
    elif status_listagem == 'pendentes':
        vendas_listagem = vendas_listagem.filter(baixada=False)

    # Determinar o período para as métricas e gráfico (SEM os filtros específicos)
    if periodo == '7_dias':
        # Garantir que começa na segunda-feira da semana atual
        data_inicio_metrica = hoje - timedelta(days=hoje.weekday())
    elif periodo == '45_dias':  # ALTERADO: de 30_dias para 45_dias
        data_inicio_metrica = hoje - timedelta(days=44)  # ALTERADO: de 29 para 44
    elif periodo == 'este_mes':
        data_inicio_metrica = hoje.replace(day=1)
    elif periodo == 'ano':
        data_inicio_metrica = hoje.replace(month=1, day=1)
    else:
        # Padrão: semana atual começando na segunda
        data_inicio_metrica = hoje - timedelta(days=hoje.weekday())

    # Dados para métricas (usando o período selecionado SEM filtros específicos)
    vendas_periodo_metrica = vendas_grafico.filter(
        data_venda__gte=data_inicio_metrica, 
        data_venda__lte=hoje
    )
    
    total_vendas = vendas_periodo_metrica.count()
    valor_total = vendas_periodo_metrica.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    dias_ativos = vendas_periodo_metrica.dates('data_venda', 'day').distinct().count()

    # ---- Função para gerar dados de gráfico por intervalo ----
    def montar_dados(data_inicio, data_fim, periodo_tipo="7_dias"):
        qs = vendas_grafico.filter(data_venda__gte=data_inicio, data_venda__lte=data_fim)
        labels, valores = [], []

        if periodo_tipo == "7_dias":
            # Para 7 dias: apenas dias da semana (Seg a Dom)
            dias_map = {'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui', 'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'}
            
            datas = [data_inicio + timedelta(days=i) for i in range(7)]
            for data in datas:
                dia_semana = dias_map.get(data.strftime('%a'), data.strftime('%a'))
                total = qs.filter(data_venda=data).aggregate(total=Sum('valor'))['total'] or 0
                labels.append(dia_semana)  # Apenas o dia da semana
                valores.append(float(total))
                
        elif periodo_tipo in ["45_dias", "este_mes"]:  # ALTERADO: de 30_dias para 45_dias
            # Para 45 dias e este mês: agrupar por semanas
            semana_atual = 1
            data_semana_inicio = data_inicio
            
            while data_semana_inicio <= data_fim:
                data_semana_fim = min(data_semana_inicio + timedelta(days=6), data_fim)
                
                total_semana = qs.filter(
                    data_venda__gte=data_semana_inicio,
                    data_venda__lte=data_semana_fim
                ).aggregate(total=Sum('valor'))['total'] or 0
                
                labels.append(f"{semana_atual}ª semana")
                valores.append(float(total_semana))
                
                semana_atual += 1
                data_semana_inicio = data_semana_fim + timedelta(days=1)
                
        elif periodo_tipo == "ano":
            # Para ano: meses
            for m in range(1, 13):
                inicio_mes = date(data_inicio.year, m, 1)
                if inicio_mes > data_fim:
                    break
                    
                fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                fim_mes = min(fim_mes, data_fim)
                
                total_mes = qs.filter(
                    data_venda__gte=inicio_mes,
                    data_venda__lte=fim_mes
                ).aggregate(total=Sum('valor'))['total'] or 0
                
                labels.append(inicio_mes.strftime("%b"))
                valores.append(float(total_mes))

        return {"labels": labels, "valores": valores}

    # ---- Montar todos os períodos de uma vez ----
    # Para 7 dias: sempre de segunda a domingo da semana atual
    inicio_7_dias = hoje - timedelta(days=hoje.weekday())
    
    dados_grafico = {
        "7_dias": montar_dados(inicio_7_dias, inicio_7_dias + timedelta(days=6), "7_dias"),
        "45_dias": montar_dados(hoje - timedelta(days=44), hoje, "45_dias"),  # ALTERADO: de 30_dias para 45_dias
        "este_mes": montar_dados(hoje.replace(day=1), hoje, "este_mes"),
        "ano": montar_dados(hoje.replace(month=1, day=1), hoje, "ano"),
    }

    # Dados para o período atual
    dados_atual = dados_grafico.get(periodo, dados_grafico["7_dias"])

    # TODAS AS VENDAS FILTRADAS (sem limite de 10) - usa vendas_listagem que tem todos os filtros
    vendas_filtradas = vendas_listagem.order_by('-data_venda', '-data_criacao')

    context = {
        "total_vendas": total_vendas,
        "valor_total": valor_total,
        "dias_ativos": dias_ativos,
        "vendas_recentes": vendas_filtradas,
        "dados_grafico": dados_atual,
        "dados_grafico_json": json.dumps(dados_grafico),
        "periodo_selecionado": periodo,
        "status_selecionado": status_filter,
        "data_inicio_filtro": data_inicio_filtro,
        "data_fim_filtro": data_fim_filtro,
        "status_listagem_selecionado": status_listagem,
    }

    # Se for requisição AJAX, retornar JSON
    if is_ajax:
        # Preparar dados para resposta AJAX
        vendas_data = []
        for venda in vendas_filtradas:
            vendas_data.append({
                'cliente': venda.cliente,
                'data_venda': venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else '',
                'quantidade': venda.quantidade,
                'valor': float(venda.valor),
                'baixada': venda.baixada,
                'id': venda.id
            })

        return JsonResponse({
            'success': True,
            'total_vendas': total_vendas,
            'valor_total': float(valor_total),
            'dias_ativos': dias_ativos,
            'dados_grafico': dados_atual,
            'vendas_recentes': vendas_data,
            'vendas_count': vendas_filtradas.count()
        })
    
    return render(request, "subPage/Home/relatorio_vendas.html", context)


@login_required
def cliente_compras_api(request):
    """API para obter dados das compras de um cliente específico"""
    cliente_nome = request.GET.get('cliente', '')
    
    if not cliente_nome:
        return JsonResponse({'error': 'Nome do cliente não fornecido'})
    
    # Buscar todas as vendas do cliente para o usuário atual
    vendas = Venda.objects.filter(
        usuario=request.user,
        cliente__iexact=cliente_nome
    ).order_by('-data_venda')
    
    if not vendas.exists():
        return JsonResponse({'error': 'Nenhuma compra encontrada para este cliente'})
    
    # Calcular métricas
    total_gasto = vendas.aggregate(total=Sum('valor'))['total'] or 0
    quantidade_compras = vendas.count()
    ticket_medio = total_gasto / quantidade_compras if quantidade_compras > 0 else 0
    
    # Formatar última compra
    ultima_venda = vendas.first()
    ultima_compra = ultima_venda.data_venda.strftime('%d/%m/%Y') if ultima_venda.data_venda else 'N/A'
    
    # Preparar lista das últimas compras
    compras = []
    for venda in vendas[:10]:  # Últimas 10 compras
        compras.append({
            'data': venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else 'N/A',
            'valor': float(venda.valor)
        })
    
    return JsonResponse({
        'cliente': cliente_nome,
        'total_gasto': float(total_gasto),
        'quantidade_compras': quantidade_compras,
        'ticket_medio': float(ticket_medio),
        'ultima_compra': ultima_compra,
        'compras': compras
    })

@login_required
def exportar_relatorio_csv(request):
    """Exportar relatório de vendas como CSV"""
    try:
        # Obter os mesmos parâmetros de filtro do relatório
        periodo = request.GET.get('periodo', '7_dias')
        status_filter = request.GET.get('status', 'todos')
        data_inicio_filtro = request.GET.get('data_inicio', '')
        data_fim_filtro = request.GET.get('data_fim', '')
        status_listagem = request.GET.get('status_listagem', 'todos')
        
        # Aplicar os mesmos filtros da view relatorio_vendas
        vendas = Venda.objects.filter(usuario=request.user)
        
        if status_filter == 'concluidas':
            vendas = vendas.filter(baixada=True)
        elif status_filter == 'pendentes':
            vendas = vendas.filter(baixada=False)
            
        if status_listagem == 'concluidas':
            vendas = vendas.filter(baixada=True)
        elif status_listagem == 'pendentes':
            vendas = vendas.filter(baixada=False)
            
        if data_inicio_filtro:
            try:
                data_inicio_obj = datetime.strptime(data_inicio_filtro, '%Y-%m-%d').date()
                vendas = vendas.filter(data_venda__gte=data_inicio_obj)
            except ValueError:
                pass
                
        if data_fim_filtro:
            try:
                data_fim_obj = datetime.strptime(data_fim_filtro, '%Y-%m-%d').date()
                vendas = vendas.filter(data_venda__lte=data_fim_obj)
            except ValueError:
                pass
        
        # Ordenar por data mais recente
        vendas = vendas.order_by('-data_venda')
        
        # Criar resposta HTTP com arquivo CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="relatorio_vendas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Relatório de Vendas - SalesManager'])
        writer.writerow(['Data de exportação', timezone.now().strftime('%d/%m/%Y %H:%M:%S')])
        writer.writerow(['Período', periodo])
        writer.writerow(['Status', status_filter])
        writer.writerow(['Data início', data_inicio_filtro or 'Não informado'])
        writer.writerow(['Data fim', data_fim_filtro or 'Não informado'])
        writer.writerow([])  # Linha em branco
        writer.writerow(['Data Venda', 'Cliente', 'Quantidade', 'Valor', 'Status', 'Data Baixa'])
        
        for venda in vendas:
            writer.writerow([
                venda.data_venda.strftime('%d/%m/%Y') if venda.data_venda else '',
                venda.cliente,
                venda.quantidade,
                str(venda.valor).replace('.', ','),
                'Baixada' if venda.baixada else 'Ativa',
                venda.data_baixa.strftime('%d/%m/%Y') if venda.data_baixa else ''
            ])
        
        # Adicionar totais
        total_vendas = vendas.count()
        valor_total = vendas.aggregate(total=Sum('valor'))['total'] or 0
        
        writer.writerow([])
        writer.writerow(['TOTAL DE VENDAS', total_vendas])
        writer.writerow(['VALOR TOTAL', str(valor_total).replace('.', ',')])
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {str(e)}")
        messages.error(request, 'Erro ao exportar relatório CSV')
        return redirect('sales:relatorio_vendas')


@login_required
@require_http_methods(["POST"])
@csrf_protect
def enviar_relatorio_email(request):
    """Enviar relatório de vendas por e-mail - Versão Simplificada e Corrigida"""
    try:
        # CORREÇÃO: Ler dados apenas do POST (nunca do body)
        email_destino = request.POST.get('email')
        periodo = request.POST.get('periodo', '7_dias')
        status_filter = request.POST.get('status', 'todos')
        data_inicio_filtro = request.POST.get('data_inicio', '')
        data_fim_filtro = request.POST.get('data_fim', '')
        
        if not email_destino:
            return JsonResponse({'success': False, 'error': 'E-mail não informado'})
        
        # Validar formato do email
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_destino):
            return JsonResponse({'success': False, 'error': 'Formato de e-mail inválido'})
        
        # Buscar dados com os filtros
        vendas = Venda.objects.filter(usuario=request.user)
        
        if status_filter == 'concluidas':
            vendas = vendas.filter(baixada=True)
        elif status_filter == 'pendentes':
            vendas = vendas.filter(baixada=False)
            
        if data_inicio_filtro:
            try:
                data_inicio_obj = datetime.strptime(data_inicio_filtro, '%Y-%m-%d').date()
                vendas = vendas.filter(data_venda__gte=data_inicio_obj)
            except ValueError:
                pass
                
        if data_fim_filtro:
            try:
                data_fim_obj = datetime.strptime(data_fim_filtro, '%Y-%m-%d').date()
                vendas = vendas.filter(data_venda__lte=data_fim_obj)
            except ValueError:
                pass
        
        total_vendas = vendas.count()
        valor_total = vendas.aggregate(total=Sum('valor'))['total'] or 0
        
        # Criar mensagem do relatório
        periodo_nome = {
            '7_dias': 'Últimos 7 dias',
            '45_dias': 'Últimos 45 dias', 
            'este_mes': 'Este mês',
            'ano': 'Ano atual'
        }.get(periodo, periodo)
        
        status_nome = {
            'todos': 'Todas',
            'concluidas': 'Concluídas',
            'pendentes': 'Pendentes'
        }.get(status_filter, status_filter)
        
        assunto = f"Relatório de Vendas - {timezone.now().strftime('%d/%m/%Y')}"
        
        mensagem = f"""
RELATÓRIO DE VENDAS - SALESMANAGER

Data do relatório: {timezone.now().strftime('%d/%m/%Y %H:%M')}
Usuário: {request.user.username}
Período: {periodo_nome}
Status: {status_nome}
Data início: {data_inicio_filtro or 'Não informado'}
Data fim: {data_fim_filtro or 'Não informado'}

RESUMO:
• Total de vendas: {total_vendas}
• Valor total: R$ {valor_total:.2f}

DETALHES DAS ÚLTIMAS VENDAS:
"""
        # Adicionar últimas 10 vendas
        for i, venda in enumerate(vendas.order_by('-data_venda')[:10], 1):
            status = "Baixada" if venda.baixada else "Ativa"
            mensagem += f"{i}. {venda.data_venda.strftime('%d/%m/%Y')} - {venda.cliente} - R$ {venda.valor:.2f} - {status}\n"
        
        mensagem += f"""
--
Este é um e-mail automático gerado pelo SalesManager.
"""
        
        # Tentar enviar e-mail
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                assunto,
                mensagem,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salasmanager.com'),
                [email_destino],
                fail_silently=False,
            )
            
            logger.info(f"E-mail enviado para {email_destino}")
            return JsonResponse({
                'success': True, 
                'message': f'Relatório enviado com sucesso para {email_destino}'
            })
            
        except Exception as e:
            logger.error(f"Erro SMTP: {str(e)}")
            # Fallback para desenvolvimento
            if settings.DEBUG:
                print("="*50)
                print("E-MAIL SIMULADO (Desenvolvimento):")
                print(f"Para: {email_destino}")
                print(f"Assunto: {assunto}")
                print(mensagem)
                print("="*50)
                return JsonResponse({
                    'success': True,
                    'message': f'E-mail simulado para {email_destino} (modo desenvolvimento)'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Erro ao enviar e-mail. Serviço temporariamente indisponível.'
                })
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Erro interno: {str(e)}'
        })