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
from enum import Enum
import calendar

from database import get_db, engine, Base
from models import (
    Usuario, Distrito, Igreja, Escala, ItemEscala,
    Avaliacao, Notificacao, SolicitacaoTroca, Delegacao
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Sistema de Escalas Distritais")
api_router = APIRouter(prefix="/api")

# ===== PYDANTIC MODELS =====

class HorarioCulto(BaseModel):
    dia_semana: str
    horario: str

class PeriodoIndisponibilidade(BaseModel):
    data_inicio: str
    data_fim: str
    motivo: str

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

# ===== AUTH UTILITIES =====

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

# ===== HELPER FUNCTIONS =====

def criar_notificacao(db: Session, id_usuario: str, tipo: str, titulo: str, mensagem: str, id_relacionado: Optional[str] = None):
    notificacao = Notificacao(
        id_usuario=id_usuario,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        id_relacionado=id_relacionado
    )
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
        itens = db.query(ItemEscala).filter(
            ItemEscala.id_escala == escala.id,
            ItemEscala.data == data,
            ItemEscala.status.in_(['confirmado', 'pendente'])
        ).all()
        for item in itens:
            if item.id_pregador == id_usuario:
                return True
            if id_usuario in (item.ids_cantores or []):
                return True
    return False

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=UsuarioResponse)
async def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(Usuario.nome_usuario == user_data.nome_usuario).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_dict = user_data.model_dump()
    senha = user_dict.pop('senha')
    
    user = Usuario(
        **user_dict,
        senha_hash=hash_password(senha)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@api_router.post("/auth/login")
async def login(credentials: UsuarioLogin, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(
        Usuario.nome_usuario == credentials.nome_usuario,
        Usuario.ativo == True
    ).first()
    
    if not user or not verify_password(credentials.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.id})
    
    user_dict = {
        "id": user.id,
        "nome_usuario": user.nome_usuario,
        "nome_completo": user.nome_completo,
        "email": user.email,
        "telefone": user.telefone,
        "funcao": user.funcao,
        "id_distrito": user.id_distrito,
        "id_igreja": user.id_igreja,
        "eh_pregador": user.eh_pregador,
        "eh_cantor": user.eh_cantor,
        "pontuacao_pregacao": user.pontuacao_pregacao,
        "pontuacao_canto": user.pontuacao_canto
    }
    
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

# ===== DISTRICT ROUTES =====

@api_router.get("/districts", response_model=List[DistritoResponse])
async def get_districts(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao == 'pastor_distrital':
        districts = db.query(Distrito).filter(Distrito.ativo == True).all()
    else:
        districts = db.query(Distrito).filter(
            Distrito.id == current_user.id_distrito,
            Distrito.ativo == True
        ).all()
    return districts

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
async def get_district(district_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    district = db.query(Distrito).filter(Distrito.id == district_id, Distrito.ativo == True).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district

@api_router.put("/districts/{district_id}", response_model=DistritoResponse)
async def update_district(district_id: str, updates: Dict[str, Any], current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can update districts")
    
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
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can delete districts")
    
    district = db.query(Distrito).filter(Distrito.id == district_id).first()
    if district:
        district.ativo = False
        db.commit()
    
    return {"message": "District deleted successfully"}

# ===== CHURCH ROUTES =====

@api_router.get("/churches", response_model=List[IgrejaResponse])
async def get_churches(
    id_distrito: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Igreja).filter(Igreja.ativo == True)
    
    if id_distrito:
        query = query.filter(Igreja.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Igreja.id_distrito == current_user.id_distrito)
    
    churches = query.all()
    return churches

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

# ===== USER ROUTES =====

@api_router.get("/users", response_model=List[UsuarioResponse])
async def get_users(
    id_distrito: Optional[str] = None,
    id_igreja: Optional[str] = None,
    eh_pregador: Optional[bool] = None,
    eh_cantor: Optional[bool] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    
    users = query.all()
    return users

@api_router.get("/users/preachers", response_model=List[UsuarioResponse])
async def get_preachers(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(Usuario.ativo == True, Usuario.eh_pregador == True)
    
    if id_distrito:
        query = query.filter(Usuario.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Usuario.id_distrito == current_user.id_distrito)
    
    preachers = query.all()
    return preachers

@api_router.get("/users/singers", response_model=List[UsuarioResponse])
async def get_singers(id_distrito: Optional[str] = None, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(Usuario.ativo == True, Usuario.eh_cantor == True)
    
    if id_distrito:
        query = query.filter(Usuario.id_distrito == id_distrito)
    elif current_user.funcao != 'pastor_distrital':
        query = query.filter(Usuario.id_distrito == current_user.id_distrito)
    
    singers = query.all()
    return singers

@api_router.post("/users", response_model=UsuarioResponse)
async def create_user(user_data: UsuarioCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.funcao not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing = db.query(Usuario).filter(Usuario.nome_usuario == user_data.nome_usuario).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_dict = user_data.model_dump()
    senha = user_dict.pop('senha')
    
    user = Usuario(
        **user_dict,
        senha_hash=hash_password(senha)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@api_router.get("/users/{user_id}", response_model=UsuarioResponse)
async def get_user(user_id: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
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

# Continue no próximo arquivo devido ao tamanho...
