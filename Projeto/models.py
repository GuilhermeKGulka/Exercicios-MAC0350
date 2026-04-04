from typing import Annotated, List, Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session
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

# ========== MODELOS ==========

class UsuarioBase(SQLModel, table=False):
    """Modelo base de usuário"""
    username: str = Field(index=True, unique=True)
    name: Optional[str] = Field(default=None)

class AnimalBase(SQLModel, table=False):
    """Modelo base de animal"""
    nome_cientifico: str = Field(unique=True)
    nome_popular: Optional[str] = Field(default=None)
    reino: Optional[str] = Field(default=None, index=True)
    filo: Optional[str] = Field(default=None, index=True)
    classe: Optional[str] = Field(default=None, index=True)
    ordem: Optional[str] = Field(default=None, index=True)
    familia: Optional[str] = Field(default=None, index=True)
    genero: Optional[str] = Field(default=None, index=True)
    epitetoEspecifico: Optional[str] = Field(default=None)

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
    profile_img_url: Optional[str] = Field(default=None)
    
    animais_favoritos: List["Animal"] = Relationship(
        back_populates="favoritado_por_usuarios",
        link_model=Favorito
    )

class Animal(AnimalBase, table=True):
    __tablename__ = "animal"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    gbif_id: Optional[int] = Field(default=None)
    img_url: Optional[str] = Field(default=None)
    img_author: Optional[str] = Field(default=None)
    
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