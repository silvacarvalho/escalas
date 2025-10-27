#!/usr/bin/env python3
"""
Script para criar todas as tabelas no PostgreSQL
"""
import sys
from pathlib import Path

# Adicionar backend ao path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from database import engine, Base
from models import (
    Usuario, Distrito, Igreja, Escala, ItemEscala,
    Avaliacao, Notificacao, SolicitacaoTroca, Delegacao, LogAuditoria
)

def init_database():
    print("🔧 Iniciando criação do banco de dados PostgreSQL...")
    print("📋 Criando tabelas...")
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    print("✅ Banco de dados criado com sucesso!")
    print("\n📊 Tabelas criadas:")
    print("  - usuarios")
    print("  - distritos")
    print("  - igrejas")
    print("  - escalas")
    print("  - itens_escala")
    print("  - avaliacoes")
    print("  - notificacoes")
    print("  - solicitacoes_troca")
    print("  - delegacoes")
    print("  - logs_auditoria")
    print("\n🎉 Sistema pronto para uso!")

if __name__ == "__main__":
    init_database()
