#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from database import SessionLocal
from models import Usuario, Distrito, Igreja
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

print("🌱 Populando banco de dados...")

# Limpar dados existentes
print("🗑️  Limpando dados existentes...")
db.query(Usuario).delete()
db.query(Igreja).delete()
db.query(Distrito).delete()
db.commit()

# Criar Pastores
pastor1 = Usuario(nome_usuario="pastor1", senha_hash=pwd_context.hash("pastor123"), nome_completo="Pastor João Silva", email="pastor.joao@example.com", telefone="+5511999999999", funcao="pastor_distrital", eh_pregador=True, eh_cantor=False, pontuacao_pregacao=85.0)
pastor2 = Usuario(nome_usuario="pastor2", senha_hash=pwd_context.hash("pastor123"), nome_completo="Pastor Carlos Mendes", email="pastor.carlos@example.com", telefone="+5511988888888", funcao="pastor_distrital", eh_pregador=True, eh_cantor=False, pontuacao_pregacao=90.0)
db.add_all([pastor1, pastor2])
db.flush()

# Criar Distritos
distrito1 = Distrito(nome="Distrito Norte", id_pastor=pastor1.id)
distrito2 = Distrito(nome="Distrito Sul", id_pastor=pastor2.id)
db.add_all([distrito1, distrito2])
db.flush()

# Atualizar pastores com distrito
pastor1.id_distrito = distrito1.id
pastor2.id_distrito = distrito2.id
db.flush()

# Criar Igrejas
igreja1 = Igreja(nome="Igreja Central", id_distrito=distrito1.id, endereco="Rua Principal, 100", latitude=-23.550520, longitude=-46.633308, horarios_culto=[{"dia_semana": "quarta", "horario": "19:00"}, {"dia_semana": "sabado", "horario": "09:00"}])
igreja2 = Igreja(nome="Igreja do Bairro Alto", id_distrito=distrito1.id, endereco="Avenida das Flores, 250", latitude=-23.560520, longitude=-46.643308, horarios_culto=[{"dia_semana": "sabado", "horario": "10:00"}, {"dia_semana": "domingo", "horario": "19:00"}])
igreja3 = Igreja(nome="Igreja Vila Nova", id_distrito=distrito2.id, endereco="Rua das Acácias, 500", latitude=-23.570520, longitude=-46.653308, horarios_culto=[{"dia_semana": "quarta", "horario": "19:30"}, {"dia_semana": "sabado", "horario": "09:30"}])
db.add_all([igreja1, igreja2, igreja3])
db.flush()

# Criar Líderes
lider1 = Usuario(nome_usuario="lider1", senha_hash=pwd_context.hash("lider123"), nome_completo="Líder Maria Santos", email="maria.santos@example.com", telefone="+5511977777777", funcao="lider_igreja", id_distrito=distrito1.id, id_igreja=igreja1.id, eh_pregador=True, eh_cantor=True, pontuacao_pregacao=78.0, pontuacao_canto=82.0)
lider2 = Usuario(nome_usuario="lider2", senha_hash=pwd_context.hash("lider123"), nome_completo="Líder Pedro Oliveira", email="pedro.oliveira@example.com", telefone="+5511966666666", funcao="lider_igreja", id_distrito=distrito1.id, id_igreja=igreja2.id, eh_pregador=True, eh_cantor=False, pontuacao_pregacao=88.0)
db.add_all([lider1, lider2])
db.flush()

# Atualizar líderes das igrejas
igreja1.id_lider = lider1.id
igreja2.id_lider = lider2.id
db.flush()

# Criar Pregadores
pregadores_data = [
    ("jose.silva", "José Silva", 75.0, True),
    ("ana.costa", "Ana Costa", 92.0, False),
    ("paulo.ferreira", "Paulo Ferreira", 68.0, False),
    ("mariana.alves", "Mariana Alves", 85.0, True),
    ("ricardo.santos", "Ricardo Santos", 79.0, False),
    ("juliana.rodrigues", "Juliana Rodrigues", 90.0, True),
    ("fernando.lima", "Fernando Lima", 72.0, False),
    ("carla.martins", "Carla Martins", 81.0, False)
]

pregadores = []
for i, (username, nome, score, is_singer) in enumerate(pregadores_data):
    p = Usuario(
        nome_usuario=username,
        senha_hash=pwd_context.hash("pregador123"),
        nome_completo=nome,
        email=f"{username}@example.com",
        telefone=f"+55119{8000000 + i:07d}",
        funcao="pregador",
        id_distrito=distrito1.id,
        id_igreja=igreja1.id if i % 2 == 0 else igreja2.id,
        eh_pregador=True,
        eh_cantor=is_singer,
        pontuacao_pregacao=score,
        pontuacao_canto=50.0 + (score - 50) * 0.8 if is_singer else 50.0
    )
    pregadores.append(p)

db.add_all(pregadores)
db.commit()

print("✅ Banco de dados populado com sucesso!")
print("\n📋 Credenciais de Teste:")
print("=" * 50)
print("Pastor Distrital:")
print("  Usuário: pastor1")
print("  Senha: pastor123")
print("\nLíder de Igreja:")
print("  Usuário: lider1")
print("  Senha: lider123")
print("\nPregador:")
print("  Usuário: jose.silva")
print("  Senha: pregador123")
print("=" * 50)
print(f"\n📊 Estatísticas:")
print(f"  • {db.query(Distrito).count()} Distritos")
print(f"  • {db.query(Igreja).count()} Igrejas")
print(f"  • {db.query(Usuario).count()} Usuários")
print(f"  • {db.query(Usuario).filter(Usuario.eh_pregador == True).count()} Pregadores")
print(f"  • {db.query(Usuario).filter(Usuario.eh_cantor == True).count()} Cantores")

db.close()
