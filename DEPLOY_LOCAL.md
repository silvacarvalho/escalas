# 🚀 Guia de Deploy Local - Sistema de Escalas Distritais

## 📋 Pré-requisitos

Certifique-se de ter instalado em sua máquina:

### Obrigatórios:
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** e **npm/yarn** - [Download](https://nodejs.org/)
- **PostgreSQL 12+** - [Download](https://www.postgresql.org/download/)
- **Git** (opcional) - [Download](https://git-scm.com/)

---

## 🗂️ Passo 1: Preparar os Arquivos

### Opção A: Baixar do Emergent
```bash
# Se você tem acesso ao código no Emergent, baixe todos os arquivos
# Ou copie a pasta /app completa
```

### Opção B: Estrutura de Pastas
Crie a seguinte estrutura:

```
sistema-escalas/
├── backend/
│   ├── server.py
│   ├── models.py
│   ├── database.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── .env
└── scripts/
    ├── init_database.py
    └── seed_database.py
```

---

## 🐘 Passo 2: Configurar PostgreSQL

### Windows:

1. **Instalar PostgreSQL:**
   - Baixe o instalador do [site oficial](https://www.postgresql.org/download/windows/)
   - Durante instalação, defina senha para usuário `postgres`
   - Anote a porta (padrão: 5432)

2. **Criar Banco de Dados:**
   ```cmd
   # Abra o SQL Shell (psql)
   # Faça login com usuário postgres
   
   CREATE DATABASE escalas_distritais;
   ```

### macOS:

1. **Instalar PostgreSQL:**
   ```bash
   brew install postgresql@15
   brew services start postgresql@15
   ```

2. **Criar Banco de Dados:**
   ```bash
   psql postgres
   CREATE DATABASE escalas_distritais;
   \q
   ```

### Linux (Ubuntu/Debian):

1. **Instalar PostgreSQL:**
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Criar Banco de Dados:**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE escalas_distritais;
   ALTER USER postgres WITH PASSWORD 'postgres';
   \q
   ```

---

## 🐍 Passo 3: Configurar Backend

### 3.1 - Criar Ambiente Virtual

```bash
# Navegue até a pasta backend
cd sistema-escalas/backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3.2 - Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt deve conter:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic[email]==2.5.0
```

### 3.3 - Configurar .env

Crie o arquivo `backend/.env`:

```env
DATABASE_URL="postgresql://postgres:SUA_SENHA@localhost:5432/escalas_distritais"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET_KEY="sua-chave-secreta-super-segura-12345"
```

**⚠️ IMPORTANTE:** Substitua `SUA_SENHA` pela senha do PostgreSQL que você definiu.

### 3.4 - Criar Tabelas do Banco

```bash
# Na pasta backend com venv ativado
cd ..
python scripts/init_database.py
```

Você deve ver:
```
✅ Banco de dados criado com sucesso!
📊 Tabelas criadas:
  - usuarios
  - distritos
  - igrejas
  ...
```

### 3.5 - Popular Banco com Dados de Teste

```bash
python scripts/seed_database.py
```

---

## ⚛️ Passo 4: Configurar Frontend

### 4.1 - Instalar Dependências

```bash
cd frontend

# Usando npm
npm install

# OU usando yarn (recomendado)
yarn install
```

### 4.2 - Configurar .env

Crie o arquivo `frontend/.env`:

```env
REACT_APP_BACKEND_URL="http://localhost:8001"
```

---

## 🚀 Passo 5: Executar o Sistema

### 5.1 - Iniciar Backend

Abra um terminal:

```bash
cd sistema-escalas/backend

# Ativar ambiente virtual
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Executar servidor
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Você deve ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

**✅ Backend rodando em:** http://localhost:8001

### 5.2 - Iniciar Frontend

Abra OUTRO terminal:

```bash
cd sistema-escalas/frontend

# Executar aplicação React
npm start
# OU
yarn start
```

Você deve ver:
```
Compiled successfully!

You can now view the app in the browser.
  Local:            http://localhost:3000
```

**✅ Frontend rodando em:** http://localhost:3000

---

## 🔐 Passo 6: Acessar o Sistema

### Abra o navegador em: http://localhost:3000

### Credenciais de Teste:

**Pastor Distrital:**
- Usuário: `pastor1`
- Senha: `pastor123`

**Líder de Igreja:**
- Usuário: `lider1`
- Senha: `lider123`

**Pregador:**
- Usuário: `jose.silva`
- Senha: `pregador123`

---

## 🔧 Solução de Problemas Comuns

### ❌ Erro: "connection refused" no Backend

**Causa:** PostgreSQL não está rodando

**Solução:**
```bash
# Windows
# Abra Services.msc e inicie "postgresql-x64-15"

# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
```

---

### ❌ Erro: "Port 8001 already in use"

**Solução:**
```bash
# Encontre o processo usando a porta
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8001 | xargs kill -9
```

---

### ❌ Erro: "Module not found" no Frontend

**Solução:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
# OU
yarn install
```

---

### ❌ Erro: "CORS policy" no navegador

**Solução:** Verifique se o `backend/.env` tem:
```env
CORS_ORIGINS="http://localhost:3000"
```

---

## 📊 Verificar se está Funcionando

### 1. Teste o Backend:
```bash
curl http://localhost:8001/api/districts
```

Deve retornar JSON vazio `[]` ou lista de distritos.

### 2. Teste o Frontend:
- Abra http://localhost:3000
- Você deve ver a tela de login

### 3. Faça Login:
- Use: `pastor1` / `pastor123`
- Deve redirecionar para o Dashboard

---

## 📝 Comandos Úteis

### Parar os Serviços:
```bash
# Backend: Ctrl + C no terminal
# Frontend: Ctrl + C no terminal
# PostgreSQL:
#   Windows: Services.msc
#   macOS: brew services stop postgresql@15
#   Linux: sudo systemctl stop postgresql
```

### Ver Logs do Banco:
```bash
# Ver todas as tabelas
psql -U postgres -d escalas_distritais -c "\dt"

# Ver dados de usuários
psql -U postgres -d escalas_distritais -c "SELECT nome_completo, funcao FROM usuarios;"
```

### Resetar Banco de Dados:
```bash
# Deletar banco
psql -U postgres -c "DROP DATABASE escalas_distritais;"

# Recriar
psql -U postgres -c "CREATE DATABASE escalas_distritais;"

# Reinicializar
python scripts/init_database.py
python scripts/seed_database.py
```

---

## 🎉 Pronto!

Seu sistema está rodando localmente!

**Acessos:**
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8001
- 📚 Documentação API: http://localhost:8001/docs
- 🐘 PostgreSQL: localhost:5432

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique se todas as dependências estão instaladas
2. Confirme que PostgreSQL está rodando
3. Verifique os arquivos `.env` em backend e frontend
4. Veja os logs no terminal para erros específicos

---

**Desenvolvido com ❤️ para gerenciamento de escalas distritais**
