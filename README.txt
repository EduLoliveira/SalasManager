# 📌 README.md — Sistema de Gestão de Vendas
## 📖 Descrição
Sistema web para **gestão de vendas** e **relatórios**, com autenticação de usuários (`is_staff`), controle de clientes e exportação de relatórios.  
A aplicação possibilita cadastro de vendas, listagem com filtros e visualização de métricas no dashboard.

---
## ▶️ Como Rodar o Projeto
### 1. Clonar o repositório
```
git clone https://github.com/EduLoliveira/SalasManager
cd salasManager
cd salasManager
```

### 2. Criar e ativar ambiente virtual
```
python -m venv venv
venv\Scripts\activate      # Windows
# ou
source venv/bin/activate   # Linux/Mac
```

### 3. Instalar dependências
```
pip install -r requirements.txt
python.exe -m pip install --upgrade pip
```

### 4. Configurar variáveis de ambiente
Copiar o arquivo de exemplo para `.env`:
```
cd sistema_vendas
copy .env.example .env      # Windows
# ou
cp .env.example .env        # Linux/Mac
```
Edite o `.env` conforme sua configuração (banco de dados, secret key etc.).

### 5. Rodar as migrações e iniciar servidor
```
python manage.py migrate
python manage.py runserver
```

## ⚙️ Tecnologias
- **Django** (backend)
- **Bootstrap / CSS customizado** (frontend)
- **Chart.js / Plotly** (gráficos do dashboard)
- **Pandas / WeasyPrint** (exportações PDF e Excel)
