#!/usr/bin/env python3
"""
Script para testar a conexão com o PostgreSQL
"""
import sys
from pathlib import Path

# Adicionar backend ao path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from database import engine, SessionLocal
from sqlalchemy import text

def test_connection():
    print("🔍 Testando conexão com PostgreSQL...")
    
    try:
        # Testar conexão
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conexão estabelecida com sucesso!")
            print(f"📦 Versão do PostgreSQL: {version[:50]}...")
        
        # Testar sessão
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT current_database()"))
            database_name = result.fetchone()[0]
            print(f"✅ Sessão criada com sucesso!")
            print(f"🗄️  Banco de dados: {database_name}")
            
            # Listar tabelas
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📊 Tabelas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️  Nenhuma tabela encontrada. Execute 'python scripts/init_database.py' para criar as tabelas.")
            
        finally:
            db.close()
        
        print("\n✅ Teste de conexão concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao PostgreSQL:")
        print(f"   {str(e)}")
        print("\n💡 Certifique-se de que:")
        print("   1. O PostgreSQL está rodando em localhost:5432")
        print("   2. O banco de dados 'escalas_distritais' existe")
        print("   3. As credenciais em backend/.env estão corretas")
        print("   4. O usuário 'postgres' tem permissão de acesso")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
