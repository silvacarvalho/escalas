from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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

# Enums
class UserRole(str, Enum):
    PASTOR_DISTRITAL = "pastor_distrital"
    LIDER_IGREJA = "lider_igreja"
    PREGADOR = "pregador"
    CANTOR = "cantor"
    MEMBRO = "membro"

class ScheduleStatus(str, Enum):
    RASCUNHO = "rascunho"
    CONFIRMADA = "confirmada"
    ATIVA = "ativa"

class ScheduleItemStatus(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    RECUSADO = "recusado"
    CANCELADO = "cancelado"
    COMPLETADO = "completado"

class GenerationMode(str, Enum):
    AUTOMATICO = "automatico"
    MANUAL = "manual"

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
    funcao: UserRole
    id_distrito: Optional[str] = None
    id_igreja: Optional[str] = None
    eh_pregador: bool = False
    eh_cantor: bool = False

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
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
    horarios_culto: List[HorarioCulto] = []

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
    modo_geracao: GenerationMode

class EscalaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    mes: int
    ano: int
    id_igreja: str
    id_distrito: str
    id_gerado_por: str
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

async def criar_notificacao(db: Session, id_usuario: str, tipo: str, titulo: str, mensagem: str, id_relacionado: Optional[str] = None):
    notificacao = Notificacao(
        id_usuario=id_usuario,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        id_relacionado=id_relacionado
    )
    db.add(notificacao)
    db.commit()

async def enviar_notificacao_mock(telefone: str, mensagem: str):
    """Mock notification via SMS/WhatsApp"""
    logging.info(f"[MOCK SMS/WhatsApp para {telefone}]: {mensagem}")

async def usuario_disponivel(db: Session, id_usuario: str, data: str) -> bool:
    user = db.query(Usuario).filter(Usuario.id == id_usuario).first()
    if not user or not user.periodos_indisponibilidade:
        return True
    
    for periodo in user.periodos_indisponibilidade:
        if periodo.get('data_inicio', '') <= data <= periodo.get('data_fim', ''):
            return False
    return True

async def slot_ocupado(db: Session, id_usuario: str, data: str) -> bool:
    """Check if user is already scheduled on this date"""
    escalas = db.query(Escala).filter(Escala.status.in_(['confirmada', 'ativa'])).all()
    for escala in escalas:
        for item in escala.itens:
            if item.data == data and item.status in ['confirmado', 'pendente']:
                if item.id_pregador == id_usuario:
                    return True
                if id_usuario in (item.ids_cantores or []):
                    return True
    return False

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
