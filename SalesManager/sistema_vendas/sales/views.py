import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import VendaForm
from .models import Venda, UsuarioCustomizado
from django.db.models import Sum, Count, Max, Q, Avg
from django.http import HttpResponse
import csv
from datetime import datetime, date, timedelta
from django.utils import timezone
from decimal import Decimal
import json
from django.http import JsonResponse


logger = logging.getLogger(__name__)

# =============================================================================
# DECORATORS PERSONALIZADOS (APENAS PARA ADMIN)
# =============================================================================

def admin_required(view_func):
    """Decorator que verifica se o usuário é superusuário"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('sales:login')
        
        if not request.user.is_superuser:
            messages.error(request, '🔒 Acesso restrito para administradores.')
            return redirect('sales:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

# =============================================================================
# VIEWS DE AUTENTICAÇÃO
# =============================================================================

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
                
                # NOVO USUÁRIO NÃO É STAFF POR PADRÃO
                user.is_staff = False
                user.is_superuser = False
                
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

@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('sales:login')

# =============================================================================
# VIEWS DE CONFIGURAÇÕES STAFF/VENDEDOR
# =============================================================================
@login_required
@require_http_methods(["POST"])
def ativar_modo_staff(request):
    """Ativar modo staff usando código de ativação"""
    codigo_inserido = request.POST.get('codigo_ativacao', '').strip().upper()
    
    print(f"🔍 Código inserido: {codigo_inserido}")
    
    # =============================================================================
    # SISTEMA DE BLOQUEIO POR TENTATIVAS FALHAS
    # =============================================================================
    
    def verificar_bloqueio_tentativas(usuario):
        """Verifica se o usuário está bloqueado por tentativas falhas"""
        if not hasattr(usuario, 'metadata') or not usuario.metadata:
            usuario.metadata = {}
        
        if isinstance(usuario.metadata, str):
            try:
                usuario.metadata = json.loads(usuario.metadata)
            except:
                usuario.metadata = {}
        
        tentativas_info = usuario.metadata.get('tentativas_staff', {})
        tentativas_falhas = tentativas_info.get('count', 0)
        ultima_tentativa = tentativas_info.get('ultima_tentativa')
        bloqueado_ate = tentativas_info.get('bloqueado_ate')
        
        # Verificar se está bloqueado
        if bloqueado_ate:
            try:
                data_bloqueio = datetime.fromisoformat(bloqueado_ate)
                if timezone.now() < data_bloqueio:
                    tempo_restante = data_bloqueio - timezone.now()
                    horas_restantes = int(tempo_restante.total_seconds() / 3600)
                    minutos_restantes = int((tempo_restante.total_seconds() % 3600) / 60)
                    
                    if horas_restantes > 0:
                        return True, f"🔒 Você está bloqueado por {horas_restantes}h {minutos_restantes}min devido a tentativas falhas. Tente novamente mais tarde."
                    else:
                        return True, f"🔒 Você está bloqueado por {minutos_restantes}min devido a tentativas falhas. Tente novamente mais tarde."
                else:
                    # Bloqueio expirado, resetar contador
                    usuario.metadata['tentativas_staff'] = {
                        'count': 0,
                        'ultima_tentativa': timezone.now().isoformat()
                    }
                    usuario.save()
            except (ValueError, TypeError):
                # Se houver erro na data, resetar
                usuario.metadata['tentativas_staff'] = {
                    'count': 0,
                    'ultima_tentativa': timezone.now().isoformat()
                }
                usuario.save()
        
        return False, "Usuário não está bloqueado"
    
    def registrar_tentativa_falha(usuario):
        """Registra uma tentativa falha e aplica bloqueio se necessário"""
        if not hasattr(usuario, 'metadata') or not usuario.metadata:
            usuario.metadata = {}
        
        if isinstance(usuario.metadata, str):
            try:
                usuario.metadata = json.loads(usuario.metadata)
            except:
                usuario.metadata = {}
        
        tentativas_info = usuario.metadata.get('tentativas_staff', {})
        tentativas_falhas = tentativas_info.get('count', 0) + 1
        agora = timezone.now()
        
        # Verificar se é a primeira tentativa hoje
        ultima_tentativa = tentativas_info.get('ultima_tentativa')
        if ultima_tentativa:
            try:
                ultima_data = datetime.fromisoformat(ultima_tentativa).date()
                if ultima_data < agora.date():
                    # Resetar contador se for um novo dia
                    tentativas_falhas = 1
            except (ValueError, TypeError):
                pass
        
        # Atualizar contador
        nova_tentativa_info = {
            'count': tentativas_falhas,
            'ultima_tentativa': agora.isoformat()
        }
        
        # Aplicar bloqueio após 3 tentativas falhas
        if tentativas_falhas >= 3:
            bloqueio_ate = agora + timedelta(days=5)
            nova_tentativa_info['bloqueado_ate'] = bloqueio_ate.isoformat()
            nova_tentativa_info['motivo_bloqueio'] = '3 tentativas falhas em 24h'
        
        usuario.metadata['tentativas_staff'] = nova_tentativa_info
        usuario.save()
        
        return tentativas_falhas
    
    def registrar_tentativa_sucesso(usuario):
        """Reseta o contador de tentativas falhas após um sucesso"""
        if not hasattr(usuario, 'metadata') or not usuario.metadata:
            return
        
        if isinstance(usuario.metadata, str):
            try:
                usuario.metadata = json.loads(usuario.metadata)
            except:
                return
        
        if 'tentativas_staff' in usuario.metadata:
            usuario.metadata['tentativas_staff'] = {
                'count': 0,
                'ultima_tentativa': timezone.now().isoformat(),
                'bloqueado_ate': None
            }
            usuario.save()
    
    # =============================================================================
    # VERIFICAR BLOQUEIO ANTES DE PROCESSAR
    # =============================================================================
    
    usuario = request.user
    bloqueado, mensagem_bloqueio = verificar_bloqueio_tentativas(usuario)
    
    if bloqueado:
        messages.error(request, mensagem_bloqueio)
        return redirect('sales:user_settings')
    
    # =============================================================================
    # SISTEMA DE CÓDIGOS DE ATIVAÇÃO
    # =============================================================================
    
    # Dicionário de códigos válidos e suas características
    CODIGOS_VALIDOS = {
        # Código Principal (Admin Master)
        "88OE-112M-NN21-AH22": {
            "nome": "Código Master",
            "nivel": "admin",
            "permissoes": ["staff", "superuser"],
            "validade": None,
            "usos_maximos": None,
            "descricao": "Acesso completo ao sistema"
        },
        
        # Código Temporário (30 dias)
        "TEMP-30DIAS-2002": {
            "nome": "Código Temporário",
            "nivel": "vendedor",
            "permissoes": ["vendedor"],
            "validade": (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "usos_maximos": None,
            "descricao": "Acesso temporário por 30 dias"
        },

        # Código de Teste
        "DEV4N-EX3C7-3S2X1": {
            "nome": "Código de Teste",
            "nivel": "vendedor", 
            "permissoes": ["vendedor"],
            "validade": None,
            "usos_maximos": None,
            "descricao": "Para testes e desenvolvimento"
        }
    }
    
    def validar_codigo(codigo, config):
        """Valida se o código pode ser usado"""
        
        # 1. Verificar validade
        if config["validade"]:
            try:
                data_validade = datetime.strptime(config["validade"], '%Y-%m-%d').date()
                if timezone.now().date() > data_validade:
                    return False, "Código expirado"
            except ValueError:
                return False, "Data de validade inválida"
        
        # 2. Verificar usos máximos (se aplicável)
        if config["usos_maximos"]:
            # Contar quantas vezes este código já foi usado
            usuarios_com_codigo = 0
            for usuario in UsuarioCustomizado.objects.all():
                usuario_metadata = getattr(usuario, 'metadata', {})
                if (usuario_metadata and 
                    usuario_metadata.get('codigo_ativacao') == codigo):
                    usuarios_com_codigo += 1
            
            if usuarios_com_codigo >= config["usos_maximos"]:
                return False, "Código já atingiu o limite de usos"
        
        return True, "Código válido"
    
    def aplicar_permissoes(usuario, config, codigo_utilizado):
        """Aplica as permissões baseado na configuração do código"""
        
        permissoes = config["permissoes"]
        
        if "superuser" in permissoes:
            usuario.is_superuser = True
            usuario.is_staff = True
        elif "staff" in permissoes:
            usuario.is_staff = True
            usuario.is_superuser = False
        elif "vendedor" in permissoes:
            usuario.is_staff = True
            usuario.is_superuser = False
        
        # Salvar metadata do código usado
        if not hasattr(usuario, 'metadata') or not usuario.metadata:
            usuario.metadata = {}
        
        if isinstance(usuario.metadata, str):
            try:
                usuario.metadata = json.loads(usuario.metadata)
            except:
                usuario.metadata = {}
        
        usuario.metadata.update({
            'codigo_ativacao': codigo_utilizado,
            'codigo_config': {
                'nome': config['nome'],
                'nivel': config['nivel'],
                'data_ativacao': timezone.now().isoformat()
            },
            'staff_ativado_em': timezone.now().isoformat()
        })
    
    # REMOVER A FUNÇÃO validar_codigo_padrao - Vamos aceitar apenas códigos da lista
    # =============================================================================
    # PROCESSAMENTO PRINCIPAL
    # =============================================================================
    
    if codigo_inserido in CODIGOS_VALIDOS:
        config_codigo = CODIGOS_VALIDOS[codigo_inserido]
        
        # Validar código
        valido, mensagem = validar_codigo(codigo_inserido, config_codigo)
        
        if not valido:
            # Registrar tentativa falha
            tentativas = registrar_tentativa_falha(usuario)
            mensagem_erro = f'❌ {mensagem}'
            
            # Adicionar informação sobre tentativas
            if tentativas >= 2:
                tentativas_restantes = 3 - tentativas
                mensagem_erro += f' ({tentativas_restantes} tentativa(s) restante(s) antes do bloqueio)'
            
            messages.error(request, mensagem_erro)
            return redirect('sales:user_settings')
        
        try:
            user = request.user
            print(f"🔍 Usuário antes da ativação: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            
            # Aplicar permissões baseado no código
            aplicar_permissoes(user, config_codigo, codigo_inserido)
            
            # Registrar tentativa bem-sucedida (resetar contador)
            registrar_tentativa_sucesso(user)
            
            user.save()
            
            # Recarregar o usuário do banco para verificar as alterações
            user.refresh_from_db()
            print(f"🔍 Usuário após ativação: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            
            # Atualiza a sessão para refletir as novas permissões
            update_session_auth_hash(request, user)
            
            messages.success(request, f'✅ {config_codigo["nome"]} ativado com sucesso! {config_codigo["descricao"]}')
            logger.info(f'Usuário {user.username} ativou modo staff com código: {codigo_inserido}')
            
            # Adiciona flag na sessão para animação
            request.session['staff_activated'] = True
            request.session['codigo_usado'] = config_codigo['nome']
            
        except Exception as e:
            logger.error(f"Erro ao ativar modo staff: {str(e)}")
            messages.error(request, '❌ Erro ao ativar modo staff. Tente novamente.')
    
    else:
        # Código não encontrado na lista - registrar tentativa falha
        tentativas = registrar_tentativa_falha(usuario)
        mensagem_erro = '❌ Código de ativação inválido. Verifique o código e tente novamente.'
        
        # Adicionar informação sobre tentativas
        if tentativas >= 2:
            tentativas_restantes = 3 - tentativas
            mensagem_erro += f' ({tentativas_restantes} tentativa(s) restante(s) antes do bloqueio)'
        elif tentativas == 3:
            mensagem_erro += ' 🚫 Você foi bloqueado por 5 dias devido a múltiplas tentativas falhas.'
        
        messages.error(request, mensagem_erro)
    
    return redirect('sales:user_settings')

@login_required
@require_http_methods(["POST"])
def desativar_modo_staff(request):
    """Desativar modo staff"""
    try:
        user = request.user
        print(f"🔍 Usuário antes da desativação: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
        
        user.is_staff = False
        user.is_superuser = False
        
        # Limpar metadata
        if hasattr(user, 'metadata') and user.metadata:
            if isinstance(user.metadata, dict):
                user.metadata.pop('codigo_ativacao', None)
                user.metadata.pop('codigo_config', None)
                user.metadata.pop('staff_ativado_em', None)
        
        user.save()
        
        # Recarregar o usuário do banco para verificar as alterações
        user.refresh_from_db()
        print(f"🔍 Usuário após desativação: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
        
        messages.success(request, '🔓 Modo staff desativado com sucesso!')
        logger.info(f'Usuário {user.username} desativou modo staff')
        
        # Adiciona flag na sessão para feedback
        request.session['staff_deactivated'] = True
        
    except Exception as e:
        logger.error(f"Erro ao desativar modo staff: {str(e)}")
        messages.error(request, '❌ Erro ao desativar modo staff.')
    
    return redirect('sales:user_settings')

# =============================================================================
# VIEWS DO DASHBOARD E RELATÓRIOS
# =============================================================================

@login_required
def dashboard_view(request):
    hoje = timezone.now().date()
    usuario = request.user
    
    mes_filtro = request.GET.get('mes')
    
    from concurrent.futures import ThreadPoolExecutor
    
    def get_vendas_hoje():
        return Venda.objects.filter(
            data_venda=hoje,
            usuario=usuario
        ).aggregate(total=Sum('valor'))
    
    def get_vendas_mes():
        if mes_filtro and mes_filtro != 'all':
            try:
                mes = int(mes_filtro)
                ano = hoje.year
                primeiro_dia_mes = date(ano, mes, 1)
                if mes == 12:
                    ultimo_dia_mes = date(ano, mes, 31)
                else:
                    ultimo_dia_mes = date(ano, mes + 1, 1) - timedelta(days=1)
            except (ValueError, TypeError):
                primeiro_dia_mes = hoje.replace(day=1)
                ultimo_dia_mes = hoje
        else:
            primeiro_dia_mes = hoje.replace(day=1)
            ultimo_dia_mes = hoje
        
        return Venda.objects.filter(
            data_venda__gte=primeiro_dia_mes,
            data_venda__lte=ultimo_dia_mes,
            usuario=usuario
        ).aggregate(total=Sum('valor'))
    
    def get_top_clientes():
        if mes_filtro and mes_filtro != 'all':
            try:
                mes = int(mes_filtro)
                ano = hoje.year
                primeiro_dia_mes = date(ano, mes, 1)
                if mes == 12:
                    ultimo_dia_mes = date(ano, mes, 31)
                else:
                    ultimo_dia_mes = date(ano, mes + 1, 1) - timedelta(days=1)
            except (ValueError, TypeError):
                trinta_dias_atras = hoje - timedelta(days=30)
                primeiro_dia_mes = trinta_dias_atras
                ultimo_dia_mes = hoje
        else:
            trinta_dias_atras = hoje - timedelta(days=30)
            primeiro_dia_mes = trinta_dias_atras
            ultimo_dia_mes = hoje
            
        return list(Venda.objects.filter(
            data_venda__gte=primeiro_dia_mes,
            data_venda__lte=ultimo_dia_mes,
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
            'lucro': [],
            'tipo': 'semana'
        }
        
        if mes_filtro and mes_filtro != 'all':
            try:
                mes = int(mes_filtro)
                ano = hoje.year
                primeiro_dia_mes = date(ano, mes, 1)
                if mes == 12:
                    ultimo_dia_mes = date(ano, mes, 31)
                else:
                    ultimo_dia_mes = date(ano, mes + 1, 1) - timedelta(days=1)
                
                data_atual = primeiro_dia_mes
                semana_numero = 1
                
                while data_atual <= ultimo_dia_mes:
                    fim_semana = data_atual + timedelta(days=(6 - data_atual.weekday()))
                    fim_semana = min(fim_semana, ultimo_dia_mes)
                    
                    vendas_semana = Venda.objects.filter(
                        data_venda__gte=data_atual,
                        data_venda__lte=fim_semana,
                        usuario=usuario
                    ).aggregate(
                        total=Sum('valor'),
                        quantidade=Count('id')
                    )
                    
                    dados['labels'].append(f"{semana_numero}ª Semana")
                    dados['quantidade'].append(vendas_semana['quantidade'] or 0)
                    dados['lucro'].append(float(vendas_semana['total'] or Decimal('0.00')))
                    
                    data_atual = fim_semana + timedelta(days=1)
                    semana_numero += 1
                
                dados['tipo'] = 'mes'
                
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao processar filtro de mês: {str(e)}")
                pass
        
        if not dados['labels']:
            dados['tipo'] = 'semana'
            dias_semana_pt = {
                'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui', 
                'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
            }
            
            for i in range(6, -1, -1):
                data = hoje - timedelta(days=i)
                dia_semana_en = data.strftime('%a')
                dia_semana_pt = dias_semana_pt.get(dia_semana_en, dia_semana_en)
                
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
    
    with ThreadPoolExecutor() as executor:
        futuro_vendas_hoje = executor.submit(get_vendas_hoje)
        futuro_vendas_mes = executor.submit(get_vendas_mes)
        futuro_top_clientes = executor.submit(get_top_clientes)
        futuro_dados_grafico = executor.submit(get_dados_grafico)
        
        vendas_hoje = futuro_vendas_hoje.result()
        vendas_mes = futuro_vendas_mes.result()
        top_clientes = futuro_top_clientes.result()
        chart_data = futuro_dados_grafico.result()
    
    chart_data_json = {
        'labels': chart_data['labels'],
        'quantidade': chart_data['quantidade'],
        'lucro': chart_data['lucro'],
        'tipo': chart_data['tipo']
    }
    
    context = {
        'user': usuario,
        'vendas_hoje': vendas_hoje,
        'vendas_mes': vendas_mes,
        'top_clientes': top_clientes,
        'chart_data': chart_data_json,
        'mes_filtro': mes_filtro
    }
    
    return render(request, 'subPage/Home/dashboard.html', context)

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
    elif periodo == '45_dias':
        data_inicio_metrica = hoje - timedelta(days=44)
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
                labels.append(dia_semana)
                valores.append(float(total))
                
        elif periodo_tipo in ["45_dias", "este_mes"]:
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
    inicio_7_dias = hoje - timedelta(days=hoje.weekday())
    
    dados_grafico = {
        "7_dias": montar_dados(inicio_7_dias, inicio_7_dias + timedelta(days=6), "7_dias"),
        "45_dias": montar_dados(hoje - timedelta(days=44), hoje, "45_dias"),
        "este_mes": montar_dados(hoje.replace(day=1), hoje, "este_mes"),
        "ano": montar_dados(hoje.replace(month=1, day=1), hoje, "ano"),
    }

    # Dados para o período atual
    dados_atual = dados_grafico.get(periodo, dados_grafico["7_dias"])

    # TODAS AS VENDAS FILTRADAS (sem limite de 10)
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

# =============================================================================
# VIEWS DE VENDAS (ACESSO LIVRE PARA TODOS OS USUÁRIOS LOGADOS)
# =============================================================================

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
            
            logger.info(f'Venda cadastrada - Usuário: {request.user.username}, Cliente: {venda.cliente}, Valor: R$ {venda.valor}')
            
            return redirect('sales:lista_vendas')
        else:
            messages.error(request, '❌ Erro ao cadastrar venda. Verifique os dados e tente novamente.')
    else:
        form = VendaForm()

    return render(request, 'subPage/vendas/cadastro_venda.html', {'form': form})

@login_required
def lista_vendas(request):
    # Verificar se há mensagem de venda bem-sucedida na sessão e REMOVER após usar
    venda_sucesso = request.session.pop('venda_sucesso', None)
    
    # Obter todos os parâmetros de filtro da URL
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', 'ativas')
    cliente = request.GET.get('cliente', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    ordenar_por = request.GET.get('ordenar_por', '-data_venda')
    
    # Iniciar com todas as vendas do usuário
    vendas = Venda.objects.filter(usuario=request.user)
    
    # Aplicar filtros
    if busca:
        vendas = vendas.filter(Q(cliente__icontains=busca))
    
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
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            vendas = vendas.filter(data_venda__lte=data_fim_obj)
        except ValueError:
            pass
    
    # ORDENAÇÃO
    ordenacao_map = {
        'data_venda': ['data_venda', '-id'],
        '-data_venda': ['-data_venda', '-id'],
        'cliente': ['cliente', '-data_venda'],
        '-cliente': ['-cliente', '-data_venda'],
        'valor': ['valor', '-data_venda'],
        '-valor': ['-valor', '-data_venda'],
    }
    
    campos_ordenacao = ordenacao_map.get(ordenar_por, ['-data_venda', '-id'])
    vendas = vendas.order_by(*campos_ordenacao)
    
    # Calcular totais
    total_vendas = vendas.count()
    total_valor = vendas.aggregate(Sum('valor'))['valor__sum'] or 0
    
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
        'venda_sucesso': venda_sucesso,  # ENVIAR DIRETAMENTE PARA O TEMPLATE
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
    """Exportar lista de vendas como CSV"""
    # Obter os mesmos filtros da lista
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', 'ativas')
    cliente = request.GET.get('cliente', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Aplicar os mesmos filtros
    vendas = Venda.objects.filter(usuario=request.user)
    
    if busca:
        vendas = vendas.filter(Q(cliente__icontains=busca))
    
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
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            vendas = vendas.filter(data_venda__lte=data_fim_obj)
        except ValueError:
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

# =============================================================================
# VIEWS DE PERFIL DO USUÁRIO
# =============================================================================

@login_required
def user_profile(request):
    """Visualizar e editar perfil do usuário"""
    if request.method == 'POST':
        # Processar dados do formulário manualmente
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        
        # Validar e atualizar
        user = request.user
        try:
            user.first_name = first_name
            user.last_name = last_name
            
            # Verificar se email já existe
            if email and email != user.email:
                if UsuarioCustomizado.objects.filter(email=email).exclude(pk=user.pk).exists():
                    messages.error(request, 'Este email já está cadastrado.')
                    return redirect('sales:user_profile')
                user.email = email.lower()
            
            # Validar telefone
            if telefone:
                telefone_limpo = ''.join(filter(str.isdigit, telefone))
                if len(telefone_limpo) not in [10, 11]:
                    messages.error(request, 'Telefone deve ter 10 ou 11 dígitos.')
                    return redirect('sales:user_profile')
                user.telefone = telefone
            
            user.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('sales:user_profile')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar perfil: {str(e)}')
    
    context = {
        'user': request.user,
        'active_tab': 'profile'
    }
    
    return render(request, 'subPage/User/profile.html', context)

@login_required
def user_settings(request):
    """Configurações da conta do usuário"""
    total_vendas = Venda.objects.filter(usuario=request.user).count()
    vendas_este_mes = Venda.objects.filter(
        usuario=request.user,
        data_venda__month=timezone.now().month,
        data_venda__year=timezone.now().year
    ).count()
    
    dias_conta = (timezone.now().date() - request.user.date_joined.date()).days
    
    # Flags para animações
    staff_activated = request.session.pop('staff_activated', False)
    staff_deactivated = request.session.pop('staff_deactivated', False)
    codigo_usado = request.session.pop('codigo_usado', None)
    
    # Obter informações do código usado
    codigo_info = None
    bloqueio_info = None
    
    if hasattr(request.user, 'metadata') and request.user.metadata:
        if isinstance(request.user.metadata, dict):
            codigo_info = request.user.metadata.get('codigo_config', {})
            
            # Verificar status de bloqueio
            tentativas_info = request.user.metadata.get('tentativas_staff', {})
            if tentativas_info:
                bloqueio_ate = tentativas_info.get('bloqueado_ate')
                tentativas_count = tentativas_info.get('count', 0)
                
                if bloqueio_ate:
                    try:
                        data_bloqueio = datetime.fromisoformat(bloqueio_ate)
                        if timezone.now() < data_bloqueio:
                            tempo_restante = data_bloqueio - timezone.now()
                            horas = int(tempo_restante.total_seconds() / 3600)
                            minutos = int((tempo_restante.total_seconds() % 3600) / 60)
                            
                            bloqueio_info = {
                                'bloqueado': True,
                                'ate': data_bloqueio,
                                'horas_restantes': horas,
                                'minutos_restantes': minutos,
                                'tentativas': tentativas_count
                            }
                        else:
                            # Bloqueio expirado
                            bloqueio_info = {
                                'bloqueado': False,
                                'tentativas': 0
                            }
                    except (ValueError, TypeError):
                        bloqueio_info = {
                            'bloqueado': False,
                            'tentativas': tentativas_count
                        }
                else:
                    bloqueio_info = {
                        'bloqueado': False,
                        'tentativas': tentativas_count
                    }
    
    context = {
        'active_tab': 'settings',
        'total_vendas': total_vendas,
        'vendas_este_mes': vendas_este_mes,
        'dias_conta': dias_conta,
        'staff_activated': staff_activated,
        'staff_deactivated': staff_deactivated,
        'codigo_usado': codigo_usado,
        'codigo_info': codigo_info,
        'bloqueio_info': bloqueio_info,
    }
    
    return render(request, 'subPage/User/settings.html', context)

@login_required
def change_password(request):
    """Alterar senha do usuário"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Atualizar a sessão para não deslogar o usuário
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('sales:change_password')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'active_tab': 'password'
    }
    
    return render(request, 'subPage/User/change_password.html', context)

# =============================================================================
# VIEWS ADMINISTRATIVAS (APENAS PARA SUPERUSERS) - CORRIGIDAS
# =============================================================================


@login_required
@admin_required
def gerenciar_usuarios(request):
    """Gerenciar todos os usuários do sistema"""
    # Filtros
    busca = request.GET.get('busca', '')
    tipo_usuario = request.GET.get('tipo', 'todos')
    
    usuarios = UsuarioCustomizado.objects.all()
    
    # Aplicar filtros
    if busca:
        usuarios = usuarios.filter(
            Q(username__icontains=busca) |
            Q(email__icontains=busca) |
            Q(first_name__icontains=busca) |
            Q(last_name__icontains=busca)
        )
    
    if tipo_usuario == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    elif tipo_usuario == 'superusers':
        usuarios = usuarios.filter(is_superuser=True)
    elif tipo_usuario == 'ativos':
        usuarios = usuarios.filter(is_active=True)
    elif tipo_usuario == 'inativos':
        usuarios = usuarios.filter(is_active=False)
    
    # Ordenação
    ordenar_por = request.GET.get('ordenar_por', '-date_joined')
    usuarios = usuarios.order_by(ordenar_por)
    
    # Adicionar estatísticas para cada usuário - CORRIGIDO
    usuarios_com_stats = []
    for usuario in usuarios:
        # Usar o related_name correto 'vendas' em vez de 'venda'
        total_vendas = Venda.objects.filter(usuario=usuario).count()
        valor_total = Venda.objects.filter(usuario=usuario).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        ultima_venda = Venda.objects.filter(usuario=usuario).aggregate(
            ultima=Max('data_venda')
        )['ultima']
        
        usuarios_com_stats.append({
            'usuario': usuario,
            'stats': {
                'total_vendas': total_vendas,
                'valor_total': valor_total,
                'ultima_venda': ultima_venda
            }
        })
    
    context = {
        'usuarios_com_stats': usuarios_com_stats,
        'busca': busca,
        'tipo_usuario': tipo_usuario,
        'ordenar_por': ordenar_por,
        'total_usuarios': usuarios.count(),
    }
    
    return render(request, 'subPage/Admin/gerenciar_usuarios.html', context)

# =============================================================================
# APIs e UTILITÁRIOS
# =============================================================================
@login_required
def check_venda_session(request):
    """Verifica se há dados de venda na sessão"""
    venda_data = request.session.get('venda_sucesso', None)
    has_data = venda_data is not None
    
    print(f"🔍 CHECK SESSION - Has data: {has_data}, Data: {venda_data}")
    
    response_data = {
        'has_venda_data': has_data,
        'venda_data': venda_data or {}
    }
    
    return JsonResponse(response_data)

@login_required
@require_http_methods(["POST"])
def clear_venda_session(request):
    """Limpa os dados de venda da sessão"""
    print("🧹 CLEARING SESSION")
    if 'venda_sucesso' in request.session:
        del request.session['venda_sucesso']
        print("✅ Session cleared")
    
    return JsonResponse({'status': 'success'})

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
    for venda in vendas[:10]:
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
        writer.writerow([])
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
def enviar_relatorio_email(request):
    """Enviar relatório de vendas por e-mail"""
    if request.method == 'POST':
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            email_destino = request.POST.get('email')
            
            if not email_destino:
                return JsonResponse({'success': False, 'error': 'E-mail não informado'})
            
            # Validar formato do email
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_destino):
                return JsonResponse({'success': False, 'error': 'Formato de e-mail inválido'})
            
            # Obter parâmetros
            periodo = request.POST.get('periodo', '7_dias')
            status_filter = request.POST.get('status', 'todos')
            data_inicio_filtro = request.POST.get('data_inicio', '')
            data_fim_filtro = request.POST.get('data_fim', '')
            
            # Buscar dados
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
            
            # Mapear nomes
            periodo_nome = {
                '7_dias': 'Últimos 7 dias',
                '45_dias': 'Últimos 45 dias', 
                'este_mes': 'Este mês',
                'ano': 'Ano'
            }.get(periodo, periodo)
            
            status_nome = {
                'todos': 'Todos',
                'concluidas': 'Concluídas',
                'pendentes': 'Pendentes'
            }.get(status_filter, status_filter)
            
            # Criar mensagem
            assunto = f"Relatório de Vendas - {timezone.now().strftime('%d/%m/%Y')}"
            
            mensagem = f"""
RELATÓRIO DE VENDAS - SALESMANAGER

Data do relatório: {timezone.now().strftime('%d/%m/%Y %H:%M')}
Período: {periodo_nome}
Status: {status_nome}
Data início: {data_inicio_filtro or 'Não informado'}
Data fim: {data_fim_filtro or 'Não informado'}

RESUMO:
• Total de vendas: {total_vendas}
• Valor total: R$ {valor_total:.2f}

Para visualizar o relatório completo com gráficos e todos os dados,
acesse o sistema SalesManager.

--
Este é um e-mail automático. Não responda.
SalesManager System
            """
            
            # Tentar enviar e-mail
            try:
                send_mail(
                    assunto,
                    mensagem,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salesmanager.com'),
                    [email_destino],
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Relatório enviado com sucesso para {email_destino}'
                })
                
            except Exception as e:
                logger.error(f"Erro SMTP: {str(e)}")
                return JsonResponse({
                    'success': False, 
                    'error': 'Servidor de e-mail não disponível. O relatório foi salvo no sistema.'
                })
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Erro interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})