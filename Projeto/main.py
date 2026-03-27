from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Annotated, Optional
import logging
from sqlmodel import Session, select
from models import engine, get_session, create_db_and_tables
from models import Usuario, Animal, Favorito  # ← SQLModel models
from models import UsuarioAuth

app = FastAPI()

# Criar tabelas ao iniciar
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logger.info("✅ Banco de dados inicializado")

# Monta a pasta "static" na rota "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sintaxe recomendada: diretório como primeiro argumento posicional
templates = Jinja2Templates(directory="templates")

# Configuração básica de log para aparecer no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# ========== DEPENDÊNCIAS ==========

async def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[dict]:
    """Obtém usuário atual do cookie"""
    username = request.cookies.get("session_username")
    logger.debug(f"Cookie session_username: {username}")
    
    if username:
        statement = select(Usuario).where(Usuario.username == username)
        usuario = session.exec(statement).first()
        return usuario
    
    return None

async def require_logged_out(request: Request, current_user: Optional[Usuario] = Depends(get_current_user)):
    """Redireciona se usuário estiver logado"""
    if current_user:
        logger.info(f"Usuário {current_user.username} tentou acessar rota protegida - REDIRECIONANDO")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return None

async def require_logged_in(current_user: Optional[Usuario] = Depends(get_current_user)) -> Usuario:
    """Exige que usuário esteja logado"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return current_user

# ========== ROTAS ==========

@app.get("/")
def pagina_inicial(request: Request, current_user: Optional[Usuario] = Depends(get_current_user),session: Session = Depends(get_session)):
    animais = session.exec(select(Animal).limit(12)).all()
    
    return templates.TemplateResponse(
        request=request,
        name="Home.html",
        context={
            "username": current_user.username if current_user else None,
            "user_nome": current_user.name if current_user else None,
            "animais": animais
        }
    )

@app.get("/register")
def pagina_cadastro(request: Request, _: None = Depends(require_logged_out)):
    return templates.TemplateResponse(
        request=request, 
        name="Register.html", 
        context={"username": None}
    )

@app.post("/createuser")
def criar_usuario(registerRequest: UsuarioAuth, session: Session = Depends(get_session)):
    #Checa se usuario existe
    statement = select(Usuario).where(Usuario.username == registerRequest.username)
    existing = session.exec(statement).first()
    
    if existing:
        return JSONResponse(
            status_code=400,
            content={"error": "Usuário já existe"}
        )

    novo_usuario = Usuario(
        username=registerRequest.username,
        name=registerRequest.name,
        password=registerRequest.password
    )
    
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    
    response = RedirectResponse(url="/", status_code=303)
    return response

@app.post("/login")
async def login(loginRequest: UsuarioAuth, response: Response = None, session: Session = Depends(get_session)):
    # Buscar usuário no banco
    statement = select(Usuario).where(Usuario.username == loginRequest.username)
    usuario = session.exec(statement).first()
    
    if not usuario:
        return JSONResponse(
            status_code=401,
            content={"error": "Usuário não encontrado"}
        )
    
    if usuario.password != loginRequest.password:
        return JSONResponse(
            status_code=401,
            content={"error": "Senha incorreta"}
        )
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_username",
        value=loginRequest.username,
        path="/"
    )

    return response

@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_username", path="/")
    return response

# ========== ROTAS PARA ANIMAIS ==========

@app.get("/animais")
async def listar_animais(
    request: Request,
    q: str = "",
    limite: int = 20,
    session: Session = Depends(get_session)
):
    """Lista animais com busca"""
    
    statement = select(Animal)
    
    if q:
        statement = statement.where(
            (Animal.nome_cientifico.contains(q)) |
            (Animal.nome_popular.contains(q))
        )
    
    animais = session.exec(statement.limit(limite)).all()
    
    return templates.TemplateResponse(
        request=request,
        name="Animais_lista.html",
        context={
            "animais": animais,
            "termo": q
        }
    )

@app.get("/animal/{animal_id}")
async def ver_animal(
    request: Request,
    animal_id: int,
    current_user: Optional[Usuario] = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Página de detalhes do animal"""
    
    animal = session.get(Animal, animal_id)
    
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    
    return templates.TemplateResponse(
        request=request,
        name="animal_detalhe.html",
        context={
            "username": current_user.username if current_user else None,
            "animal": animal
        }
    )

# ========== ROTAS DE DEBUG ==========

@app.get("/debug/status")
async def debug_status(
    session: Session = Depends(get_session)
):
    """Endpoint para debug - mostra estatísticas"""
    
    total_usuarios = session.exec(select(Usuario)).all().__len__()
    total_animais = session.exec(select(Animal)).all().__len__()
    
    return {
        "total_usuarios": total_usuarios,
        "total_animais": total_animais,
        "status": "online",
        "database": "fauna.db"
    }

@app.get("/debug/animais")
async def debug_animais(
    session: Session = Depends(get_session)
):
    """Lista primeiros 10 animais para debug"""
    
    animais = session.exec(select(Animal).limit(10)).all()
    
    return [
        {
            "id": a.id,
            "nome_cientifico": a.nome_cientifico,
            "nome_popular": a.nome_popular,
            "familia": a.familia
        }
        for a in animais
    ]