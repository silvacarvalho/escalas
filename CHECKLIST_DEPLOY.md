# ✅ Checklist de Deploy Local

Use este checklist para garantir que tudo está configurado corretamente.

## 📋 Pré-Instalação

- [ ] Python 3.9+ instalado
  ```bash
  python --version  # ou python3 --version
  ```

- [ ] Node.js 16+ instalado
  ```bash
  node --version
  ```

- [ ] npm ou yarn instalado
  ```bash
  npm --version  # ou yarn --version
  ```

- [ ] PostgreSQL 12+ instalado
  ```bash
  psql --version
  ```

- [ ] Git instalado (opcional)
  ```bash
  git --version
  ```

---

## 🗄️ Configuração do Banco de Dados

- [ ] PostgreSQL está rodando
  - **Linux:** `sudo systemctl status postgresql`
  - **macOS:** `brew services list`
  - **Windows:** Services.msc → verificar postgresql-x64-15

- [ ] Banco de dados criado
  ```sql
  psql -U postgres
  CREATE DATABASE apostello;
  \q
  ```

- [ ] Senha do PostgreSQL definida/conhecida
  ```sql
  ALTER USER postgres WITH PASSWORD 'postgres';
  ```

- [ ] Conexão testada
  ```bash
  psql -U postgres -d apostello -c "SELECT version();"
  ```

---

## 🐍 Configuração do Backend

- [ ] Navegou para pasta backend
  ```bash
  cd escalas/backend
  ```

- [ ] Ambiente virtual criado
  ```bash
  python -m venv venv
  ```

- [ ] Ambiente virtual ativado
  - **Windows:** `venv\Scripts\activate`
  - **Linux/macOS:** `source venv/bin/activate`

- [ ] Dependências instaladas
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Arquivo .env criado e configurado
  - [ ] DATABASE_URL com senha correta
  - [ ] CORS_ORIGINS configurado
  - [ ] JWT_SECRET_KEY definido

- [ ] Tabelas do banco criadas
  ```bash
  python ../scripts/init_database.py
  ```

- [ ] Dados de teste inseridos (opcional)
  ```bash
  python ../scripts/seed_database.py
  ```

- [ ] Backend inicia sem erros
  ```bash
  uvicorn server:app --host 0.0.0.0 --port 8001 --reload
  ```

- [ ] API responde
  ```bash
  curl http://localhost:8001/api/districts
  ```

---

## ⚛️ Configuração do Frontend

- [ ] Navegou para pasta frontend
  ```bash
  cd sistema-escalas/frontend
  ```

- [ ] Arquivo .env criado
  ```env
  REACT_APP_BACKEND_URL="http://localhost:8001"
  ```

- [ ] Dependências instaladas
  ```bash
  npm install  # ou yarn install
  ```

- [ ] Frontend inicia sem erros
  ```bash
  npm start  # ou yarn start
  ```

- [ ] Navegador abre automaticamente
  - URL: http://localhost:3000

- [ ] Página de login carrega corretamente

---

## 🧪 Testes Funcionais

- [ ] Login funciona
  - Usuário: `pastor1`
  - Senha: `pastor123`

- [ ] Dashboard carrega

- [ ] Menu lateral funciona
  - [ ] Distritos
  - [ ] Igrejas
  - [ ] Usuários
  - [ ] Escalas
  - [ ] Perfil
  - [ ] Notificações
  - [ ] Analytics (só para pastor)

- [ ] CRUD de Distritos funciona
  - [ ] Criar
  - [ ] Listar
  - [ ] Editar
  - [ ] Deletar

- [ ] CRUD de Igrejas funciona
  - [ ] Criar com horários de culto
  - [ ] Listar
  - [ ] Editar
  - [ ] Deletar

- [ ] CRUD de Usuários funciona
  - [ ] Criar
  - [ ] Listar com scores
  - [ ] Editar
  - [ ] Deletar

- [ ] Perfil do usuário
  - [ ] Editar informações
  - [ ] Adicionar período de indisponibilidade
  - [ ] Ver scores

---

## 🔧 Solução de Problemas

### Se o Backend não iniciar:

- [ ] Verificou que PostgreSQL está rodando
- [ ] Confirmou credenciais no .env
- [ ] Testou conexão com: `psql -U postgres -d escalas_distritais`
- [ ] Verificou que porta 8001 está livre
- [ ] Viu os logs de erro no terminal

### Se o Frontend não iniciar:

- [ ] Deletou node_modules e reinstalou
- [ ] Verificou que porta 3000 está livre
- [ ] Confirmou que .env tem REACT_APP_BACKEND_URL
- [ ] Viu os logs de erro no terminal

### Se Login não funciona:

- [ ] Verificou que backend está rodando
- [ ] Confirmou que dados foram inseridos (seed)
- [ ] Abriu DevTools do navegador (F12) para ver erros
- [ ] Testou endpoint diretamente:
  ```bash
  curl -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"nome_usuario":"pastor1","senha":"pastor123"}'
  ```

---

## ✅ Deploy Completo!

Se todos os itens estão marcados, seu sistema está funcionando corretamente!

**Próximos Passos:**
1. Explore todas as funcionalidades
2. Crie seus próprios distritos e igrejas
3. Adicione usuários reais
4. Gere suas primeiras escalas

**Importante para Produção:**
- Mude JWT_SECRET_KEY para algo aleatório
- Use HTTPS
- Configure CORS para domínio específico
- Use variáveis de ambiente do servidor
- Configure backups do banco de dados
- Implemente logs adequados
- Configure monitoramento

---

**Documentação Completa:** DEPLOY_LOCAL.md
**Guia Rápido:** README_RAPIDO.md
