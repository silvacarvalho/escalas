@echo off
REM Script de Deploy Local para Windows
REM Sistema de Escalas Distritais

echo ========================================
echo  Sistema de Escalas Distritais
echo  Script de Deploy Local - Windows
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.9+ de https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar se Node está instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Node.js nao encontrado!
    echo Por favor, instale Node.js de https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python e Node.js encontrados
echo.

REM Verificar PostgreSQL
echo Verificando PostgreSQL...
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] PostgreSQL nao encontrado no PATH
    echo Certifique-se de que o PostgreSQL esta instalado e rodando
    echo.
)

echo ========================================
echo  PASSO 1: Configurar Backend
echo ========================================
echo.

cd backend

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo Criando ambiente virtual Python...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias do backend...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo  PASSO 2: Configurar Banco de Dados
echo ========================================
echo.

REM Verificar se .env existe
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado!
    echo Criando .env com configuracoes padrao...
    (
        echo DATABASE_URL="postgresql://postgres:postgres@localhost:5432/escalas_distritais"
        echo CORS_ORIGINS="http://localhost:3000"
        echo JWT_SECRET_KEY="sua-chave-secreta-super-segura-12345"
    ) > .env
    echo.
    echo [IMPORTANTE] Edite o arquivo backend/.env e configure:
    echo   - Senha do PostgreSQL
    echo   - Outras configuracoes conforme necessario
    echo.
    pause
)

echo Criando tabelas do banco de dados...
cd ..
python scripts\init_database.py

echo.
echo Deseja popular o banco com dados de teste? (S/N)
set /p SEED=
if /i "%SEED%"=="S" (
    python scripts\seed_database.py
)

echo.
echo ========================================
echo  PASSO 3: Configurar Frontend
echo ========================================
echo.

cd frontend

REM Verificar se .env existe
if not exist ".env" (
    echo Criando .env do frontend...
    echo REACT_APP_BACKEND_URL="http://localhost:8001" > .env
)

REM Verificar se node_modules existe
if not exist "node_modules" (
    echo Instalando dependencias do frontend...
    if exist "yarn.lock" (
        call yarn install
    ) else (
        call npm install
    )
)

echo.
echo ========================================
echo  DEPLOY CONCLUIDO!
echo ========================================
echo.
echo Para iniciar o sistema, abra 2 terminais:
echo.
echo TERMINAL 1 - Backend:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
echo.
echo TERMINAL 2 - Frontend:
echo   cd frontend
echo   npm start (ou yarn start)
echo.
echo Depois acesse: http://localhost:3000
echo.
echo Credenciais de teste:
echo   Usuario: pastor1
echo   Senha: pastor123
echo.
pause
