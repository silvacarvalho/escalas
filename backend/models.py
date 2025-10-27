"""
Modelos do Banco de Dados PostgreSQL
Todos os atributos estão em português
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

def gerar_uuid():
    return str(uuid.uuid4())

# Tabela de Usuários
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    nome_usuario = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(200), nullable=False)
    email = Column(String(200))
    telefone = Column(String(20))
    funcao = Column(String(50), nullable=False)  # pastor_distrital, lider_igreja, pregador, cantor, membro
    id_distrito = Column(String, ForeignKey('distritos.id'))
    id_igreja = Column(String, ForeignKey('igrejas.id'))
    eh_pregador = Column(Boolean, default=False)
    eh_cantor = Column(Boolean, default=False)
    pontuacao_pregacao = Column(Float, default=50.0)
    pontuacao_canto = Column(Float, default=50.0)
    periodos_indisponibilidade = Column(JSON, default=list)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    distrito = relationship("Distrito", back_populates="usuarios")
    igreja = relationship("Igreja", back_populates="usuarios")
    avaliacoes_recebidas = relationship("Avaliacao", back_populates="usuario_avaliado", foreign_keys="Avaliacao.id_usuario_avaliado")
    notificacoes = relationship("Notificacao", back_populates="usuario")


# Tabela de Distritos
class Distrito(Base):
    __tablename__ = "distritos"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    nome = Column(String(200), nullable=False)
    id_pastor = Column(String, ForeignKey('usuarios.id'))
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    pastor = relationship("Usuario", foreign_keys=[id_pastor])
    usuarios = relationship("Usuario", back_populates="distrito", foreign_keys="Usuario.id_distrito")
    igrejas = relationship("Igreja", back_populates="distrito")
    escalas = relationship("Escala", back_populates="distrito")


# Tabela de Igrejas
class Igreja(Base):
    __tablename__ = "igrejas"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    nome = Column(String(200), nullable=False)
    id_distrito = Column(String, ForeignKey('distritos.id'), nullable=False)
    endereco = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    id_lider = Column(String, ForeignKey('usuarios.id'))
    horarios_culto = Column(JSON, default=list)  # [{"dia_semana": "wednesday", "horario": "19:00"}]
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    distrito = relationship("Distrito", back_populates="igrejas")
    lider = relationship("Usuario", foreign_keys=[id_lider])
    usuarios = relationship("Usuario", back_populates="igreja", foreign_keys="Usuario.id_igreja")
    escalas = relationship("Escala", back_populates="igreja")


# Tabela de Escalas
class Escala(Base):
    __tablename__ = "escalas"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    id_igreja = Column(String, ForeignKey('igrejas.id'), nullable=False)
    id_distrito = Column(String, ForeignKey('distritos.id'), nullable=False)
    id_gerado_por = Column(String, ForeignKey('usuarios.id'))
    modo_geracao = Column(String(50), nullable=False)  # automatico, manual
    status = Column(String(50), default='rascunho')  # rascunho, confirmada, ativa
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    igreja = relationship("Igreja", back_populates="escalas")
    distrito = relationship("Distrito", back_populates="escalas")
    gerado_por = relationship("Usuario", foreign_keys=[id_gerado_por])
    itens = relationship("ItemEscala", back_populates="escala", cascade="all, delete-orphan")


# Tabela de Itens da Escala
class ItemEscala(Base):
    __tablename__ = "itens_escala"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_escala = Column(String, ForeignKey('escalas.id', ondelete='CASCADE'), nullable=False)
    data = Column(String(10), nullable=False)  # YYYY-MM-DD
    horario = Column(String(5), nullable=False)  # HH:MM
    id_pregador = Column(String, ForeignKey('usuarios.id'))
    ids_cantores = Column(JSON, default=list)  # Lista de IDs dos cantores
    status = Column(String(50), default='pendente')  # pendente, confirmado, recusado, cancelado, completado
    motivo_recusa = Column(Text)
    confirmado_em = Column(DateTime(timezone=True))
    cancelado_em = Column(DateTime(timezone=True))
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    escala = relationship("Escala", back_populates="itens")
    pregador = relationship("Usuario", foreign_keys=[id_pregador])
    avaliacoes = relationship("Avaliacao", back_populates="item_escala")


# Tabela de Avaliações
class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_item_escala = Column(String, ForeignKey('itens_escala.id'), nullable=False)
    id_igreja = Column(String, ForeignKey('igrejas.id'), nullable=False)
    tipo_membro = Column(String(20), nullable=False)  # pregador, cantor
    id_usuario_avaliado = Column(String, ForeignKey('usuarios.id'), nullable=False)
    nota = Column(Integer, nullable=False)  # 1 a 5
    comentario = Column(Text)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    item_escala = relationship("ItemEscala", back_populates="avaliacoes")
    usuario_avaliado = relationship("Usuario", back_populates="avaliacoes_recebidas", foreign_keys=[id_usuario_avaliado])


# Tabela de Notificações
class Notificacao(Base):
    __tablename__ = "notificacoes"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_usuario = Column(String, ForeignKey('usuarios.id'), nullable=False)
    tipo = Column(String(50), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensagem = Column(Text, nullable=False)
    id_relacionado = Column(String)  # ID do item relacionado (escala, etc)
    status = Column(String(20), default='nao_lida')  # nao_lida, lida
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="notificacoes")


# Tabela de Solicitações de Troca
class SolicitacaoTroca(Base):
    __tablename__ = "solicitacoes_troca"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_item_escala_original = Column(String, ForeignKey('itens_escala.id'), nullable=False)
    id_escala = Column(String, ForeignKey('escalas.id'), nullable=False)
    id_solicitante = Column(String, ForeignKey('usuarios.id'), nullable=False)
    id_usuario_alvo = Column(String, ForeignKey('usuarios.id'), nullable=False)
    motivo = Column(Text, nullable=False)
    status = Column(String(20), default='pendente')  # pendente, aceita, rejeitada
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    respondido_em = Column(DateTime(timezone=True))
    
    # Relacionamentos
    solicitante = relationship("Usuario", foreign_keys=[id_solicitante])
    usuario_alvo = relationship("Usuario", foreign_keys=[id_usuario_alvo])


# Tabela de Delegações
class Delegacao(Base):
    __tablename__ = "delegacoes"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_distrito = Column(String, ForeignKey('distritos.id'), nullable=False)
    id_usuario = Column(String, ForeignKey('usuarios.id'), nullable=False)
    id_delegado_por = Column(String, ForeignKey('usuarios.id'), nullable=False)
    permissoes = Column(JSON, default=list)  # ['criar_escala', 'editar_escala', 'deletar_escala']
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", foreign_keys=[id_usuario])
    delegado_por = relationship("Usuario", foreign_keys=[id_delegado_por])


# Tabela de Logs de Auditoria
class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"
    
    id = Column(String, primary_key=True, default=gerar_uuid)
    id_usuario = Column(String, ForeignKey('usuarios.id'))
    acao = Column(String(100), nullable=False)
    tipo_entidade = Column(String(50))
    id_entidade = Column(String)
    alteracoes = Column(JSON)
    endereco_ip = Column(String(50))
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    usuario = relationship("Usuario")
