
# 📌 README.md — Sistema de Gestão de Vendas

## 📖 Descrição
Sistema web para **gestão de vendas** e **relatórios**, com autenticação de usuários (`is_staff`), controle de clientes e exportação de relatórios.  
A aplicação possibilita cadastro de vendas, listagem com filtros e visualização de métricas no dashboard.

---

## 🚀 Funcionalidades Atuais

### 🔑 0. Tela de Login
- Acesso restrito com **`login_required`**.
- Apenas usuários **`is_staff=True`** conseguem acessar o Dashboard.
- Autenticação gerencia navegação entre telas.

---

### 📊 1. Dashboard
- Página inicial após login.
- Exibe:
  - **Top 3 clientes** que mais compraram.
  - **Gráfico progressivo**:
    - Linha verde: **GANHOS** 💰
    - Linha azul: **QUANTIDADE DE VENDAS** 📦
- **Footer fixo (Menu bar)** com:
  - 📌 Dashboard  
  - 📝 Cadastrar Venda  
  - 📋 Listar Vendas  

---

### 📝 2. Cadastro de Vendas
- Formulário com campos:
  - Cliente
  - Quantidade
  - Valor
  - Data
- Header fixo com botão **Voltar → Dashboard**.
- Botão de **Salvar** cria o registro no banco.

---

### 📋 3. Listagem de Vendas
- Exibição em **tabela responsiva** com:
  - Cliente
  - Quantidade
  - Valor
  - Data
- Funcionalidades:
  - 🔍 **Buscar Cliente**
  - 📆 **Filtros dinâmicos**: Dia, Semana, Mês, Trimestre, Ano
  - 📤 **Exportar para PDF**
  - 📈 Contabilização de compras por cliente (com base nos filtros aplicados)
- Header fixo com botão **Cadastrar Venda**.

---

## 🗃️ Banco de Dados (MVP)
Estrutura mínima:
```
Venda {
    id
    cliente (FK → Cliente)
    quantidade
    valor
    data_venda
}

Cliente {
    id
    nome
    email
    telefone
}
```

---

## 🔮 Futuras Implementações
- **Cadastro de Cliente** (associar vendas diretamente).
- **Encomendas Online**:
  - Usuário cria conta.
  - Solicitação de pedidos com prazo mínimo de **3 dias úteis**.
  - Confirmação via WhatsApp antes de iniciar o pedido.
- **Gestão de Clientes**:
  - Listagem completa.
  - Exclusão e bloqueio de clientes.
- Relatórios em **Excel** e outras integrações.

---

## 📂 Estrutura do Sistema
1. **Login** → Autenticação com `is_staff`
2. **Dashboard**
   - Exibe métricas
   - Top 3 clientes
   - Navegação pelo footer
3. **Cadastro de Venda**
4. **Listagem de Vendas**
   - Filtros
   - Exportações
   - Buscar cliente

---

## ⚙️ Tecnologias
- **Django** (backend)
- **Bootstrap / CSS customizado** (frontend)
- **Chart.js / Plotly** (gráficos do dashboard)
- **Pandas / WeasyPrint** (exportações PDF e Excel)

---

## ▶️ Como Rodar o Projeto
```bash
# Clonar repositório
git clone https://github.com/seu-repo.git
cd seu-repo

# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Criar superusuário (Admin)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```
