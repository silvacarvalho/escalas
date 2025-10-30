# 🧪 Guia de Testes Backend PostgreSQL

## ✅ Pré-requisitos

1. **PostgreSQL instalado e rodando**
   - Porta: 5432 (padrão)
   - Usuário: postgres
   - Senha: postgres
   - Banco: escalas_distritais

2. **Python 3.8+** com dependências instaladas

## 📋 Passo a Passo para Testes

### 1️⃣ Verificar Conexão com PostgreSQL

```bash
# No diretório /app
python scripts/test_connection.py
```

**Resultado esperado:**
```
✅ Conexão estabelecida com sucesso!
📦 Versão do PostgreSQL: ...
✅ Sessão criada com sucesso!
🗄️  Banco de dados: apostello
```

### 2️⃣ Criar Banco de Dados (se necessário)

Se o banco não existe, crie-o com:

```bash
# No terminal PostgreSQL
psql -U postgres
CREATE DATABASE escalas_distritais;
\q
```

### 3️⃣ Inicializar Esquema do Banco

```bash
# No diretório /app
python scripts/init_database.py
```

**Resultado esperado:**
```
✅ Banco de dados criado com sucesso!

📊 Tabelas criadas:
  - usuarios
  - distritos
  - igrejas
  - escalas
  - itens_escala
  - avaliacoes
  - notificacoes
  - solicitacoes_troca
  - delegacoes
  - logs_auditoria

🎉 Sistema pronto para uso!
```

### 4️⃣ Popular Banco com Dados de Teste

```bash
# No diretório /app
python scripts/seed_database.py
```

**Resultado esperado:**
```
✅ Banco de dados populado com sucesso!

📋 Credenciais de Teste:
==================================================
Pastor Distrital:
  Usuário: pastor1
  Senha: pastor123

Líder de Igreja:
  Usuário: lider1
  Senha: lider123

Pregador:
  Usuário: jose.silva
  Senha: pregador123
==================================================

📊 Estatísticas:
  • 2 Distritos
  • 3 Igrejas
  • 12 Usuários
  • 10 Pregadores
  • 4 Cantores
```

### 5️⃣ Iniciar Backend

```bash
# No diretório /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Ou usando supervisor (se configurado):**
```bash
sudo supervisorctl restart backend
```

### 6️⃣ Testar Endpoints com curl

#### Login
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"nome_usuario":"pastor1","senha":"pastor123"}'
```

**Resposta esperada:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Listar Distritos (use o token obtido)
```bash
curl -X GET http://localhost:8001/api/districts \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

#### Listar Igrejas
```bash
curl -X GET http://localhost:8001/api/churches \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

#### Listar Usuários
```bash
curl -X GET http://localhost:8001/api/users \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 🔍 Verificações de Saúde

### Verificar se o Backend está rodando
```bash
curl http://localhost:8001/docs
```

Você deve ver a documentação interativa do FastAPI.

### Verificar logs do Backend
```bash
# Se usando supervisor
tail -f /var/log/supervisor/backend.*.log

# Se rodando diretamente
# Os logs aparecerão no terminal
```

## 🐛 Solução de Problemas

### Erro: "connection refused"
- Verifique se o PostgreSQL está rodando
- Confirme a porta e as credenciais em `backend/.env`

### Erro: "database does not exist"
- Execute: `CREATE DATABASE escalas_distritais;` no psql

### Erro: "relation does not exist"
- Execute: `python scripts/init_database.py`

### Erro: "authentication failed"
- Verifique usuário/senha no arquivo `backend/.env`

## 📝 Estrutura dos Dados de Teste

### Usuários Criados
- **2 Pastores Distritais** (pastor1, pastor2)
- **2 Líderes de Igreja** (lider1, lider2)
- **8 Pregadores** (jose.silva, ana.costa, paulo.ferreira, etc.)

### Igrejas Criadas
- **Igreja Central** - Distrito Norte
- **Igreja do Bairro Alto** - Distrito Norte
- **Igreja Vila Nova** - Distrito Sul

### Horários de Culto Configurados
Cada igreja tem horários pré-configurados para testes de geração de escala.

## 🎯 Endpoints Principais Implementados

Total: **45 endpoints**

### Autenticação (3)
- POST `/api/auth/register`
- POST `/api/auth/login`
- GET `/api/auth/me`

### Distritos (5)
- GET `/api/districts`
- POST `/api/districts`
- GET `/api/districts/{id}`
- PUT `/api/districts/{id}`
- DELETE `/api/districts/{id}`

### Igrejas (5)
- GET `/api/churches`
- POST `/api/churches`
- GET `/api/churches/{id}`
- PUT `/api/churches/{id}`
- DELETE `/api/churches/{id}`

### Usuários (7)
- GET `/api/users`
- GET `/api/users/preachers`
- GET `/api/users/singers`
- POST `/api/users`
- GET `/api/users/{id}`
- PUT `/api/users/{id}`
- DELETE `/api/users/{id}`

### Escalas (12)
- GET `/api/schedules`
- POST `/api/schedules/generate-auto`
- POST `/api/schedules/manual`
- GET `/api/schedules/{id}`
- PUT `/api/schedules/{id}/items/{item_id}`
- POST `/api/schedules/{id}/confirm`
- POST `/api/schedule-items/{item_id}/confirm`
- POST `/api/schedule-items/{item_id}/refuse`
- POST `/api/schedule-items/{item_id}/cancel`
- POST `/api/schedule-items/{item_id}/volunteer`
- DELETE `/api/schedules/{id}`

### Avaliações (2)
- POST `/api/evaluations`
- GET `/api/evaluations/by-user/{user_id}`

### Notificações (3)
- GET `/api/notifications`
- PUT `/api/notifications/{id}/read`
- PUT `/api/notifications/mark-all-read`

### Substituições (4)
- POST `/api/substitutions`
- POST `/api/substitutions/{id}/accept`
- POST `/api/substitutions/{id}/reject`
- GET `/api/substitutions/pending`

### Delegações (3)
- POST `/api/delegations`
- GET `/api/delegations`
- DELETE `/api/delegations/{id}`

### Analytics (1)
- GET `/api/analytics/dashboard`

## ✅ Checklist de Validação

- [ ] PostgreSQL está rodando
- [ ] Banco de dados criado
- [ ] Tabelas criadas (10 tabelas)
- [ ] Dados de teste populados
- [ ] Backend iniciado sem erros
- [ ] Login funciona e retorna token
- [ ] Endpoints de listagem funcionam
- [ ] Endpoints de criação funcionam
- [ ] Autenticação JWT funciona

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do backend
2. Confirme as configurações do `backend/.env`
3. Teste a conexão com `test_connection.py`
4. Verifique se todas as dependências estão instaladas
