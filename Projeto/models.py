from typing import Annotated, List, Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session
from passlib.context import CryptContext
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURAÇÃO DO BANCO ==========

# Criar pasta data
Path("data").mkdir(exist_ok=True)

# URL do banco
DATABASE_URL = "sqlite:///data/fauna.db"

# Engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    """Cria todas as tabelas"""
    SQLModel.metadata.create_all(engine)
    logger.info("✅ Banco de dados criado/verificado")

def get_session():
    """Retorna uma sessão"""
    with Session(engine) as session:
        yield session

# ========== CONFIGURAÇÃO DE HASH ==========

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========== MODELOS ==========

class UsuarioBase(SQLModel, table=False):
    """Modelo base de usuário"""
    username: str = Field(index=True, unique=True)
    name: Optional[str] = Field(default=None)

class AnimalBase(SQLModel, table=False):
    """Modelo base de animal"""
    nome_cientifico: str = Field(index=True, unique=True)
    nome_popular: Optional[str] = Field(default=None, index=True)
    reino: Optional[str] = Field(default=None)
    filo: Optional[str] = Field(default=None)
    classe: Optional[str] = Field(default=None)
    ordem: Optional[str] = Field(default=None)
    familia: Optional[str] = Field(default=None, index=True)
    genero: Optional[str] = Field(default=None)
    especie: Optional[str] = Field(default=None)

class Favorito(SQLModel, table=True):
    """Tabela de favoritos"""
    __tablename__ = "favoritos"
    
    # TODOS OS CAMPOS DEVEM TER ANOTAÇÃO DE TIPO!
    usuario_id: int = Field(
        foreign_key="usuario.id",
        primary_key=True
    )
    animal_id: int = Field(
        foreign_key="animal.id",
        primary_key=True
    )

class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuario"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    
    # Relacionamento - string com o nome da classe para evitar circular import
    animais_favoritos: List["Animal"] = Relationship(
        back_populates="favoritado_por_usuarios",
        link_model=Favorito
    )

class Animal(AnimalBase, table=True):
    __tablename__ = "animal"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relacionamento
    favoritado_por_usuarios: List["Usuario"] = Relationship(
        back_populates="animais_favoritos",
        link_model=Favorito
    )
    
    @property
    def total_favoritos(self) -> int:
        """Retorna o número de favoritos deste animal"""
        return len(self.favoritado_por_usuarios) if self.favoritado_por_usuarios else 0

class UsuarioAuth(UsuarioBase):
    password: str