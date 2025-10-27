# ⚡ Guia Rápido de Início

## 🚀 Setup em 5 Minutos

### 1️⃣ Requisitos Mínimos
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

### 2️⃣ Executar Script Automatizado

**Windows:**
```cmd
deploy_windows.bat
```

**Linux/macOS:**
```bash
chmod +x deploy_linux.sh
./deploy_linux.sh
```

### 3️⃣ Iniciar Serviços

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# OU
venv\Scripts\activate     # Windows

uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 4️⃣ Acessar Sistema
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- Docs API: http://localhost:8001/docs

### 5️⃣ Login
```
Usuário: pastor1
Senha: pastor123
```

---

## 📁 Estrutura do Projeto

```
sistema-escalas/
├── backend/                    # API FastAPI
│   ├── server.py              # Servidor principal
│   ├── models.py              # Modelos SQLAlchemy
│   ├── database.py            # Configuração do banco
│   ├── requirements.txt       # Dependências Python
│   └── .env                   # Variáveis de ambiente
│
├── frontend/                   # App React
│   ├── src/
│   │   ├── pages/             # Páginas da aplicação
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── App.js            # Componente principal
│   │   └── index.js          # Entry point
│   ├── package.json          # Dependências Node
│   └── .env                  # Variáveis de ambiente
│
└── scripts/                   # Scripts utilitários
    ├── init_database.py      # Criar tabelas
    └── seed_database.py      # Popular dados
```

---

## ⚙️ Variáveis de Ambiente

### Backend (.env)
```env
DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/escalas_distritais"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET_KEY="sua-chave-secreta"
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL="http://localhost:8001"
```

---

## 🗄️ Banco de Dados PostgreSQL

### Criar Banco Manualmente
```sql
CREATE DATABASE escalas_distritais;
```

### Ver Tabelas
```sql
\c escalas_distritais
\dt
```

### Resetar Dados
```bash
python scripts/init_database.py
python scripts/seed_database.py
```

---

## 🔧 Comandos Úteis

### Backend
```bash
# Instalar dependências
pip install -r requirements.txt

# Criar tabelas
python scripts/init_database.py

# Popular dados
python scripts/seed_database.py

# Iniciar servidor
uvicorn server:app --reload
```

### Frontend
```bash
# Instalar dependências
npm install  # ou yarn install

# Iniciar dev server
npm start    # ou yarn start

# Build produção
npm run build
```

---

## 🐛 Solução Rápida de Problemas

### PostgreSQL não conecta
```bash
# Verificar se está rodando
# Linux: sudo systemctl status postgresql
# macOS: brew services list
# Windows: Services.msc → postgresql-x64-15

# Reiniciar
# Linux: sudo systemctl restart postgresql
# macOS: brew services restart postgresql@15
```

### Porta em uso
```bash
# Matar processo na porta 8001
# Linux/macOS: lsof -ti:8001 | xargs kill -9
# Windows: netstat -ano | findstr :8001
```

### Erro de módulo não encontrado
```bash
# Backend
pip install -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 Funcionalidades Principais

✅ Autenticação JWT com 3 níveis de acesso
✅ CRUD completo de Distritos, Igrejas e Usuários
✅ Geração de escalas automática e manual
✅ Sistema de avaliações e pontuações
✅ Notificações (mock pronto para integração)
✅ Gestão de períodos de indisponibilidade
✅ Analytics e dashboards
✅ Design responsivo e moderno

---

## 🔐 Usuários de Teste

| Usuário | Senha | Perfil |
|---------|-------|--------|
| pastor1 | pastor123 | Pastor Distrital |
| lider1 | lider123 | Líder de Igreja |
| jose.silva | pregador123 | Pregador |

---

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs no terminal
2. Consulte DEPLOY_LOCAL.md para guia completo
3. Verifique configurações do .env

---

**Desenvolvido com ❤️ para gestão de escalas eclesiásticas**
