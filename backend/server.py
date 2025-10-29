from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import calendar

from database import get_db
from models import Usuario, Distrito, Igreja, Escala, ItemEscala, Avaliacao, Notificacao, SolicitacaoTroca, Delegacao

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="Sistema de Escalas Distritais")
api_router = APIRouter(prefix="/api")

# Pydantic Models
class HorarioCulto(BaseModel):
    dia_semana: str
    horario: str

class UsuarioBase(BaseModel):
    nome_usuario: str
    nome_completo: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    funcao: str
    id_distrito: Optional[str] = None
    id_igreja: Optional[str] = None
    eh_pregador: bool = False
    eh_cantor: bool = False

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome_usuario: str
    nome_completo: str
    email: Optional[str]
    telefone: Optional[str]
    funcao: str
    id_distrito: Optional[str]
    id_igreja: Optional[str]
    eh_pregador: bool
    eh_cantor: bool
    pontuacao_pregacao: float
    pontuacao_canto: float
    periodos_indisponibilidade: List[Dict] = []
    criado_em: datetime
    atualizado_em: datetime
    ativo: bool

class UsuarioLogin(BaseModel):
    nome_usuario: str
    senha: str

class DistritoCreate(BaseModel):
    nome: str
    id_pastor: str

class DistritoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome: str
    id_pastor: str
    criado_em: datetime
    atualizado_em: datetime
    ativo: bool

class IgrejaCreate(BaseModel):
    nome: str
    id_distrito: str
    endereco: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    id_lider: Optional[str] = None
    horarios_culto: List[Dict] = []

class IgrejaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome: str
    id_distrito: str
    endereco: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    id_lider: Optional[str]
    horarios_culto: List[Dict] = []
    criado_em: datetime
    atualizado_em: datetime
    ativo: bool

class ItemEscalaData(BaseModel):
    id: str
    data: str
    horario: str
    id_pregador: Optional[str] = None
    ids_cantores: List[str] = []
    status: str
    motivo_recusa: Optional[str] = None
    confirmado_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None

class EscalaCreate(BaseModel):
    mes: int
    ano: int
    id_igreja: str
    modo_geracao: str

class EscalaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    mes: int
    ano: int
    id_igreja: str
    id_distrito: str
    id_gerado_por: Optional[str]
    modo_geracao: str
    status: str
    itens: List[ItemEscalaData] = []
    criado_em: datetime
    atualizado_em: datetime

class AvaliacaoCreate(BaseModel):
    id_item_escala: str
    id_igreja: str
    tipo_membro: str
    id_usuario_avaliado: str
    nota: int
    comentario: Optional[str] = None

class AvaliacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    id_item_escala: str
    id_igreja: str
    tipo_membro: str
    id_usuario_avaliado: str
    nota: int
    comentario: Optional[str]
    criado_em: datetime

class NotificacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    id_usuario: str
    tipo: str
    titulo: str
    mensagem: str
    id_relacionado: Optional[str]
    status: str
    criado_em: datetime

class SolicitacaoTrocaCreate(BaseModel):
    id_item_escala_original: str
    id_escala: str
    id_usuario_alvo: str
    motivo: str

class DelegacaoCreate(BaseModel):
    id_distrito: str
    id_usuario: str
    permissoes: List[str]

# Auth utilities
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Usuario:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(Usuario).filter(Usuario.id == user_id, Usuario.ativo == True).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper functions
def criar_notificacao(db: Session, id_usuario: str, tipo: str, titulo: str, mensagem: str, id_relacionado: Optional[str] = None):
    notificacao = Notificacao(id_usuario=id_usuario, tipo=tipo, titulo=titulo, mensagem=mensagem, id_relacionado=id_relacionado)
    db.add(notificacao)
    db.commit()

def enviar_notificacao_mock(telefone: str, mensagem: str):
    logging.info(f"[MOCK SMS/WhatsApp para {telefone}]: {mensagem}")

def usuario_disponivel(db: Session, id_usuario: str, data: str) -> bool:
    user = db.query(Usuario).filter(Usuario.id == id_usuario).first()
    if not user or not user.periodos_indisponibilidade:
        return True
    for periodo in user.periodos_indisponibilidade:
        if periodo.get('data_inicio', '') <= data <= periodo.get('data_fim', ''):
            return False
    return True

def slot_ocupado(db: Session, id_usuario: str, data: str) -> bool:
    escalas = db.query(Escala).filter(Escala.status.in_(['confirmada', 'ativa'])).all()
    for escala in escalas:
        itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id, ItemEscala.data == data, ItemEscala.status.in_(['confirmado', 'pendente'])).all()
        for item in itens:
            if item.id_pregador == id_usuario or id_usuario in (item.ids_cantores or []):
                return True
    return False

# AUTH ROUTES
@api_router.post("/auth/register", response_model=UsuarioResponse)
async def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(Usuario.nome_usuario == user_data.nome_usuario).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_dict = user_data.model_dump()
    senha = user_dict.pop('senha')
    user = Usuario(**user_dict, senha_hash=hash_password(senha))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@api_router.post("/auth/login")
async def login(credentials: UsuarioLogin, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.nome_usuario == credentials.nome_usuario, Usuario.ativo == True).first()
    if not user or not verify_password(credentials.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.id})
    user_dict = {"id": user.id, "nome_usuario": user.nome_usuario, "nome_completo": user.nome_completo, "email": user.email, "telefone": user.telefone, "funcao": user.funcao, "id_distrito": user.id_distrito, "id_igreja": user.id_igreja, "eh_pregador": user.eh_pregador, "eh_cantor": user.eh_cantor, "pontuacao_pregacao": user.pontuacao_pregacao, "pontuacao_canto": user.pontuacao_canto}
    return {"access_token": token, "token_type": "bearer", "user": user_dict}

@api_router.get("/auth/me", response_model=UsuarioResponse)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user

@api_router.put("/auth/me", response_model=UsuarioResponse)
async def update_me(updates: Dict[str, Any], current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed_fields = ['nome_completo', 'email', 'telefone', 'periodos_indisponibilidade']
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(current_user, key, value)
    current_user.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return current_user

# DISTRICTS
@api_router.get("/districts", response_model=List[DistritoResponse])
async def get_districts(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao == 'pastor_distrital':
        return db.query(Distrito).filter(Distrito.ativo == True).all()
    return db.query(Distrito).filter(Distrito.id == current_user.id_distrito, Distrito.ativo == True).all()

@api_router.post("/districts", response_model=DistritoResponse)
async def create_district(district_data: DistritoCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can create districts")
    district = Distrito(**district_data.model_dump())
    db.add(district)
    db.commit()
    db.refresh(district)
    return district

@api_router.get("/districts/{district_id}", response_model=DistritoResponse)
async def get_district(district_id: str, db: Session = Depends(get_db)):
    district = db.query(Distrito).filter(Distrito.id == district_id, Distrito.ativo == True).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district

@api_router.put("/districts/{district_id}", response_model=DistritoResponse)
async def update_district(district_id: str, updates: Dict[str, Any], current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Permission denied")
    district = db.query(Distrito).filter(Distrito.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    for key, value in updates.items():
        if hasattr(district, key):
            setattr(district, key, value)
    district.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(district)
    return district

@api_router.delete("/districts/{district_id}")
async def delete_district(district_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Permission denied")
    district = db.query(Distrito).filter(Distrito.id == district_id).first()
    if district:
        district.ativo = False
        db.commit()
    return {"message": "District deleted successfully"}

# CHURCHES
@api_router.get("/churches", response_model=List[IgrejaResponse])
async def get_churches(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Igreja).filter(Igreja.ativo == True)
    if id_distrito:
        query = query.filter(Igreja.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Igreja.id_distrito == current_user.id_distrito)
    return query.all()

@api_router.post("/churches", response_model=IgrejaResponse)
async def create_church(church_data: IgrejaCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    church = Igreja(**church_data.model_dump())
    db.add(church)
    db.commit()
    db.refresh(church)
    return church

@api_router.get("/churches/{church_id}", response_model=IgrejaResponse)
async def get_church(church_id: str, db: Session = Depends(get_db)):
    church = db.query(Igreja).filter(Igreja.id == church_id, Igreja.ativo == True).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church

@api_router.put("/churches/{church_id}", response_model=IgrejaResponse)
async def update_church(church_id: str, updates: Dict[str, Any], current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    church = db.query(Igreja).filter(Igreja.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    for key, value in updates.items():
        if hasattr(church, key):
            setattr(church, key, value)
    church.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(church)
    return church

@api_router.delete("/churches/{church_id}")
async def delete_church(church_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    church = db.query(Igreja).filter(Igreja.id == church_id).first()
    if church:
        church.ativo = False
        db.commit()
    return {"message": "Church deleted successfully"}

# USERS
@api_router.get("/users", response_model=List[UsuarioResponse])
async def get_users(id_distrito: Optional[str] = None, id_igreja: Optional[str] = None, eh_pregador: Optional[bool] = None, eh_cantor: Optional[bool] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(Usuario.ativo == True)
    if current_user.funcao != 'pastor_distrital':
        query = query.filter(Usuario.id_distrito == current_user.id_distrito)
    if id_distrito:
        query = query.filter(Usuario.id_distrito == id_distrito)
    if id_igreja:
        query = query.filter(Usuario.id_igreja == id_igreja)
    if eh_pregador is not None:
        query = query.filter(Usuario.eh_pregador == eh_pregador)
    if eh_cantor is not None:
        query = query.filter(Usuario.eh_cantor == eh_cantor)
    return query.all()

@api_router.get("/users/preachers", response_model=List[UsuarioResponse])
async def get_preachers(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(Usuario.ativo == True, Usuario.eh_pregador == True)
    if id_distrito:
        query = query.filter(Usuario.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Usuario.id_distrito == current_user.id_distrito)
    return query.all()

@api_router.get("/users/singers", response_model=List[UsuarioResponse])
async def get_singers(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(Usuario.ativo == True, Usuario.eh_cantor == True)
    if id_distrito:
        query = query.filter(Usuario.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Usuario.id_distrito == current_user.id_distrito)
    return query.all()

@api_router.post("/users", response_model=UsuarioResponse)
async def create_user(user_data: UsuarioCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    existing = db.query(Usuario).filter(Usuario.nome_usuario == user_data.nome_usuario).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_dict = user_data.model_dump()
    senha = user_dict.pop('senha')
    user = Usuario(**user_dict, senha_hash=hash_password(senha))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@api_router.get("/users/{user_id}", response_model=UsuarioResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id == user_id, Usuario.ativo == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/users/{user_id}", response_model=UsuarioResponse)
async def update_user(user_id: str, updates: Dict[str, Any], current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja'] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates.pop('senha', None)
    updates.pop('senha_hash', None)
    for key, value in updates.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user:
        user.ativo = False
        db.commit()
    return {"message": "User deleted successfully"}

# SCHEDULES
@api_router.get("/schedules", response_model=List[EscalaResponse])
async def get_schedules(mes: Optional[int] = None, ano: Optional[int] = None, id_igreja: Optional[str] = None, id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Escala)
    if current_user.funcao != 'pastor_distrital':
        query = query.filter(Escala.id_distrito == current_user.id_distrito)
    if mes:
        query = query.filter(Escala.mes == mes)
    if ano:
        query = query.filter(Escala.ano == ano)
    if id_igreja:
        query = query.filter(Escala.id_igreja == id_igreja)
    if id_distrito:
        query = query.filter(Escala.id_distrito == id_distrito)
    escalas = query.all()
    result = []
    for escala in escalas:
        itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
        result.append(EscalaResponse(id=escala.id, mes=escala.mes, ano=escala.ano, id_igreja=escala.id_igreja, id_distrito=escala.id_distrito, id_gerado_por=escala.id_gerado_por, modo_geracao=escala.modo_geracao, status=escala.status, criado_em=escala.criado_em, atualizado_em=escala.atualizado_em, itens=[ItemEscalaData(id=item.id, data=item.data, horario=item.horario, id_pregador=item.id_pregador, ids_cantores=item.ids_cantores or [], status=item.status, motivo_recusa=item.motivo_recusa, confirmado_em=item.confirmado_em, cancelado_em=item.cancelado_em) for item in itens]))
    return result

@api_router.post("/schedules/generate-auto")
async def generate_schedule_auto(mes: int, ano: int, id_distrito: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    igrejas = db.query(Igreja).filter(Igreja.id_distrito == id_distrito, Igreja.ativo == True).all()
    pregadores = db.query(Usuario).filter(Usuario.id_distrito == id_distrito, Usuario.eh_pregador == True, Usuario.ativo == True).order_by(Usuario.pontuacao_pregacao.desc()).all()
    escalas_geradas = []
    for igreja in igrejas:
        existing = db.query(Escala).filter(Escala.id_igreja == igreja.id, Escala.mes == mes, Escala.ano == ano).first()
        if existing:
            continue
        escala = Escala(mes=mes, ano=ano, id_igreja=igreja.id, id_distrito=id_distrito, id_gerado_por=current_user.id, modo_geracao='automatico', status='rascunho')
        db.add(escala)
        db.flush()
        horarios_culto = igreja.horarios_culto or []
        if not horarios_culto:
            continue
        _, num_dias = calendar.monthrange(ano, mes)
        pregador_index = 0
        for dia in range(1, num_dias + 1):
            date_obj = datetime(ano, mes, dia)
            dia_semana = date_obj.strftime('%A').lower()
            dia_semana_map = {'monday': 'segunda', 'tuesday': 'terca', 'wednesday': 'quarta', 'thursday': 'quinta', 'friday': 'sexta', 'saturday': 'sabado', 'sunday': 'domingo'}
            dia_semana_pt = dia_semana_map.get(dia_semana, dia_semana)
            horario_encontrado = None
            for horario in horarios_culto:
                if horario.get('dia_semana', '').lower() in [dia_semana, dia_semana_pt]:
                    horario_encontrado = horario
                    break
            if horario_encontrado:
                data_str = date_obj.strftime('%Y-%m-%d')
                pregador = None
                tentativas = 0
                while tentativas < len(pregadores):
                    candidato = pregadores[pregador_index % len(pregadores)]
                    pregador_index += 1
                    tentativas += 1
                    if usuario_disponivel(db, candidato.id, data_str) and not slot_ocupado(db, candidato.id, data_str):
                        pregador = candidato
                        break
                if pregador:
                    item = ItemEscala(id_escala=escala.id, data=data_str, horario=horario_encontrado.get('horario', ''), id_pregador=pregador.id, ids_cantores=[], status='pendente')
                    db.add(item)
        escalas_geradas.append(escala)
    db.commit()
    return {"message": f"Geradas {len(escalas_geradas)} escalas", "escalas": [e.id for e in escalas_geradas]}

@api_router.post("/schedules/manual", response_model=EscalaResponse)
async def create_manual_schedule(schedule_data: EscalaCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    existing = db.query(Escala).filter(Escala.id_igreja == schedule_data.id_igreja, Escala.mes == schedule_data.mes, Escala.ano == schedule_data.ano).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists for this month/year")
    igreja = db.query(Igreja).filter(Igreja.id == schedule_data.id_igreja).first()
    if not igreja:
        raise HTTPException(status_code=404, detail="Church not found")
    escala = Escala(mes=schedule_data.mes, ano=schedule_data.ano, id_igreja=schedule_data.id_igreja, id_distrito=igreja.id_distrito, id_gerado_por=current_user.id, modo_geracao='manual', status='rascunho')
    db.add(escala)
    db.flush()
    horarios_culto = igreja.horarios_culto or []
    _, num_dias = calendar.monthrange(schedule_data.ano, schedule_data.mes)
    for dia in range(1, num_dias + 1):
        date_obj = datetime(schedule_data.ano, schedule_data.mes, dia)
        dia_semana = date_obj.strftime('%A').lower()
        horario_encontrado = None
        for horario in horarios_culto:
            if horario.get('dia_semana', '').lower() == dia_semana:
                horario_encontrado = horario
                break
        if horario_encontrado:
            item = ItemEscala(id_escala=escala.id, data=date_obj.strftime('%Y-%m-%d'), horario=horario_encontrado.get('horario', ''), id_pregador=None, ids_cantores=[], status='pendente')
            db.add(item)
    db.commit()
    db.refresh(escala)
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
    return EscalaResponse(id=escala.id, mes=escala.mes, ano=escala.ano, id_igreja=escala.id_igreja, id_distrito=escala.id_distrito, id_gerado_por=escala.id_gerado_por, modo_geracao=escala.modo_geracao, status=escala.status, criado_em=escala.criado_em, atualizado_em=escala.atualizado_em, itens=[ItemEscalaData(id=item.id, data=item.data, horario=item.horario, id_pregador=item.id_pregador, ids_cantores=item.ids_cantores or [], status=item.status, motivo_recusa=item.motivo_recusa, confirmado_em=item.confirmado_em, cancelado_em=item.cancelado_em) for item in itens])

@api_router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Schedule not found")
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == escala.id).all()
    return EscalaResponse(id=escala.id, mes=escala.mes, ano=escala.ano, id_igreja=escala.id_igreja, id_distrito=escala.id_distrito, id_gerado_por=escala.id_gerado_por, modo_geracao=escala.modo_geracao, status=escala.status, criado_em=escala.criado_em, atualizado_em=escala.atualizado_em, itens=[ItemEscalaData(id=item.id, data=item.data, horario=item.horario, id_pregador=item.id_pregador, ids_cantores=item.ids_cantores or [], status=item.status, motivo_recusa=item.motivo_recusa, confirmado_em=item.confirmado_em, cancelado_em=item.cancelado_em) for item in itens])

@api_router.put("/schedules/{schedule_id}/items/{item_id}")
async def update_schedule_item(schedule_id: str, item_id: str, id_pregador: Optional[str] = None, ids_cantores: Optional[List[str]] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id, ItemEscala.id_escala == schedule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if id_pregador is not None:
        if slot_ocupado(db, id_pregador, item.data):
            raise HTTPException(status_code=400, detail="Preacher already scheduled on this date")
        item.id_pregador = id_pregador
    if ids_cantores is not None:
        for cantor_id in ids_cantores:
            if slot_ocupado(db, cantor_id, item.data):
                raise HTTPException(status_code=400, detail=f"Singer {cantor_id} already scheduled on this date")
        item.ids_cantores = ids_cantores
    item.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Schedule item updated"}

@api_router.post("/schedules/{schedule_id}/confirm")
async def confirm_schedule(schedule_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Schedule not found")
    itens = db.query(ItemEscala).filter(ItemEscala.id_escala == schedule_id).all()
    for item in itens:
        if not item.id_pregador:
            raise HTTPException(status_code=400, detail=f"Item on {item.data} has no preacher assigned")
    escala.status = 'confirmada'
    escala.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    igreja = db.query(Igreja).filter(Igreja.id == escala.id_igreja).first()
    for item in itens:
        if item.id_pregador:
            pregador = db.query(Usuario).filter(Usuario.id == item.id_pregador).first()
            if pregador:
                mensagem = f"Você foi escalado para pregar em {igreja.nome} no dia {item.data} às {item.horario}"
                criar_notificacao(db, pregador.id, 'atribuicao_escala', 'Nova Escala de Pregação', mensagem, item.id)
                if pregador.telefone:
                    enviar_notificacao_mock(pregador.telefone, mensagem)
        for cantor_id in (item.ids_cantores or []):
            cantor = db.query(Usuario).filter(Usuario.id == cantor_id).first()
            if cantor:
                mensagem = f"Você foi escalado para Louvor Especial em {igreja.nome} no dia {item.data} às {item.horario}"
                criar_notificacao(db, cantor.id, 'atribuicao_escala', 'Nova Escala de Louvor', mensagem, item.id)
                if cantor.telefone:
                    enviar_notificacao_mock(cantor.telefone, mensagem)
    return {"message": "Schedule confirmed and notifications sent"}

@api_router.post("/schedule-items/{item_id}/confirm")
async def confirm_participation(item_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if item.id_pregador != current_user.id and current_user.id not in (item.ids_cantores or []):
        raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
    item.status = 'confirmado'
    item.confirmado_em = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Participation confirmed"}

@api_router.post("/schedule-items/{item_id}/refuse")
async def refuse_participation(item_id: str, motivo: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    escala = db.query(Escala).filter(Escala.id == item.id_escala).first()
    igreja = db.query(Igreja).filter(Igreja.id == escala.id_igreja).first()
    distrito = db.query(Distrito).filter(Distrito.id == escala.id_distrito).first()
    tipo_membro = 'pregador' if item.id_pregador == current_user.id else 'cantor'
    if item.id_pregador == current_user.id:
        item.id_pregador = None
    elif current_user.id in (item.ids_cantores or []):
        item.ids_cantores.remove(current_user.id)
    else:
        raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
    item.status = 'recusado'
    item.motivo_recusa = motivo
    db.commit()
    pastor = db.query(Usuario).filter(Usuario.id == distrito.id_pastor).first()
    if pastor:
        mensagem = f"{current_user.nome_completo} ({tipo_membro}) recusou a escala em {igreja.nome} no dia {item.data} às {item.horario}. Motivo: {motivo}"
        criar_notificacao(db, pastor.id, 'recusa_escala', 'Recusa de Escala', mensagem, item_id)
        if pastor.telefone:
            enviar_notificacao_mock(pastor.telefone, mensagem)
    if igreja.id_lider:
        lider = db.query(Usuario).filter(Usuario.id == igreja.id_lider).first()
        if lider:
            criar_notificacao(db, lider.id, 'recusa_escala', 'Recusa de Escala', mensagem, item_id)
    return {"message": "Participation refused"}

@api_router.post("/schedule-items/{item_id}/cancel")
async def cancel_participation(item_id: str, motivo: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    item_date = datetime.fromisoformat(item.data)
    days_until = (item_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
    if days_until < 2:
        raise HTTPException(status_code=400, detail="Cannot cancel within 2 days of the service")
    if item.status != 'confirmado':
        raise HTTPException(status_code=400, detail="Can only cancel confirmed participation")
    item.status = 'cancelado'
    item.cancelado_em = datetime.now(timezone.utc)
    item.motivo_recusa = motivo
    if item.id_pregador == current_user.id:
        item.id_pregador = None
    elif current_user.id in (item.ids_cantores or []):
        item.ids_cantores.remove(current_user.id)
    db.commit()
    return {"message": "Participation cancelled"}

@api_router.post("/schedule-items/{item_id}/volunteer")
async def volunteer_for_slot(item_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ItemEscala).filter(ItemEscala.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if item.id_pregador:
        raise HTTPException(status_code=400, detail="Slot is already filled")
    if not usuario_disponivel(db, current_user.id, item.data):
        raise HTTPException(status_code=400, detail="You are not available on this date")
    if slot_ocupado(db, current_user.id, item.data):
        raise HTTPException(status_code=400, detail="You are already scheduled on this date")
    if current_user.eh_pregador:
        item.id_pregador = current_user.id
        item.status = 'confirmado'
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="You must be a preacher to volunteer")
    return {"message": "Successfully volunteered for slot"}

@api_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    escala = db.query(Escala).filter(Escala.id == schedule_id).first()
    if escala:
        db.query(ItemEscala).filter(ItemEscala.id_escala == schedule_id).delete()
        db.delete(escala)
        db.commit()
    return {"message": "Schedule deleted successfully"}

# EVALUATIONS
@api_router.post("/evaluations", response_model=AvaliacaoResponse)
async def create_evaluation(eval_data: AvaliacaoCreate, db: Session = Depends(get_db)):
    evaluation = Avaliacao(**eval_data.model_dump())
    db.add(evaluation)
    db.commit()
    user = db.query(Usuario).filter(Usuario.id == eval_data.id_usuario_avaliado).first()
    if user:
        score_field = 'pontuacao_pregacao' if eval_data.tipo_membro == 'pregador' else 'pontuacao_canto'
        current_score = getattr(user, score_field, 50.0)
        rating_impact = (eval_data.nota - 3) * 2
        new_score = max(0, min(100, current_score + rating_impact))
        setattr(user, score_field, new_score)
        db.commit()
    db.refresh(evaluation)
    return evaluation

@api_router.get("/evaluations/by-user/{user_id}", response_model=List[AvaliacaoResponse])
async def get_evaluations_by_user(user_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Avaliacao).filter(Avaliacao.id_usuario_avaliado == user_id).all()

# NOTIFICATIONS
@api_router.get("/notifications", response_model=List[NotificacaoResponse])
async def get_notifications(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notificacao).filter(Notificacao.id_usuario == current_user.id).order_by(Notificacao.criado_em.desc()).limit(100).all()

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notificacao).filter(Notificacao.id == notification_id, Notificacao.id_usuario == current_user.id).first()
    if notif:
        notif.status = "lida"
        db.commit()
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notificacao).filter(Notificacao.id_usuario == current_user.id, Notificacao.status == "nao_lida").update({"status": "lida"})
    db.commit()
    return {"message": "All notifications marked as read"}

# SUBSTITUTIONS
@api_router.post("/substitutions")
async def create_substitution_request(sub_data: SolicitacaoTrocaCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    substitution = SolicitacaoTroca(**sub_data.model_dump(), id_solicitante=current_user.id)
    db.add(substitution)
    db.commit()
    criar_notificacao(db, sub_data.id_usuario_alvo, 'solicitacao_troca', 'Solicitação de Troca de Escala', f"{current_user.nome_completo} solicitou trocar a escala com você. Motivo: {sub_data.motivo}", substitution.id)
    return {"message": "Substitution request created"}

@api_router.post("/substitutions/{sub_id}/accept")
async def accept_substitution(sub_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(SolicitacaoTroca).filter(SolicitacaoTroca.id == sub_id).first()
    if not sub or sub.id_usuario_alvo != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    sub.status = "aceita"
    sub.respondido_em = datetime.now(timezone.utc)
    item = db.query(ItemEscala).filter(ItemEscala.id == sub.id_item_escala_original).first()
    if item:
        if item.id_pregador == sub.id_solicitante:
            item.id_pregador = current_user.id
        elif sub.id_solicitante in (item.ids_cantores or []):
            item.ids_cantores.remove(sub.id_solicitante)
            item.ids_cantores.append(current_user.id)
    db.commit()
    criar_notificacao(db, sub.id_solicitante, 'troca_aceita', 'Troca Aceita', f"Sua solicitação de troca foi aceita por {current_user.nome_completo}", sub_id)
    return {"message": "Substitution accepted"}

@api_router.post("/substitutions/{sub_id}/reject")
async def reject_substitution(sub_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(SolicitacaoTroca).filter(SolicitacaoTroca.id == sub_id).first()
    if not sub or sub.id_usuario_alvo != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    sub.status = "rejeitada"
    sub.respondido_em = datetime.now(timezone.utc)
    db.commit()
    criar_notificacao(db, sub.id_solicitante, 'troca_rejeitada', 'Troca Recusada', f"Sua solicitação de troca foi recusada por {current_user.nome_completo}", sub_id)
    return {"message": "Substitution rejected"}

@api_router.get("/substitutions/pending")
async def get_pending_substitutions(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SolicitacaoTroca).filter(SolicitacaoTroca.id_usuario_alvo == current_user.id, SolicitacaoTroca.status == "pendente").all()

# DELEGATIONS
@api_router.post("/delegations")
async def create_delegation(delegation_data: DelegacaoCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can delegate")
    delegation = Delegacao(**delegation_data.model_dump(), id_delegado_por=current_user.id)
    db.add(delegation)
    db.commit()
    return {"message": "Delegation created"}

@api_router.get("/delegations")
async def get_delegations(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Delegacao).filter(Delegacao.ativo == True)
    if id_distrito:
        query = query.filter(Delegacao.id_distrito == id_distrito)
    return query.all()

@api_router.delete("/delegations/{delegation_id}")
async def delete_delegation(delegation_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Permission denied")
    delegation = db.query(Delegacao).filter(Delegacao.id == delegation_id).first()
    if delegation:
        delegation.ativo = False
        db.commit()
    return {"message": "Delegation deleted"}

# ANALYTICS
@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard(id_distrito: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Permission denied")
    total_churches = db.query(Igreja).filter(Igreja.id_distrito == id_distrito, Igreja.ativo == True).count()
    total_preachers = db.query(Usuario).filter(Usuario.id_distrito == id_distrito, Usuario.eh_pregador == True, Usuario.ativo == True).count()
    total_singers = db.query(Usuario).filter(Usuario.id_distrito == id_distrito, Usuario.eh_cantor == True, Usuario.ativo == True).count()
    preachers = db.query(Usuario).filter(Usuario.id_distrito == id_distrito, Usuario.eh_pregador == True, Usuario.ativo == True).order_by(Usuario.pontuacao_pregacao.desc()).limit(10).all()
    evaluations = db.query(Avaliacao).order_by(Avaliacao.criado_em.desc()).limit(20).all()
    return {"total_churches": total_churches, "total_preachers": total_preachers, "total_singers": total_singers, "top_preachers": preachers, "recent_evaluations": evaluations}

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
