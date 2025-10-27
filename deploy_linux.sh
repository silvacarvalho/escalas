#!/bin/bash
# Script de Deploy Local para Linux/macOS
# Sistema de Escalas Distritais

echo "========================================"
echo " Sistema de Escalas Distritais"
echo " Script de Deploy Local - Linux/macOS"
echo "========================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERRO] Python3 não encontrado!${NC}"
    echo "Por favor, instale Python 3.9+ de https://www.python.org/downloads/"
    exit 1
fi

# Verificar se Node está instalado
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERRO] Node.js não encontrado!${NC}"
    echo "Por favor, instale Node.js de https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}[OK] Python e Node.js encontrados${NC}"
echo ""

# Verificar PostgreSQL
echo "Verificando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}[AVISO] PostgreSQL não encontrado no PATH${NC}"
    echo "Certifique-se de que o PostgreSQL está instalado e rodando"
    echo ""
else
    echo -e "${GREEN}[OK] PostgreSQL encontrado${NC}"
    echo ""
fi

echo "========================================"
echo " PASSO 1: Configurar Backend"
echo "========================================"
echo ""

cd backend

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Instalando dependências do backend..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo " PASSO 2: Configurar Banco de Dados"
echo "========================================"
echo ""

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[AVISO] Arquivo .env não encontrado!${NC}"
    echo "Criando .env com configurações padrão..."
    cat > .env << EOF
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/escalas_distritais"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET_KEY="sua-chave-secreta-super-segura-12345"
EOF
    echo ""
    echo -e "${YELLOW}[IMPORTANTE] Edite o arquivo backend/.env e configure:${NC}"
    echo "  - Senha do PostgreSQL"
    echo "  - Outras configurações conforme necessário"
    echo ""
    read -p "Pressione ENTER para continuar..."
fi

echo "Criando tabelas do banco de dados..."
cd ..
python3 scripts/init_database.py

echo ""
read -p "Deseja popular o banco com dados de teste? (s/N): " SEED
if [[ "$SEED" =~ ^[Ss]$ ]]; then
    python3 scripts/seed_database.py
fi

echo ""
echo "========================================"
echo " PASSO 3: Configurar Frontend"
echo "========================================"
echo ""

cd frontend

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "Criando .env do frontend..."
    echo 'REACT_APP_BACKEND_URL="http://localhost:8001"' > .env
fi

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo "Instalando dependências do frontend..."
    if [ -f "yarn.lock" ]; then
        yarn install
    else
        npm install
    fi
fi

echo ""
echo "========================================"
echo " DEPLOY CONCLUÍDO!"
echo "========================================"
echo ""
echo "Para iniciar o sistema, abra 2 terminais:"
echo ""
echo -e "${GREEN}TERMINAL 1 - Backend:${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo -e "${GREEN}TERMINAL 2 - Frontend:${NC}"
echo "  cd frontend"
echo "  npm start (ou yarn start)"
echo ""
echo "Depois acesse: http://localhost:3000"
echo ""
echo -e "${YELLOW}Credenciais de teste:${NC}"
echo "  Usuário: pastor1"
echo "  Senha: pastor123"
echo ""
